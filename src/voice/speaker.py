import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

import edge_tts

from src.vision.mimi_vision import (
    detect_audio_devices,
)


# =========================================================
# MIMI VOICE SETTINGS
# =========================================================

VOICE = "ar-JO-SanaNeural"

RATE = "+0%"

PITCH = "+0Hz"

VOLUME = "+0%"


# =========================================================
# HARDWARE SETTINGS
# =========================================================

SPEAKER_VOLUME_PERCENT = 80

PLAYBACK_SAMPLE_RATE = 44100

PLAYBACK_CHANNELS = 1


# =========================================================
# PROJECT / CACHE
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CACHE_DIR = (
    PROJECT_ROOT
    / "data"
    / "private"
    / "tts_cache"
)

CACHE_READ_CHUNK = 32768


# =========================================================
# RUNTIME CACHE
# =========================================================

_cached_speaker_device = None

_volume_configured_device = None


# =========================================================
# LIVE PLAYBACK / BARGE-IN STATE
# =========================================================

_playback_state_lock = threading.RLock()

_active_ffmpeg_process = None
_active_aplay_process = None

_stop_requested = threading.Event()


class PlaybackInterrupted(Exception):
    """Raised internally when the child stops Mimi while speaking."""
    pass


def _register_active_pipeline(
    ffmpeg_process,
    aplay_process,
):
    global _active_ffmpeg_process
    global _active_aplay_process

    with _playback_state_lock:
        _active_ffmpeg_process = ffmpeg_process
        _active_aplay_process = aplay_process


def _clear_active_pipeline(
    ffmpeg_process=None,
    aplay_process=None,
):
    global _active_ffmpeg_process
    global _active_aplay_process

    with _playback_state_lock:

        if (
            ffmpeg_process is None
            or
            _active_ffmpeg_process
            is ffmpeg_process
        ):
            _active_ffmpeg_process = None

        if (
            aplay_process is None
            or
            _active_aplay_process
            is aplay_process
        ):
            _active_aplay_process = None


def is_playing():

    with _playback_state_lock:

        for process in (
            _active_ffmpeg_process,
            _active_aplay_process,
        ):

            if (
                process is not None
                and
                process.poll() is None
            ):
                return True

    return False


def stop_playback():
    """
    Stop Mimi's current TTS playback immediately.

    Used by voice barge-in commands such as:
        وقف
        ميمي وقف
    """

    _stop_requested.set()

    with _playback_state_lock:

        processes = (
            _active_ffmpeg_process,
            _active_aplay_process,
        )

    stopped = False

    for process in processes:

        if process is None:
            continue

        try:

            if process.poll() is None:

                process.kill()

                stopped = True

        except Exception:

            pass

    if stopped:

        print()
        print(
            "🛑 Mimi playback stopped by child."
        )

    return stopped


def get_speaker_volume():

    return int(
        SPEAKER_VOLUME_PERCENT
    )


def _apply_volume_percent(
    percent,
):
    """
    Apply volume immediately to the USB speaker.

    Tries common ALSA controls because USB sound cards
    can expose PCM, Speaker, or Master.
    """

    global SPEAKER_VOLUME_PERCENT
    global _volume_configured_device

    try:

        percent = int(
            round(
                float(percent)
            )
        )

    except Exception:

        percent = int(
            SPEAKER_VOLUME_PERCENT
        )

    percent = max(
        0,
        min(
            100,
            percent,
        ),
    )

    SPEAKER_VOLUME_PERCENT = percent

    speaker_device = (
        get_speaker_device()
    )

    if not speaker_device:

        return False

    card_number = (
        get_card_number(
            speaker_device
        )
    )

    if card_number is None:

        return False

    controls = (
        "PCM",
        "Speaker",
        "Master",
    )

    for control in controls:

        try:

            result = subprocess.run(
                [
                    "amixer",
                    "-c",
                    str(
                        card_number
                    ),
                    "sset",
                    control,
                    f"{percent}%",
                    "unmute",
                ],
                stdout=
                    subprocess.DEVNULL,
                stderr=
                    subprocess.DEVNULL,
                check=False,
            )

            if result.returncode == 0:

                _volume_configured_device = (
                    speaker_device
                )

                print(
                    f"🔊 Mimi volume: "
                    f"{percent}%"
                )

                return True

        except Exception:

            continue

    # Force normal configure_speaker_volume() to retry later.
    _volume_configured_device = None

    print(
        "⚠️ Could not change "
        "speaker volume."
    )

    return False


def set_speaker_volume(
    percent,
):

    return _apply_volume_percent(
        percent
    )


def volume_down(
    step=15,
):

    try:
        step = abs(
            int(step)
        )
    except Exception:
        step = 15

    target = max(
        0,
        get_speaker_volume()
        -
        step,
    )

    return _apply_volume_percent(
        target
    )


def volume_up(
    step=15,
):

    try:
        step = abs(
            int(step)
        )
    except Exception:
        step = 15

    target = min(
        100,
        get_speaker_volume()
        +
        step,
    )

    return _apply_volume_percent(
        target
    )


# =========================================================
# CREATE CACHE DIRECTORY
# =========================================================

def ensure_cache_directory():

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# =========================================================
# CACHE KEY
# =========================================================

def get_cache_path(
    text,
):

    cache_source = (
        f"{VOICE}|"
        f"{RATE}|"
        f"{PITCH}|"
        f"{VOLUME}|"
        f"{text}"
    )

    digest = hashlib.sha256(
        cache_source.encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        CACHE_DIR
        /
        f"{digest}.mp3"
    )


# =========================================================
# CHECK REQUIRED PROGRAMS
# =========================================================

def check_audio_tools():

    missing = []

    if shutil.which(
        "ffmpeg"
    ) is None:

        missing.append(
            "ffmpeg"
        )

    if shutil.which(
        "aplay"
    ) is None:

        missing.append(
            "aplay"
        )

    if missing:

        print()
        print(
            "❌ Missing audio tools:"
        )

        print(
            ", ".join(
                missing
            )
        )

        return False

    return True


# =========================================================
# SPEAKER DEVICE
# =========================================================

def get_speaker_device(
    force_refresh=False,
):

    global _cached_speaker_device
    global _volume_configured_device

    if (
        _cached_speaker_device
        and
        not force_refresh
    ):

        return (
            _cached_speaker_device
        )

    _, speaker_device = (
        detect_audio_devices()
    )

    if not speaker_device:

        _cached_speaker_device = None

        return None

    if (
        speaker_device
        !=
        _cached_speaker_device
    ):

        _volume_configured_device = (
            None
        )

    _cached_speaker_device = (
        speaker_device
    )

    return (
        _cached_speaker_device
    )


# =========================================================
# EXTRACT ALSA CARD NUMBER
# =========================================================

def get_card_number(
    speaker_device,
):

    if not speaker_device:

        return None

    match = re.search(
        r"(?:plughw|hw):(\d+)",
        str(
            speaker_device
        ),
    )

    if not match:

        return None

    try:

        return int(
            match.group(1)
        )

    except Exception:

        return None


# =========================================================
# SET VOLUME ONLY WHEN NEEDED
# =========================================================

def configure_speaker_volume(
    speaker_device,
):

    global _volume_configured_device

    if (
        _volume_configured_device
        ==
        speaker_device
    ):

        return True

    card_number = (
        get_card_number(
            speaker_device
        )
    )

    if card_number is None:

        print()
        print(
            "⚠️ Could not determine "
            "speaker card number."
        )

        return False

    try:

        result = subprocess.run(
            [
                "amixer",
                "-c",
                str(
                    card_number
                ),
                "sset",
                "PCM",
                f"{SPEAKER_VOLUME_PERCENT}%",
                "unmute",
            ],

            stdout=
                subprocess.DEVNULL,

            stderr=
                subprocess.DEVNULL,

            check=False,
        )

        if result.returncode == 0:

            _volume_configured_device = (
                speaker_device
            )

            print(
                f"🔊 Speaker volume: "
                f"{SPEAKER_VOLUME_PERCENT}%"
            )

            return True

    except Exception as error:

        print()
        print(
            "⚠️ Volume warning:"
        )

        print(
            error
        )

    return False


# =========================================================
# START FFMPEG -> APLAY PIPELINE
# =========================================================

def start_playback_pipeline(
    speaker_device,
):

    # -----------------------------------------------------
    # Edge TTS gives us MP3 chunks.
    #
    # MP3 chunks
    #     ↓
    # ffmpeg stdin
    #     ↓
    # raw PCM
    #     ↓
    # aplay stdin
    #     ↓
    # USB Speaker
    # -----------------------------------------------------

    ffmpeg_process = (
        subprocess.Popen(
            [
                "ffmpeg",

                "-hide_banner",

                "-loglevel",
                "error",

                "-f",
                "mp3",

                "-i",
                "pipe:0",

                "-vn",

                "-ac",
                str(
                    PLAYBACK_CHANNELS
                ),

                "-ar",
                str(
                    PLAYBACK_SAMPLE_RATE
                ),

                "-acodec",
                "pcm_s16le",

                "-f",
                "s16le",

                "pipe:1",
            ],

            stdin=
                subprocess.PIPE,

            stdout=
                subprocess.PIPE,

            stderr=
                subprocess.PIPE,

            bufsize=0,
        )
    )

    if ffmpeg_process.stdout is None:

        raise RuntimeError(
            "Could not open ffmpeg output."
        )

    aplay_process = (
        subprocess.Popen(
            [
                "aplay",

                "-q",

                "-D",
                speaker_device,

                "-f",
                "S16_LE",

                "-c",
                str(
                    PLAYBACK_CHANNELS
                ),

                "-r",
                str(
                    PLAYBACK_SAMPLE_RATE
                ),
            ],

            stdin=
                ffmpeg_process.stdout,

            stdout=
                subprocess.DEVNULL,

            stderr=
                subprocess.PIPE,

            bufsize=0,
        )
    )

    # Parent process no longer needs its own copy.
    ffmpeg_process.stdout.close()

    _register_active_pipeline(
        ffmpeg_process,
        aplay_process,
    )

    return (
        ffmpeg_process,
        aplay_process,
    )


# =========================================================
# ABORT PIPELINE
# =========================================================

def abort_pipeline(
    ffmpeg_process,
    aplay_process,
):

    for process in (
        ffmpeg_process,
        aplay_process,
    ):

        if process is None:

            continue

        try:

            if process.poll() is None:

                process.kill()

        except Exception:

            pass

    for process in (
        ffmpeg_process,
        aplay_process,
    ):

        if process is None:

            continue

        try:

            process.wait(
                timeout=0.5
            )

        except Exception:

            pass

    _clear_active_pipeline(
        ffmpeg_process,
        aplay_process,
    )


# =========================================================
# FINISH PIPELINE
# =========================================================

def finish_pipeline(
    ffmpeg_process,
    aplay_process,
):

    # القصص والجمل الطويلة قد تتجاوز 15 ثانية بسهولة.
    # نستخدم مهلة أكبر حتى لا ينقطع صوت Mimi في منتصف الكلام.
    FFMPEG_TIMEOUT = 120
    APLAY_TIMEOUT = 120

    try:

        if (
            ffmpeg_process.stdin
            and
            not ffmpeg_process.stdin.closed
        ):

            ffmpeg_process.stdin.close()

    except Exception:

        pass

    try:

        ffmpeg_return = (
            ffmpeg_process.wait(
                timeout=FFMPEG_TIMEOUT
            )
        )

    except subprocess.TimeoutExpired:

        print()
        print(
            f"❌ ffmpeg timeout after {FFMPEG_TIMEOUT} seconds."
        )

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    try:

        aplay_return = (
            aplay_process.wait(
                timeout=APLAY_TIMEOUT
            )
        )

    except subprocess.TimeoutExpired:

        print()
        print(
            f"❌ aplay timeout after {APLAY_TIMEOUT} seconds."
        )

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    ffmpeg_error = ""

    aplay_error = ""

    try:

        if ffmpeg_process.stderr:

            ffmpeg_error = (
                ffmpeg_process.stderr
                .read()
                .decode(
                    "utf-8",
                    errors="ignore",
                )
                .strip()
            )

    except Exception:

        pass

    try:

        if aplay_process.stderr:

            aplay_error = (
                aplay_process.stderr
                .read()
                .decode(
                    "utf-8",
                    errors="ignore",
                )
                .strip()
            )

    except Exception:

        pass

    if _stop_requested.is_set():

        _clear_active_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    if ffmpeg_return != 0:

        print()
        print(
            "❌ ffmpeg playback error."
        )

        if ffmpeg_error:

            print(
                ffmpeg_error
            )

        return False

    if aplay_return != 0:

        print()
        print(
            "❌ Speaker playback error."
        )

        if aplay_error:

            print(
                aplay_error
            )

        return False

    _clear_active_pipeline(
        ffmpeg_process,
        aplay_process,
    )

    print(
        "✅ Full audio playback finished."
    )

    return True


# =========================================================
# WRITE MP3 DATA INTO LIVE PIPELINE
# =========================================================

def write_audio_chunk(
    ffmpeg_process,
    data,
):

    if _stop_requested.is_set():

        raise PlaybackInterrupted(
            "Playback stopped by child."
        )

    if not data:

        return

    if (
        ffmpeg_process is None
        or
        ffmpeg_process.stdin is None
    ):

        raise RuntimeError(
            "ffmpeg input is not available."
        )

    ffmpeg_process.stdin.write(
        data
    )

    # stdin is unbuffered, but flush keeps
    # first-audio latency as small as possible.
    ffmpeg_process.stdin.flush()


# =========================================================
# PLAY CACHED VOICE
# =========================================================

def play_cached_voice(
    cache_path,
    speaker_device,
):

    if (
        not cache_path.exists()
        or
        cache_path.stat().st_size == 0
    ):

        return False

    print(
        "⚡ Using cached Mimi voice."
    )

    ffmpeg_process = None

    aplay_process = None

    try:

        (
            ffmpeg_process,
            aplay_process,
        ) = start_playback_pipeline(
            speaker_device
        )

        with cache_path.open(
            "rb"
        ) as audio_file:

            while True:

                data = audio_file.read(
                    CACHE_READ_CHUNK
                )

                if not data:

                    break

                if _stop_requested.is_set():

                    raise PlaybackInterrupted(
                        "Playback stopped by child."
                    )

                write_audio_chunk(
                    ffmpeg_process,
                    data,
                )

        return finish_pipeline(
            ffmpeg_process,
            aplay_process,
        )

    except PlaybackInterrupted:

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    except Exception as error:

        print()
        print(
            "⚠️ Cached voice playback error:"
        )

        print(
            error
        )

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False


# =========================================================
# ASYNC EDGE-TTS STREAM FALLBACK
# =========================================================

async def stream_edge_async(
    communicate,
    audio_callback,
):

    async for chunk in communicate.stream():

        if (
            chunk.get(
                "type"
            )
            ==
            "audio"
        ):

            audio_callback(
                chunk.get(
                    "data",
                    b"",
                )
            )


# =========================================================
# GENERATE + PLAY AT SAME TIME
# =========================================================

def generate_and_stream_voice(
    text,
    cache_path,
    speaker_device,
):

    ffmpeg_process = None

    aplay_process = None

    cache_file = None

    temp_cache_path = (
        cache_path.with_suffix(
            ".part"
        )
    )

    audio_bytes_received = 0

    first_audio_received = False

    generation_started = (
        time.monotonic()
    )

    try:

        # -------------------------------------------------
        # Audio pipeline first
        # -------------------------------------------------

        (
            ffmpeg_process,
            aplay_process,
        ) = start_playback_pipeline(
            speaker_device
        )

        # -------------------------------------------------
        # Temporary cache
        # -------------------------------------------------

        cache_file = (
            temp_cache_path.open(
                "wb"
            )
        )

        # -------------------------------------------------
        # Edge communicate
        # -------------------------------------------------

        communicate = (
            edge_tts.Communicate(
                text=text,
                voice=VOICE,
                rate=RATE,
                pitch=PITCH,
                volume=VOLUME,
            )
        )

        # -------------------------------------------------
        # Handle each MP3 chunk immediately
        # -------------------------------------------------

        def on_audio(
            data,
        ):

            nonlocal audio_bytes_received
            nonlocal first_audio_received

            if _stop_requested.is_set():

                raise PlaybackInterrupted(
                    "Playback stopped by child."
                )

            if not data:

                return

            if not first_audio_received:

                first_audio_received = True

                first_audio_delay = (
                    time.monotonic()
                    -
                    generation_started
                )

                print(
                    f"⚡ First TTS audio received "
                    f"after "
                    f"{first_audio_delay:.2f}s"
                )

                print(
                    "🔊 Mimi is speaking..."
                )

            audio_bytes_received += (
                len(data)
            )

            # Save for future instant reuse
            cache_file.write(
                data
            )

            # Play now, without waiting for
            # the whole MP3.
            write_audio_chunk(
                ffmpeg_process,
                data,
            )

        # -------------------------------------------------
        # Newer edge-tts versions
        # -------------------------------------------------

        if hasattr(
            communicate,
            "stream_sync",
        ):

            for chunk in (
                communicate.stream_sync()
            ):

                if (
                    chunk.get(
                        "type"
                    )
                    ==
                    "audio"
                ):

                    on_audio(
                        chunk.get(
                            "data",
                            b"",
                        )
                    )

        # -------------------------------------------------
        # Compatibility with versions that only
        # expose async stream()
        # -------------------------------------------------

        else:

            asyncio.run(
                stream_edge_async(
                    communicate,
                    on_audio,
                )
            )

        # -------------------------------------------------
        # Validate response
        # -------------------------------------------------

        if audio_bytes_received <= 0:

            raise RuntimeError(
                "Edge TTS returned no audio."
            )

        # -------------------------------------------------
        # Finish cache write
        # -------------------------------------------------

        cache_file.flush()

        cache_file.close()

        cache_file = None

        # -------------------------------------------------
        # Finish live playback
        # -------------------------------------------------

        playback_ok = (
            finish_pipeline(
                ffmpeg_process,
                aplay_process,
            )
        )

        ffmpeg_process = None

        aplay_process = None

        # -------------------------------------------------
        # Cache successful TTS result
        # -------------------------------------------------

        if (
            temp_cache_path.exists()
            and
            temp_cache_path.stat().st_size
            > 0
        ):

            os.replace(
                temp_cache_path,
                cache_path,
            )

        return playback_ok

    except PlaybackInterrupted:

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    except Exception as error:

        print()
        print(
            "❌ Mimi streaming TTS error:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        abort_pipeline(
            ffmpeg_process,
            aplay_process,
        )

        return False

    finally:

        if cache_file is not None:

            try:

                cache_file.close()

            except Exception:

                pass

        try:

            if temp_cache_path.exists():

                temp_cache_path.unlink(
                    missing_ok=True
                )

        except Exception:

            pass


# =========================================================
# RESET SPEAKER CACHE
# =========================================================

def reset_speaker_cache():

    global _cached_speaker_device
    global _volume_configured_device

    _cached_speaker_device = None

    _volume_configured_device = None


# =========================================================
# CLEAR TTS CACHE
# =========================================================

def clear_tts_cache():

    ensure_cache_directory()

    removed = 0

    for file_path in (
        CACHE_DIR.glob(
            "*.mp3"
        )
    ):

        try:

            file_path.unlink()

            removed += 1

        except Exception:

            pass

    print(
        f"🧹 Removed "
        f"{removed} cached voices."
    )

    return removed


# =========================================================
# CACHE COUNT
# =========================================================

def get_tts_cache_count():

    ensure_cache_directory()

    return len(
        list(
            CACHE_DIR.glob(
                "*.mp3"
            )
        )
    )


# =========================================================
# MIMI SPEAK
# =========================================================

def speak(
    text,
):

    text = str(
        text
    ).strip()

    if not text:

        return False

    # New sentence starts with a clean interrupt state.
    _stop_requested.clear()

    started = (
        time.monotonic()
    )

    print()
    print(
        f"🤖 Mimi: {text}"
    )

    # -----------------------------------------------------
    # Tools
    # -----------------------------------------------------

    if not check_audio_tools():

        return False

    # -----------------------------------------------------
    # Local cache directory
    # -----------------------------------------------------

    ensure_cache_directory()

    # -----------------------------------------------------
    # Speaker detection is now cached.
    # We do NOT scan USB audio every sentence.
    # -----------------------------------------------------

    speaker_device = (
        get_speaker_device()
    )

    if not speaker_device:

        print(
            "❌ USB speaker not found."
        )

        return False

    print(
        f"🔊 Speaker: "
        f"{speaker_device}"
    )

    # -----------------------------------------------------
    # Volume is also configured once per device,
    # not every sentence.
    # -----------------------------------------------------

    configure_speaker_volume(
        speaker_device
    )

    # -----------------------------------------------------
    # Cached voice?
    # -----------------------------------------------------

    cache_path = (
        get_cache_path(
            text
        )
    )

    if (
        cache_path.exists()
        and
        cache_path.stat().st_size
        > 0
    ):

        cached_started = (
            time.monotonic()
        )

        result = (
            play_cached_voice(
                cache_path,
                speaker_device,
            )
        )

        cached_elapsed = (
            time.monotonic()
            -
            cached_started
        )

        if result:

            print(
                f"✅ Cached speech finished "
                f"in "
                f"{cached_elapsed:.2f}s"
            )

            return True

        # If cache failed, regenerate once.
        print(
            "⚠️ Cached audio failed. "
            "Regenerating..."
        )

        try:

            cache_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass

        # Refresh USB speaker in case card number changed.
        speaker_device = (
            get_speaker_device(
                force_refresh=True
            )
        )

        if not speaker_device:

            return False

        configure_speaker_volume(
            speaker_device
        )

    # -----------------------------------------------------
    # New text:
    # stream from Edge directly into the speaker.
    # -----------------------------------------------------

    print(
        "🧠 Streaming new Mimi voice..."
    )

    result = (
        generate_and_stream_voice(
            text=
                text,

            cache_path=
                cache_path,

            speaker_device=
                speaker_device,
        )
    )

    elapsed = (
        time.monotonic()
        -
        started
    )

    if result:

        print(
            f"✅ Mimi finished speaking. "
            f"Total: "
            f"{elapsed:.2f}s"
        )

    return result


# =========================================================
# STANDALONE SPEED TEST
# =========================================================

if __name__ == "__main__":

    test_text = (
        "مرحبا، أنا ميمي بوت. "
        "كيف بقدر أساعدك؟"
    )

    print()
    print("=" * 60)
    print("🔊 MIMI FAST SPEAKER TEST")
    print("=" * 60)

    print()
    print(
        "TEST 1: New / network voice"
    )

    first_start = (
        time.monotonic()
    )

    first_result = speak(
        test_text
    )

    first_time = (
        time.monotonic()
        -
        first_start
    )

    print()
    print(
        f"First result: "
        f"{first_result}"
    )

    print(
        f"First total: "
        f"{first_time:.2f}s"
    )

    print()
    print(
        "TEST 2: Same sentence from cache"
    )

    second_start = (
        time.monotonic()
    )

    second_result = speak(
        test_text
    )

    second_time = (
        time.monotonic()
        -
        second_start
    )

    print()
    print(
        f"Second result: "
        f"{second_result}"
    )

    print(
        f"Second total: "
        f"{second_time:.2f}s"
    )

    print()
    print(
        f"Cached files: "
        f"{get_tts_cache_count()}"
    )

    print("=" * 60)