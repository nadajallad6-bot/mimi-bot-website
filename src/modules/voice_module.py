import re
import threading
import time
import unicodedata

from src.voice.speaker import (
    get_speaker_volume,
    speak,
    stop_playback,
    volume_down,
    volume_up,
)
from src.voice.voice_loop import VoiceListener


# =========================================================
# BARGE-IN SETTINGS
# =========================================================

BARGE_IN_PROFILE = {
    "start_timeout": 8.0,
    "end_silence": 0.45,
    "max_speech": 3.5,
}

BARGE_IN_POLL_SECONDS = 0.05


# =========================================================
# Arabic normalization
# =========================================================

_ARABIC_DIACRITICS = re.compile(
    r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]"
)


def normalize_command(text):

    text = str(
        text or ""
    ).strip().lower()

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = _ARABIC_DIACRITICS.sub(
        "",
        text,
    )

    text = text.replace(
        "ـ",
        "",
    )

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ى": "ي",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


STOP_COMMANDS = {
    "وقف",
    "وقفي",
    "توقف",
    "توقفي",
    "اسكت",
    "اسكتي",
    "خلص",
    "بس",
    "ميمي وقف",
    "ميمي وقفي",
    "ميمي توقف",
    "ميمي توقفي",
    "ميمي اسكتي",
    "ميمي خلص",
}

VOLUME_DOWN_COMMANDS = {
    "وطي الصوت",
    "وطي صوتك",
    "وطي شوي",
    "وطّي الصوت",
    "خفض الصوت",
    "خفضي الصوت",
    "قلل الصوت",
    "قللي الصوت",
    "نزل الصوت",
    "نزلي الصوت",
    "ميمي وطي الصوت",
    "ميمي وطي صوتك",
    "ميمي خفضي الصوت",
    "ميمي قللي الصوت",
    "ميمي نزلي الصوت",
}

VOLUME_UP_COMMANDS = {
    "علي الصوت",
    "علي صوتك",
    "علي شوي",
    "ارفع الصوت",
    "ارفعي الصوت",
    "زيد الصوت",
    "زيدي الصوت",
    "ميمي علي الصوت",
    "ميمي علي صوتك",
    "ميمي ارفعي الصوت",
    "ميمي زيدي الصوت",
}


# =========================================================
# Voice Module
# =========================================================

class VoiceModule:
    """
    Mimi Voice Module with Barge-In.

    Important behavior:
    - The microphone stays ON while Mimi speaks.
    - During Mimi speech, only short control commands are consumed:
        وقف
        وطي الصوت
        علي الصوت
    - Other recognized text during Mimi speech is ignored for now.
      This reduces self-triggering from Mimi's own speaker before AEC.
    """

    def __init__(self):

        self.listener = (
            VoiceListener()
        )

        self.started = False
        self.speaking = False
        self.closed = False

        self.lock = (
            threading.RLock()
        )

        self._speech_lock = (
            threading.Lock()
        )

        self._barge_stop_event = (
            threading.Event()
        )

        self._barge_thread = None

        self._saved_listener_profile = None
        self._saved_listener_values = None

        self.last_barge_command = None

    # =====================================================
    # Start
    # =====================================================

    def start(
        self,
        listening=False,
    ):

        with self.lock:

            if self.started:

                if listening:
                    self.enable()

                return True

            self.closed = False

        print()
        print("=" * 60)
        print("🎤 STARTING VOICE MODULE - BARGE IN")
        print("=" * 60)

        try:

            self.listener.start()

        except Exception as error:

            print(
                "❌ Voice Listener start error:",
                error,
            )

            return False

        with self.lock:

            self.started = True

        if listening:

            self.enable()

            print(
                "🎤 Microphone listening."
            )

        else:

            try:
                self.listener.disable()
            except Exception:
                pass

            print(
                "🎤 Microphone waiting."
            )

        print(
            "✅ Voice Module ready."
        )

        return True

    # =====================================================
    # Enable / Disable
    # =====================================================

    def enable(self):

        with self.lock:

            if self.closed:
                return False

            started = (
                self.started
            )

        if not started:

            return self.start(
                listening=True
            )

        try:

            self.listener.enable()

            return True

        except Exception as error:

            print(
                "⚠️ Microphone enable error:",
                error,
            )

            return False

    def disable(self):

        with self.lock:

            if not self.started:
                return True

        try:

            self.listener.disable()

            return True

        except Exception as error:

            print(
                "⚠️ Microphone disable error:",
                error,
            )

            return False

    # =====================================================
    # Existing compatibility helpers
    # =====================================================

    def pause_and_wait(
        self,
        timeout=6,
    ):

        with self.lock:

            if not self.started:
                return True

        try:

            self.listener.pause_and_wait(
                timeout=timeout
            )

            return True

        except TypeError:

            try:

                self.listener.pause_and_wait()

                return True

            except Exception:

                return False

        except Exception:

            return False

    def clear_commands(self):

        with self.lock:

            if not self.started:
                return True

        try:

            self.listener.clear_commands()

            return True

        except Exception:

            return False

    def set_listening_profile(
        self,
        profile_name="short",
        values=None,
    ):

        setter = getattr(
            self.listener,
            "set_listening_profile",
            None,
        )

        if not callable(setter):
            return False

        try:

            setter(
                profile_name,
                values or {},
            )

            return True

        except Exception as error:

            print(
                "⚠️ Listening profile error:",
                error,
            )

            return False

    # =====================================================
    # Barge-in profile
    # =====================================================

    def _save_listener_profile(self):

        self._saved_listener_profile = (
            getattr(
                self.listener,
                "current_profile",
                None,
            )
        )

        values = getattr(
            self.listener,
            "profile_values",
            None,
        )

        if isinstance(
            values,
            dict,
        ):

            self._saved_listener_values = (
                dict(values)
            )

        else:

            self._saved_listener_values = None

    def _apply_barge_profile(self):

        self._save_listener_profile()

        setter = getattr(
            self.listener,
            "set_listening_profile",
            None,
        )

        if callable(setter):

            try:

                setter(
                    "barge_in",
                    dict(
                        BARGE_IN_PROFILE
                    ),
                )

            except Exception:

                pass

    def _restore_listener_profile(self):

        profile = (
            self._saved_listener_profile
        )

        values = (
            self._saved_listener_values
        )

        if not profile:
            return

        setter = getattr(
            self.listener,
            "set_listening_profile",
            None,
        )

        if not callable(setter):
            return

        try:

            setter(
                profile,
                values or {},
            )

        except Exception:

            pass

    # =====================================================
    # Barge-in commands
    # =====================================================

    def _handle_barge_command(
        self,
        text,
    ):

        normalized = normalize_command(
            text
        )

        if not normalized:
            return False

        if normalized in STOP_COMMANDS:

            self.last_barge_command = (
                "stop"
            )

            print()
            print(
                f"🛑 Child interrupt: {text}"
            )

            stop_playback()

            return True

        if normalized in VOLUME_DOWN_COMMANDS:

            self.last_barge_command = (
                "volume_down"
            )

            print()
            print(
                f"🔉 Child interrupt: {text}"
            )

            volume_down(
                step=15
            )

            return True

        if normalized in VOLUME_UP_COMMANDS:

            self.last_barge_command = (
                "volume_up"
            )

            print()
            print(
                f"🔊 Child interrupt: {text}"
            )

            volume_up(
                step=15
            )

            return True

        # Important:
        # During Mimi speech we do not pass arbitrary recognized text
        # to the normal dialogue queue yet, because without AEC the
        # microphone can also hear Mimi's own speaker.
        return False

    def _barge_in_worker(self):

        while not self._barge_stop_event.is_set():

            with self.lock:

                if (
                    not self.speaking
                    or
                    self.closed
                ):
                    break

            try:

                text = (
                    self.listener.get_command()
                )

            except Exception:

                text = None

            if text:

                self._handle_barge_command(
                    text
                )

            time.sleep(
                BARGE_IN_POLL_SECONDS
            )

    def _start_barge_in(self):

        self._barge_stop_event.clear()

        self._apply_barge_profile()

        # The microphone MUST stay enabled while Mimi is speaking.
        self.enable()

        self._barge_thread = (
            threading.Thread(
                target=
                    self._barge_in_worker,
                daemon=True,
            )
        )

        self._barge_thread.start()

    def _stop_barge_in(self):

        self._barge_stop_event.set()

        thread = (
            self._barge_thread
        )

        if (
            thread is not None
            and
            thread.is_alive()
            and
            thread is not
            threading.current_thread()
        ):

            thread.join(
                timeout=1.0
            )

        self._barge_thread = None

        self._restore_listener_profile()

    # =====================================================
    # Mimi Speak
    # =====================================================

    def say(
        self,
        text,
        resume_listening=True,
    ):
        """
        Mimi speaks WITHOUT closing the microphone.

        During playback the child can say:
            وقف
            ميمي وقف
            وطي الصوت
            علي الصوت
        """

        text = str(
            text or ""
        ).strip()

        if not text:
            return False

        print()
        print(
            f"🤖 Mimi: {text}"
        )

        with self._speech_lock:

            with self.lock:

                if self.closed:
                    return False

                self.speaking = True
                self.last_barge_command = None

            playback_ok = False

            try:

                # Clear only stale commands BEFORE speaking.
                # We do NOT pause the microphone.
                self.clear_commands()

                if self.started:

                    self._start_barge_in()

                try:

                    playback_ok = bool(
                        speak(
                            text
                        )
                    )

                except Exception as error:

                    print()
                    print(
                        "❌ Voice output error:"
                    )

                    print(
                        error
                    )

                    playback_ok = False

                return playback_ok

            finally:

                with self.lock:
                    self.speaking = False

                self._stop_barge_in()

                if (
                    self.started
                    and
                    not self.closed
                ):

                    if resume_listening:

                        self.enable()

                    else:

                        self.disable()

    # =====================================================
    # External playback controls
    # =====================================================

    def stop_speaking(self):

        return stop_playback()

    def lower_volume(
        self,
        step=15,
    ):

        return volume_down(
            step=step
        )

    def raise_volume(
        self,
        step=15,
    ):

        return volume_up(
            step=step
        )

    def get_volume(self):

        return get_speaker_volume()

    # =====================================================
    # Commands outside Mimi speech
    # =====================================================

    def has_command(self):

        with self.lock:

            if (
                not self.started
                or
                self.closed
            ):
                return False

        try:

            return bool(
                self.listener.has_command()
            )

        except Exception:

            return False

    def get_command(self):

        with self.lock:

            if (
                not self.started
                or
                self.closed
            ):
                return None

        try:

            text = (
                self.listener.get_command()
            )

        except Exception:

            return None

        if text is None:
            return None

        text = str(
            text
        ).strip()

        return (
            text
            if text
            else None
        )

    def wait_for_command(
        self,
        timeout=20,
        poll_interval=0.1,
    ):

        start_time = (
            time.monotonic()
        )

        while True:

            with self.lock:

                if (
                    not self.started
                    or
                    self.closed
                ):
                    return None

            text = (
                self.get_command()
            )

            if text:
                return text

            if timeout is not None:

                if (
                    time.monotonic()
                    -
                    start_time
                    >=
                    float(timeout)
                ):
                    return None

            time.sleep(
                poll_interval
            )

    # =====================================================
    # State
    # =====================================================

    def is_speaking(self):

        with self.lock:

            return bool(
                self.speaking
            )

    def is_started(self):

        with self.lock:

            return bool(
                self.started
                and
                not self.closed
            )

    # =====================================================
    # Close
    # =====================================================

    def close(self):

        print()
        print(
            "🧹 Closing Voice Module..."
        )

        with self.lock:

            self.closed = True
            self.speaking = False

        stop_playback()

        self._stop_barge_in()

        try:
            self.listener.disable()
        except Exception:
            pass

        try:
            self.listener.clear_commands()
        except Exception:
            pass

        try:
            self.listener.stop()
        except Exception:
            pass

        with self.lock:
            self.started = False

        print(
            "✅ Voice Module closed."
        )

        return True


# =========================================================
# Standalone test
# =========================================================

def test_barge_in():

    voice = VoiceModule()

    try:

        if not voice.start(
            listening=True
        ):
            return

        print()
        print("=" * 60)
        print("🎤 BARGE-IN TEST")
        print("=" * 60)
        print(
            "خلال كلام ميمي جرّبي:"
        )
        print(
            "  وطي الصوت"
        )
        print(
            "  علي الصوت"
        )
        print(
            "  وقف"
        )
        print("=" * 60)

        voice.say(
            "مرحبا، أنا ميمي بوت. "
            "هذا اختبار طويل شوي حتى تقدري تحكي معي "
            "وأنا بتكلم. إذا كان صوتي عالي احكي وطي الصوت، "
            "وإذا بدك توقفي كلامي احكي وقف. "
            "أنا رح أضل سامعتك طول الوقت.",
            resume_listening=True,
        )

        print()
        print(
            "📌 Last barge command:",
            voice.last_barge_command,
        )

        print(
            "📌 Current volume:",
            voice.get_volume(),
        )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test stopped."
        )

    finally:

        voice.close()


if __name__ == "__main__":

    test_barge_in()
