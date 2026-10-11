import math
import subprocess
import sys
import tempfile
import threading
import time
import wave

from array import array
from collections import deque
from pathlib import Path

import speech_recognition as sr

from src.vision.mimi_vision import (
    detect_audio_devices,
)


# =========================================================
# AUDIO SETTINGS
# =========================================================

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2

LANGUAGE = "ar-PS"

# تقريبًا 100ms لكل chunk
CHUNK_SECONDS = 0.10

CHUNK_SAMPLES = int(
    SAMPLE_RATE
    * CHUNK_SECONDS
)

CHUNK_BYTES = (
    CHUNK_SAMPLES
    * SAMPLE_WIDTH
)


# =========================================================
# VAD SETTINGS
# =========================================================

# مدة أطول قليلًا لمعايرة ضوضاء المكان
CALIBRATION_SECONDS = 0.60

# ميمي تنتظر الطفل مدة أطول بعد السؤال
SPEECH_START_TIMEOUT = 6.0

# تعتبر الطفل خلص كلام إذا سكت تقريبًا ثانية
END_SILENCE_SECONDS = 0.80

# نحفظ صوت بسيط قبل اكتشاف الكلام
# حتى أول حرف ما ينقص
PRE_ROLL_SECONDS = 0.45

# تجاهل النقرات والأصوات القصيرة جدًا
MIN_SPEECH_SECONDS = 0.35

# السماح بإجابة أطول
MAX_SPEECH_SECONDS = 10.0

# لازم 3 chunks متتالية قبل اعتبار الصوت كلام
# لتقليل تأثير الضوضاء والخبطة المفاجئة
START_CONFIRM_CHUNKS = 2


# =========================================================
# VAD THRESHOLDS
# =========================================================

# أقل threshold مسموح
MIN_SPEECH_RMS = 300.0

# مهم:
# لا نخليه 4000 لأن ضوضاء المكان عندك
# وصلت فوق 4000.
MAX_SPEECH_RMS = 12000.0

# threshold فوق مستوى الضوضاء
NOISE_MULTIPLIER = 1.22

# زيادة ثابتة فوق الضوضاء
NOISE_OFFSET = 350.0

# تحديث بطيء لتقدير ضوضاء الغرفة
NOISE_ADAPTATION = 0.025

# أثناء استمرار الكلام نسمح للصوت
# أن ينخفض قليلًا عن threshold البداية
CONTINUE_THRESHOLD_RATIO = 0.85

# لازم صوت الاستمرار يكون أعلى من ضوضاء الغرفة بهامش.
CONTINUE_NOISE_MARGIN = 600.0

# =========================================================
# SAFETY - REAL LOUD SOUND DETECTOR
# =========================================================

# Candidate loud sound threshold.
# The threshold is adaptive:
# max(LOUD_MIN_RMS, room_noise * LOUD_NOISE_MULTIPLIER)
LOUD_MIN_RMS = 12000.0
LOUD_NOISE_MULTIPLIER = 2.40
LOUD_MAX_RMS_THRESHOLD = 28000.0

# One continuous sound can generate another candidate only
# after this cooldown. SafetyModule still requires 3 hits
# within 4 seconds before creating the real alert.
LOUD_CANDIDATE_COOLDOWN = 0.80


# =========================================================
# LISTENING PROFILE
# =========================================================

# الافتراضي دائمًا قصير.
ACTIVE_LISTENING_PROFILE_NAME = "short"

ACTIVE_LISTENING_PROFILE = {
    "start_timeout": 6.0,
    "end_silence": 0.80,
    "max_speech": 10.0,
}


def set_listening_profile(
    profile_name="short",
    values=None,
):
    """
    MimiBot ينادي هذه الدالة قبل فتح المايك.

    كل الأنشطة تستخدم short افتراضيًا.
    القرآن وحده يرسل quran_short / quran_medium / quran_long.
    """

    global ACTIVE_LISTENING_PROFILE_NAME
    global ACTIVE_LISTENING_PROFILE

    if not isinstance(values, dict):
        values = {}

    ACTIVE_LISTENING_PROFILE_NAME = str(
        profile_name or "short"
    )

    ACTIVE_LISTENING_PROFILE = {
        "start_timeout": float(
            values.get(
                "start_timeout",
                SPEECH_START_TIMEOUT,
            )
        ),
        "end_silence": float(
            values.get(
                "end_silence",
                END_SILENCE_SECONDS,
            )
        ),
        "max_speech": float(
            values.get(
                "max_speech",
                MAX_SPEECH_SECONDS,
            )
        ),
    }

    print(
        "🎤 Listening profile:",
        ACTIVE_LISTENING_PROFILE_NAME,
        ACTIVE_LISTENING_PROFILE,
    )


def reset_listening_profile():
    """
    يرجع المايك للوضع القصير.
    """

    set_listening_profile(
        "short",
        {
            "start_timeout": 6.0,
            "end_silence": 0.80,
            "max_speech": 10.0,
        },
    )


# =========================================================
# RUNTIME CACHE
# =========================================================

_cached_microphone_device = None
_cached_speech_threshold = None
_cached_noise_level = None

_recognizer = sr.Recognizer()

# Safety audio callback.
# It is registered by SafetyModule.start_module().
_audio_event_callback = None
_loud_detection_enabled = True
_last_loud_candidate_time = 0.0


def set_audio_event_callback(callback=None):
    """
    Register a callback that receives audio safety candidates.

    Expected callback signature:
        callback(
            event_type,
            sound_level=None,
            confidence=None,
            duration_ms=None,
        )
    """

    global _audio_event_callback

    _audio_event_callback = callback


def set_loud_detection_enabled(enabled=True):
    global _loud_detection_enabled

    _loud_detection_enabled = bool(
        enabled
    )


def get_loud_detection_state():
    room_noise = (
        float(_cached_noise_level)
        if _cached_noise_level is not None
        else None
    )

    if room_noise is None:
        threshold = LOUD_MIN_RMS
    else:
        threshold = max(
            LOUD_MIN_RMS,
            room_noise
            *
            LOUD_NOISE_MULTIPLIER,
        )

    threshold = min(
        LOUD_MAX_RMS_THRESHOLD,
        threshold,
    )

    return {
        "enabled":
            _loud_detection_enabled,
        "room_noise":
            room_noise,
        "threshold":
            float(threshold),
        "callback_registered":
            _audio_event_callback
            is not None,
    }


def _dispatch_audio_event(
    event_type,
    **kwargs,
):
    """
    Run Safety callback on another thread.

    Important:
    record_command() owns the microphone stream. The callback
    is dispatched asynchronously so Safety work never blocks
    the microphone capture loop. Mimi's microphone may remain
    enabled while audio is playing.
    """

    callback = (
        _audio_event_callback
    )

    if callback is None:
        return

    def worker():

        try:

            callback(
                event_type,
                **kwargs,
            )

        except Exception as error:

            print(
                "⚠️ Safety audio callback error:",
                error,
            )

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()


def _check_loud_sound_candidate(
    level,
):
    global _last_loud_candidate_time

    if not _loud_detection_enabled:
        return False

    if _audio_event_callback is None:
        return False

    try:
        level = float(level)
    except Exception:
        return False

    room_noise = (
        float(_cached_noise_level)
        if _cached_noise_level is not None
        else 0.0
    )

    loud_threshold = max(
        LOUD_MIN_RMS,
        room_noise
        *
        LOUD_NOISE_MULTIPLIER,
    )

    loud_threshold = min(
        LOUD_MAX_RMS_THRESHOLD,
        loud_threshold,
    )

    if level < loud_threshold:
        return False

    now = time.monotonic()

    if (
        now
        -
        _last_loud_candidate_time
        <
        LOUD_CANDIDATE_COOLDOWN
    ):
        return False

    _last_loud_candidate_time = now

    print()
    print(
        f"🔊 Loud candidate | "
        f"RMS={level:.0f} "
        f"| threshold={loud_threshold:.0f}"
    )

    _dispatch_audio_event(
        "loud_sound",
        sound_level=
            float(level),
        duration_ms=
            int(
                CHUNK_SECONDS
                *
                1000
            ),
    )

    return True



# =========================================================
# RMS
# =========================================================

def calculate_rms(
    raw_data,
):

    if not raw_data:
        return 0.0

    samples = array(
        "h"
    )

    samples.frombytes(
        raw_data
    )

    if (
        sys.byteorder
        !=
        "little"
    ):

        samples.byteswap()

    if not samples:
        return 0.0

    square_sum = 0

    for sample in samples:

        value = int(
            sample
        )

        square_sum += (
            value
            *
            value
        )

    mean_square = (
        square_sum
        /
        len(samples)
    )

    return math.sqrt(
        mean_square
    )


# =========================================================
# BUILD THRESHOLD
# =========================================================

def build_threshold(
    noise_level,
):

    noise_level = max(
        0.0,
        float(
            noise_level
        ),
    )

    threshold = (
        noise_level
        *
        NOISE_MULTIPLIER
        +
        NOISE_OFFSET
    )

    threshold = max(
        MIN_SPEECH_RMS,
        threshold,
    )

    threshold = min(
        MAX_SPEECH_RMS,
        threshold,
    )

    # =====================================================
    # حماية إضافية
    #
    # لازم threshold يكون دائمًا أعلى من
    # الضوضاء المقاسة.
    # =====================================================

    threshold = max(
        threshold,
        noise_level + 350.0,
    )

    return float(
        threshold
    )


# =========================================================
# MICROPHONE DEVICE
# =========================================================

def get_microphone_device(
    force_refresh=False,
):

    global _cached_microphone_device
    global _cached_speech_threshold
    global _cached_noise_level

    if (
        _cached_microphone_device
        and
        not force_refresh
    ):

        return (
            _cached_microphone_device
        )

    microphone_device, _ = (
        detect_audio_devices()
    )

    if not microphone_device:

        _cached_microphone_device = None

        return None

    if (
        microphone_device
        !=
        _cached_microphone_device
    ):

        _cached_speech_threshold = None
        _cached_noise_level = None

    _cached_microphone_device = (
        microphone_device
    )

    return (
        _cached_microphone_device
    )


# =========================================================
# START ARECORD
# =========================================================

def start_arecord(
    microphone_device,
):

    try:

        return subprocess.Popen(
            [
                "arecord",
                "-q",

                "-D",
                microphone_device,

                "-t",
                "raw",

                "-f",
                "S16_LE",

                "-r",
                str(
                    SAMPLE_RATE
                ),

                "-c",
                str(
                    CHANNELS
                ),
            ],

            stdout=
                subprocess.PIPE,

            stderr=
                subprocess.PIPE,

            bufsize=0,
        )

    except Exception as error:

        print()
        print(
            "❌ Could not start microphone:"
        )

        print(
            error
        )

        return None


# =========================================================
# STOP ARECORD
# =========================================================

def stop_arecord(
    process,
):

    if process is None:
        return

    try:

        if process.poll() is None:

            process.terminate()

            try:

                process.wait(
                    timeout=0.5
                )

            except subprocess.TimeoutExpired:

                process.kill()

                process.wait(
                    timeout=0.5
                )

    except Exception:

        try:

            process.kill()

        except Exception:

            pass


# =========================================================
# READ CHUNK
# =========================================================

def read_chunk(
    process,
):

    if (
        process is None
        or
        process.stdout is None
    ):

        return None

    try:

        data = (
            process.stdout.read(
                CHUNK_BYTES
            )
        )

    except Exception:

        return None

    if not data:
        return None

    return data


# =========================================================
# CALIBRATE
# =========================================================

def calibrate_microphone(
    process,
    cancel_check=None,
):

    global _cached_speech_threshold
    global _cached_noise_level

    count = max(
        1,
        int(
            CALIBRATION_SECONDS
            /
            CHUNK_SECONDS
        ),
    )

    levels = []

    print()
    print(
        "🎚️ ضبط ضوضاء المكان..."
    )

    for _ in range(
        count
    ):

        if (
            cancel_check
            and
            cancel_check()
        ):

            return None

        data = read_chunk(
            process
        )

        if data is None:
            return None

        level = calculate_rms(
            data
        )

        levels.append(
            level
        )

    if levels:

        # =================================================
        # بدل الاعتماد فقط على المتوسط:
        # نستخدم المتوسط مع أعلى قراءة بشكل بسيط
        # حتى ما نقلل الضوضاء الموجودة في المكان.
        # =================================================

        average_noise = (
            sum(levels)
            /
            len(levels)
        )

        peak_noise = max(
            levels
        )

        noise_level = (
            average_noise * 0.75
            +
            peak_noise * 0.25
        )

    else:

        noise_level = 0.0

    threshold = build_threshold(
        noise_level
    )

    _cached_noise_level = (
        float(
            noise_level
        )
    )

    _cached_speech_threshold = (
        threshold
    )

    print(
        "✅ المايك جاهز."
    )

    print(
        f"🎚️ Noise: "
        f"{noise_level:.0f}"
    )

    print(
        f"🎯 Voice threshold: "
        f"{threshold:.0f}"
    )

    return threshold


# =========================================================
# UPDATE ROOM NOISE
# =========================================================

def update_noise_estimate(
    level,
):

    global _cached_noise_level
    global _cached_speech_threshold

    level = float(
        level
    )

    if _cached_noise_level is None:

        _cached_noise_level = (
            level
        )

    else:

        _cached_noise_level = (
            (
                1.0
                -
                NOISE_ADAPTATION
            )
            *
            _cached_noise_level
            +
            NOISE_ADAPTATION
            *
            level
        )

    _cached_speech_threshold = (
        build_threshold(
            _cached_noise_level
        )
    )

    return (
        _cached_speech_threshold
    )


# =========================================================
# SAVE WAV
# =========================================================

def save_wav(
    audio_path,
    chunks,
):

    try:

        with wave.open(
            str(
                audio_path
            ),
            "wb",
        ) as wav_file:

            wav_file.setnchannels(
                CHANNELS
            )

            wav_file.setsampwidth(
                SAMPLE_WIDTH
            )

            wav_file.setframerate(
                SAMPLE_RATE
            )

            wav_file.writeframes(
                b"".join(
                    chunks
                )
            )

        return True

    except Exception as error:

        print()
        print(
            "❌ Could not save WAV:"
        )

        print(
            error
        )

        return False


# =========================================================
# RECORD COMMAND
# =========================================================

def record_command(
    cancel_check=None,
):

    global _cached_speech_threshold

    # نأخذ نسخة من الـprofile الحالي لهذه المرة فقط.
    start_timeout = float(
        ACTIVE_LISTENING_PROFILE.get(
            "start_timeout",
            SPEECH_START_TIMEOUT,
        )
    )

    end_silence = float(
        ACTIVE_LISTENING_PROFILE.get(
            "end_silence",
            END_SILENCE_SECONDS,
        )
    )

    max_speech = float(
        ACTIVE_LISTENING_PROFILE.get(
            "max_speech",
            MAX_SPEECH_SECONDS,
        )
    )

    print(
        f"🎛️ Active profile: {ACTIVE_LISTENING_PROFILE_NAME} | "
        f"start={start_timeout:.1f}s | "
        f"silence={end_silence:.2f}s | "
        f"max={max_speech:.1f}s"
    )

    microphone_device = (
        get_microphone_device()
    )

    if not microphone_device:

        print(
            "❌ Microphone not found."
        )

        return None

    audio_path = (
        Path(
            tempfile.gettempdir()
        )
        /
        "mimi_command.wav"
    )

    process = start_arecord(
        microphone_device
    )

    if process is None:
        return None

    try:

        # =================================================
        # CALIBRATION
        # =================================================

        if (
            _cached_speech_threshold
            is None
        ):

            threshold = (
                calibrate_microphone(
                    process,
                    cancel_check=
                        cancel_check,
                )
            )

            if threshold is None:
                return None

        # =================================================
        # READY
        # =================================================

        print()
        print(
            "🎤 Mimi is listening..."
        )

        print(
            "احكي الآن..."
        )

        pre_roll_count = max(
            1,
            int(
                PRE_ROLL_SECONDS
                /
                CHUNK_SECONDS
            ),
        )

        pre_roll = deque(
            maxlen=
                pre_roll_count
        )

        audio_chunks = []

        speech_started = False

        start_voice_chunks = 0

        silence_seconds = 0.0

        speech_seconds = 0.0

        wait_start = (
            time.monotonic()
        )

        # =================================================
        # LISTEN LOOP
        # =================================================

        while True:

            if (
                cancel_check
                and
                cancel_check()
            ):

                return None

            data = read_chunk(
                process
            )

            if data is None:
                return None

            level = calculate_rms(
                data
            )

            # Feed the SAME microphone stream to Safety.
            # We do not open a second arecord process.
            _check_loud_sound_candidate(
                level
            )

            # Use latest adaptive threshold
            threshold = (
                _cached_speech_threshold
                or
                MIN_SPEECH_RMS
            )

            # =================================================
            # BEFORE CHILD STARTS TALKING
            # =================================================

            if not speech_started:

                pre_roll.append(
                    data
                )

                # -----------------------------------------
                # Strong enough to be possible speech
                # -----------------------------------------

                if level >= threshold:

                    start_voice_chunks += 1

                else:

                    start_voice_chunks = 0

                    # -------------------------------------
                    # Room noise only.
                    # Adapt slowly.
                    # -------------------------------------

                    threshold = (
                        update_noise_estimate(
                            level
                        )
                    )

                # -----------------------------------------
                # Confirm speech
                # -----------------------------------------

                if (
                    start_voice_chunks
                    >=
                    START_CONFIRM_CHUNKS
                ):

                    speech_started = True

                    audio_chunks.extend(
                        list(
                            pre_roll
                        )
                    )

                    speech_seconds = (
                        len(
                            audio_chunks
                        )
                        *
                        CHUNK_SECONDS
                    )

                    silence_seconds = 0.0

                    print(
                        "🟢 Speech detected."
                    )

                    continue

                # -----------------------------------------
                # Nobody spoke
                # -----------------------------------------

                if (
                    time.monotonic()
                    -
                    wait_start
                    >=
                    start_timeout
                ):

                    print()
                    print(
                        "⌛ No clear speech detected."
                    )

                    return None

                continue

            # =================================================
            # CHILD IS TALKING
            # =================================================

            audio_chunks.append(
                data
            )

            speech_seconds += (
                CHUNK_SECONDS
            )

            room_noise = (
                _cached_noise_level
                if _cached_noise_level is not None
                else 0.0
            )

            continuation_threshold = max(
                MIN_SPEECH_RMS,
                threshold
                *
                CONTINUE_THRESHOLD_RATIO,
                room_noise
                +
                CONTINUE_NOISE_MARGIN,
            )

            # ---------------------------------------------
            # Still talking
            # ---------------------------------------------

            if (
                level
                >=
                continuation_threshold
            ):

                silence_seconds = 0.0

            # ---------------------------------------------
            # Silence
            # ---------------------------------------------

            else:

                silence_seconds += (
                    CHUNK_SECONDS
                )

            # ---------------------------------------------
            # Natural end of speech
            # ---------------------------------------------

            if (
                speech_seconds
                >=
                MIN_SPEECH_SECONDS
                and
                silence_seconds
                >=
                end_silence
            ):

                print(
                    "🔵 End of speech detected."
                )

                break

            # ---------------------------------------------
            # Protection from false continuous detection
            # ---------------------------------------------

            if (
                speech_seconds
                >=
                max_speech
            ):

                print()
                print(
                    "⚠️ Maximum recording safety limit reached."
                )

                print(
                    "💾 Keeping the recorded speech."
                )

                break

        # =================================================
        # SAVE AUDIO
        # =================================================

        if not audio_chunks:
            return None

        if not save_wav(
            audio_path,
            audio_chunks,
        ):

            return None

        print(
            "✅ Recording ready."
        )

        return audio_path

    finally:

        stop_arecord(
            process
        )


# =========================================================
# SPEECH RECOGNITION
# =========================================================

def recognize_audio(
    audio_path,
):

    try:

        with sr.AudioFile(
            str(
                audio_path
            )
        ) as source:

            audio = (
                _recognizer.record(
                    source
                )
            )

        print(
            "🧠 Understanding speech..."
        )

        text = (
            _recognizer
            .recognize_google(
                audio,
                language=
                    LANGUAGE,
            )
        )

        text = str(
            text
        ).strip()

        if not text:
            return None

        print()
        print(
            f"📝 STT result: "
            f"{text}"
        )

        return text

    except sr.UnknownValueError:

        print()
        print(
            "⚠️ Google STT couldn't "
            "understand this audio."
        )

        return None

    except sr.RequestError as error:

        print()
        print(
            "❌ Speech Recognition "
            "service error:"
        )

        print(
            error
        )

        return None

    except Exception as error:

        print()
        print(
            "❌ Speech error:"
        )

        print(
            error
        )

        return None


# =========================================================
# LISTEN ONCE
# =========================================================

def listen_once(
    cancel_check=None,
):

    audio_path = (
        record_command(
            cancel_check=
                cancel_check
        )
    )

    if audio_path is None:
        return None

    if (
        cancel_check
        and
        cancel_check()
    ):

        try:

            audio_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass

        return None

    try:

        return (
            recognize_audio(
                audio_path
            )
        )

    finally:

        try:

            audio_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass


# =========================================================
# RESET AUDIO CACHE
# =========================================================

def reset_audio_cache():

    global _cached_microphone_device
    global _cached_speech_threshold
    global _cached_noise_level
    global _last_loud_candidate_time

    _cached_microphone_device = None
    _cached_speech_threshold = None
    _cached_noise_level = None
    _last_loud_candidate_time = 0.0


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🎤 MIMI SMART LISTENER TEST")
    print("=" * 60)

    start = (
        time.monotonic()
    )

    text = (
        listen_once()
    )

    elapsed = (
        time.monotonic()
        -
        start
    )

    print()
    print("=" * 60)

    if text:

        print(
            f"✅ RESULT: {text}"
        )

    else:

        print(
            "⚠️ No command."
        )

    print(
        f"⏱️ Time: "
        f"{elapsed:.2f}s"
    )

    print("=" * 60)