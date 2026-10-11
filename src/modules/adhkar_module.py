
import re
import subprocess
import time
import unicodedata
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ADHKAR_AUDIO_DIR = (
    PROJECT_ROOT
    / "data"
    / "adhkar"
    / "audio"
)

SABAH_MASAA_AUDIO = (
    ADHKAR_AUDIO_DIR
    / "sabahandmasaa.mp3"
)

SLEEP_AUDIO = (
    ADHKAR_AUDIO_DIR
    / "sleep.mp3"
)


# =========================================================
# ADHKAR SEGMENTS
# =========================================================

ADHKAR_SEGMENTS = {
    "morning": {
        "title": "أذكار الصباح",
        "file": SABAH_MASAA_AUDIO,
        "start": 18.20,
        "end": 26.3,
    },
    "evening": {
        "title": "أذكار المساء",
        "file": SABAH_MASAA_AUDIO,
        "start": 34.0,
        "end": 42.0,
    },
    "sleep": {
        "title": "أذكار النوم",
        "file": SLEEP_AUDIO,
        "start": 9.0,
        "end": 25.0,
    },
}


# =========================================================
# NORMALIZATION + BARGE-IN COMMANDS
# =========================================================

def normalize_arabic(text):

    text = str(
        text or ""
    ).strip().lower()

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
        "",
        text,
    )

    text = text.replace(
        "ـ",
        "",
    )

    for old, new in {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }.items():

        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


ADHKAR_BARGE_PROFILE = {
    "start_timeout": 8.0,
    "end_silence": 0.45,
    "max_speech": 3.5,
}

ADHKAR_STOP_COMMANDS = {
    normalize_arabic("وقف"),
    normalize_arabic("وقفي"),
    normalize_arabic("توقف"),
    normalize_arabic("توقفي"),
    normalize_arabic("اسكت"),
    normalize_arabic("اسكتي"),
    normalize_arabic("خلص"),
    normalize_arabic("بس"),
    normalize_arabic("ميمي وقف"),
    normalize_arabic("ميمي وقفي"),
    normalize_arabic("ميمي توقفي"),
    normalize_arabic("ميمي اسكتي"),
    normalize_arabic("ميمي خلص"),
}

ADHKAR_VOLUME_DOWN_COMMANDS = {
    normalize_arabic("وطي الصوت"),
    normalize_arabic("وطي صوتك"),
    normalize_arabic("وطي شوي"),
    normalize_arabic("خفض الصوت"),
    normalize_arabic("خفضي الصوت"),
    normalize_arabic("قلل الصوت"),
    normalize_arabic("قللي الصوت"),
    normalize_arabic("نزل الصوت"),
    normalize_arabic("نزلي الصوت"),
    normalize_arabic("ميمي وطي الصوت"),
    normalize_arabic("ميمي وطي صوتك"),
}

ADHKAR_VOLUME_UP_COMMANDS = {
    normalize_arabic("علي الصوت"),
    normalize_arabic("علي صوتك"),
    normalize_arabic("علي شوي"),
    normalize_arabic("ارفع الصوت"),
    normalize_arabic("ارفعي الصوت"),
    normalize_arabic("زيد الصوت"),
    normalize_arabic("زيدي الصوت"),
    normalize_arabic("ميمي علي الصوت"),
    normalize_arabic("ميمي علي صوتك"),
}


# =========================================================
# ADHKAR MODULE
# =========================================================

class AdhkarModule:

    def __init__(
        self,
        voice_module=None,
        face_module=None,
    ):
        self.voice = voice_module
        self.face = face_module

        self.started = False
        self.mode = None

        self.audio_process = None
        self.decoder_process = None
        self.audio_playing = False

        # Live playback controls
        self.adhkar_stop_requested = False
        self.last_control_command = None

        self._saved_listener_profile = None
        self._saved_listener_values = None

    # =====================================================
    # FACE HELPERS
    # =====================================================

    def set_face(self, expression):
        if self.face is None:
            return False

        try:
            self.face.set_expression(expression)
            self.face.update()
            return True
        except Exception as error:
            print("⚠️ Adhkar face error:", error)
            return False

    def set_talking_face(self):
        self.set_face("talking")

    def set_listening_face(self):
        self.set_face("listening")

    # =====================================================
    # START MODULE
    # =====================================================

    def start_module(self):
        if self.started:
            return

        print()
        print("=" * 60)
        print("🤲 STARTING ADHKAR MODULE")
        print("=" * 60)

        print()
        print("🌅 Morning/Evening file:")
        print(SABAH_MASAA_AUDIO)
        print(
            "✅ Morning/Evening audio found."
            if SABAH_MASAA_AUDIO.exists()
            else "❌ Morning/Evening audio missing."
        )

        print()
        print("😴 Sleep file:")
        print(SLEEP_AUDIO)
        print(
            "✅ Sleep audio found."
            if SLEEP_AUDIO.exists()
            else "❌ Sleep audio missing."
        )

        print()
        print("🌅 Morning: 10s -> 26s")
        print("🌙 Evening: 34s -> 42s")
        print("😴 Sleep: 9s -> 31s")

        self.started = True

        print()
        print("✅ Adhkar Module ready.")
        print("=" * 60)

    # =====================================================
    # SET MODULES
    # =====================================================

    def set_voice(self, voice_module):
        self.voice = voice_module

    def set_face_module(self, face_module):
        self.face = face_module

    # =====================================================
    # SAY
    # =====================================================

    def say(
        self,
        text,
        resume_listening=True,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:
            return False

        self.set_talking_face()

        result = True

        try:

            if self.voice is not None:

                try:

                    voice_result = self.voice.say(
                        text,
                        resume_listening=
                            resume_listening,
                    )

                except TypeError:

                    voice_result = (
                        self.voice.say(
                            text
                        )
                    )

                result = (
                    True
                    if voice_result is None
                    else bool(voice_result)
                )

                if (
                    getattr(
                        self.voice,
                        "last_barge_command",
                        None,
                    )
                    ==
                    "stop"
                ):

                    self.adhkar_stop_requested = True
                    self.last_control_command = "stop"

            else:

                print()
                print(
                    f"🤖 Mimi: {text}"
                )

        finally:

            if (
                resume_listening
                and
                not self.adhkar_stop_requested
            ):

                self.set_listening_face()

        return result


    # =====================================================
    # MICROPHONE / LIVE CONTROL
    # =====================================================

    def disable_microphone(self):
        """
        Kept only for backward compatibility.

        For Adhkar playback we no longer disable the microphone.
        """
        if self.voice is None:
            return

        try:
            self.voice.disable()
        except Exception:
            pass

        try:
            self.voice.clear_commands()
        except Exception:
            pass

    def enable_microphone(self):

        if self.voice is None:
            return

        try:
            self.voice.clear_commands()
        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception:
            pass

    def _save_listener_profile(self):

        if self.voice is None:
            return

        listener = getattr(
            self.voice,
            "listener",
            None,
        )

        if listener is None:
            return

        self._saved_listener_profile = getattr(
            listener,
            "current_profile",
            None,
        )

        values = getattr(
            listener,
            "profile_values",
            None,
        )

        self._saved_listener_values = (
            dict(values)
            if isinstance(values, dict)
            else None
        )

    def _enable_adhkar_barge_in(self):

        if self.voice is None:
            return

        self._save_listener_profile()

        try:
            self.voice.clear_commands()
        except Exception:
            pass

        try:

            setter = getattr(
                self.voice,
                "set_listening_profile",
                None,
            )

            if callable(setter):

                setter(
                    "adhkar_barge_in",
                    dict(
                        ADHKAR_BARGE_PROFILE
                    ),
                )

        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception as error:
            print(
                "⚠️ Adhkar microphone enable error:",
                error,
            )

    def _restore_listener_profile(self):

        if self.voice is None:
            return

        profile = (
            self._saved_listener_profile
        )

        values = (
            self._saved_listener_values
        )

        if profile:

            try:

                setter = getattr(
                    self.voice,
                    "set_listening_profile",
                    None,
                )

                if callable(setter):

                    setter(
                        profile,
                        values or {},
                    )

            except Exception:
                pass

        self._saved_listener_profile = None
        self._saved_listener_values = None

    def _poll_adhkar_control(self):

        if self.voice is None:
            return None

        try:
            text = self.voice.get_command()
        except Exception:
            text = None

        if not text:
            return None

        normalized = normalize_arabic(
            text
        )

        if normalized in ADHKAR_STOP_COMMANDS:

            self.adhkar_stop_requested = True
            self.last_control_command = "stop"

            print()
            print(
                f"🛑 Adhkar command: {text}"
            )

            return "stop"

        if normalized in ADHKAR_VOLUME_DOWN_COMMANDS:

            self.last_control_command = "volume_down"

            print()
            print(
                f"🔉 Adhkar command: {text}"
            )

            try:

                lower = getattr(
                    self.voice,
                    "lower_volume",
                    None,
                )

                if callable(lower):
                    lower(
                        step=15
                    )

            except Exception as error:

                print(
                    "⚠️ Could not lower Adhkar volume:",
                    error,
                )

            return None

        if normalized in ADHKAR_VOLUME_UP_COMMANDS:

            self.last_control_command = "volume_up"

            print()
            print(
                f"🔊 Adhkar command: {text}"
            )

            try:

                raise_volume = getattr(
                    self.voice,
                    "raise_volume",
                    None,
                )

                if callable(
                    raise_volume
                ):
                    raise_volume(
                        step=15
                    )

            except Exception as error:

                print(
                    "⚠️ Could not raise Adhkar volume:",
                    error,
                )

            return None

        # Ordinary speech is ignored during the MP3 for now.
        # Without AEC the speaker can be picked up by the mic.
        return None


    # =====================================================
    # GET SEGMENT
    # =====================================================

    def get_segment(self, mode):
        return ADHKAR_SEGMENTS.get(mode)

    # =====================================================
    # STOP AUDIO
    # =====================================================

    def stop_audio(self):
        player = self.audio_process
        decoder = self.decoder_process

        self.audio_process = None
        self.decoder_process = None
        self.audio_playing = False

        stopped = False

        for process in (player, decoder):
            if process is None:
                continue

            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1.0)
                stopped = True
            except Exception:
                pass

        if stopped:
            print()
            print("🛑 Adhkar audio stopped.")

        return stopped

    # =====================================================
    # PLAY SEGMENT
    # =====================================================

    def play_segment(self, mode):

        segment = self.get_segment(
            mode
        )

        if segment is None:

            print()
            print(
                f"❌ Unknown adhkar mode: {mode}"
            )

            return False

        audio_file = segment.get(
            "file"
        )

        if audio_file is None:

            print()
            print(
                "❌ Audio file not configured."
            )

            return False

        audio_file = Path(
            audio_file
        )

        if not audio_file.exists():

            print()
            print(
                "❌ Adhkar audio file missing:"
            )
            print(
                audio_file
            )

            return False

        start_seconds = float(
            segment.get(
                "start",
                0.0,
            )
            or 0.0
        )

        end_seconds = float(
            segment.get(
                "end",
                0.0,
            )
            or 0.0
        )

        duration = (
            end_seconds
            -
            start_seconds
        )

        if duration <= 0:

            print()
            print(
                "❌ Invalid adhkar duration."
            )

            return False

        self.stop_audio()

        self.adhkar_stop_requested = False
        self.last_control_command = None

        self._enable_adhkar_barge_in()

        self.set_talking_face()

        print()
        print("=" * 60)
        print(
            f"🤲 Playing {segment.get('title')}"
        )
        print(
            f"🎧 File: {audio_file}"
        )
        print(
            f"▶️ Start: {start_seconds:.1f}s"
        )
        print(
            f"⏹️ End: {end_seconds:.1f}s"
        )
        print(
            f"⏱️ Duration: {duration:.1f}s"
        )
        print(
            "🎤 Microphone stays ON: "
            "وقف / وطي الصوت / علي الصوت"
        )
        print("=" * 60)

        ffmpeg_command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-ss",
            str(start_seconds),
            "-t",
            str(duration),
            "-i",
            str(audio_file),
            "-vn",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "pipe:1",
        ]

        aplay_command = [
            "aplay",
            "-q",
            "-D",
            "plughw:2,0",
            "-f",
            "S16_LE",
            "-c",
            "2",
            "-r",
            "48000",
        ]

        try:

            self.audio_playing = True

            self.decoder_process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.audio_process = subprocess.Popen(
                aplay_command,
                stdin=self.decoder_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

            if self.decoder_process.stdout is not None:
                self.decoder_process.stdout.close()

            while self.audio_process.poll() is None:

                command = self._poll_adhkar_control()

                if command == "stop":

                    self.stop_audio()

                    print()
                    print(
                        "🛑 Adhkar audio stopped by child."
                    )

                    return False

                if self.face is not None:

                    try:
                        self.face.update()
                    except Exception as error:
                        print(
                            "⚠️ Adhkar face update error:",
                            error,
                        )

                time.sleep(
                    0.03
                )

            player_code = (
                self.audio_process.returncode
            )

            try:

                decoder_code = (
                    self.decoder_process.wait(
                        timeout=2.0
                    )
                )

            except subprocess.TimeoutExpired:

                self.decoder_process.terminate()

                decoder_code = (
                    self.decoder_process.wait(
                        timeout=1.0
                    )
                )

            player_error = b""
            decoder_error = b""

            if self.audio_process.stderr is not None:

                try:
                    player_error = (
                        self.audio_process.stderr.read()
                    )
                except Exception:
                    pass

            if self.decoder_process.stderr is not None:

                try:
                    decoder_error = (
                        self.decoder_process.stderr.read()
                    )
                except Exception:
                    pass

            self.audio_process = None
            self.decoder_process = None
            self.audio_playing = False

            if (
                player_code != 0
                or
                decoder_code != 0
            ):

                print()
                print(
                    "❌ Adhkar audio playback failed."
                )

                if decoder_error:
                    print(
                        decoder_error.decode(
                            errors="ignore"
                        ).strip()
                    )

                if player_error:
                    print(
                        player_error.decode(
                            errors="ignore"
                        ).strip()
                    )

                return False

            print()
            print(
                "✅ Adhkar audio finished."
            )

            # Give ALSA a short moment before Mimi TTS.
            time.sleep(
                0.60
            )

            return True

        except FileNotFoundError as error:

            print()
            print(
                "❌ Audio playback tool missing:"
            )
            print(
                error
            )
            print(
                "Run: sudo apt install "
                "ffmpeg alsa-utils -y"
            )

            self.stop_audio()

            return False

        except Exception as error:

            print()
            print(
                "❌ Adhkar audio error:"
            )
            print(
                error
            )

            self.stop_audio()

            return False

        finally:

            self._restore_listener_profile()


    # =====================================================
    # START HELPERS
    # =====================================================

    def start_morning(self):
        return self.start_adhkar("morning")

    def start_evening(self):
        return self.start_adhkar("evening")

    def start_sleep(self):
        return self.start_adhkar("sleep")

    # =====================================================
    # START ADHKAR
    # =====================================================

    def start_adhkar(self, mode):
        if not self.started:
            self.start_module()

        if mode not in ("morning", "evening", "sleep"):
            return {
                "started": False,
                "completed": False,
                "error": "invalid_mode",
            }

        self.stop_audio()

        self.adhkar_stop_requested = False
        self.last_control_command = None

        self.mode = mode

        if mode == "morning":
            intro = "يلا نقرأ أذكار الصباح سوا."
        elif mode == "evening":
            intro = "يلا نقرأ أذكار المساء سوا."
        else:
            intro = "قبل ما ننام، يلا نقرأ أذكار النوم سوا."

        # Mimi intro + talking face
        self.say(
            intro,
            resume_listening=False,
        )

        if self.adhkar_stop_requested:

            self.mode = None
            self.enable_microphone()
            self.set_listening_face()

            return {
                "started": False,
                "completed": False,
                "stopped": True,
                "mode": mode,
            }

        # Sheikh audio + talking face
        success = self.play_segment(mode)

        if not success:

            self.mode = None
            self.enable_microphone()
            self.set_listening_face()

            if self.adhkar_stop_requested:

                return {
                    "started": True,
                    "completed": False,
                    "stopped": True,
                    "mode": mode,
                }

            return {
                "started": True,
                "completed": False,
                "mode": mode,
                "error": "audio_failed",
            }

        self.mode = None

        # بعد انتهاء الشيخ:
        # Mimi تقول جملة ختامية ثم ترجع للاستماع.
        self.say(
            "تقبل الله منك. شو بدك نعمل الآن؟",
            resume_listening=True,
        )

        self.enable_microphone()
        self.set_listening_face()

        return {
            "started": True,
            "completed": True,
            "mode": mode,
        }

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):
        if self.mode is None and not self.audio_playing:
            return False

        print()
        print("🛑 Stopping Adhkar...")

        self.stop_audio()
        self.mode = None

        self.adhkar_stop_requested = True
        self.last_control_command = "stop"

        self.say(
            "تمام، بنقدر نكمل أذكارنا بعدين. شو بتحب نعمل هسا؟",
            resume_listening=True,
        )

        self.enable_microphone()
        self.set_listening_face()

        return True

    # =====================================================
    # STATE
    # =====================================================

    def is_active(self):
        return self.mode is not None or self.audio_playing

    def is_morning(self):
        return self.mode == "morning"

    def is_evening(self):
        return self.mode == "evening"

    def is_sleep(self):
        return self.mode == "sleep"

    def is_playing(self):
        return bool(self.audio_playing)

    def get_state(self):
        return {
            "mode": self.mode,
            "audio_playing": self.audio_playing,
            "morning_evening_file": str(SABAH_MASAA_AUDIO),
            "sleep_file": str(SLEEP_AUDIO),
            "adhkar_stop_requested":
                self.adhkar_stop_requested,
            "last_control_command":
                self.last_control_command,
        }

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):
        self.stop_audio()
        self.mode = None

        self.adhkar_stop_requested = False
        self.last_control_command = None
        self.enable_microphone()
        self.set_listening_face()

        print()
        print("🤲 Adhkar session reset.")

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):
        self.stop_audio()
        self.mode = None
        self.started = False

        print()
        print("✅ Adhkar Module closed.")


# =========================================================
# STANDALONE TEST
# =========================================================

def test_adhkar():
    from src.modules.voice_module import VoiceModule

    voice = VoiceModule()
    adhkar = None

    try:
        voice.start(listening=False)

        adhkar = AdhkarModule(
            voice_module=voice,
            face_module=None,
        )

        adhkar.start_module()

        print()
        print("=" * 60)
        print("🤲 ADHKAR TEST")
        print("=" * 60)
        print()
        print("1 = Morning")
        print("2 = Evening")
        print("3 = Sleep")

        choice = input("\nChoose: ").strip()

        if choice == "1":
            adhkar.start_morning()
        elif choice == "2":
            adhkar.start_evening()
        elif choice == "3":
            adhkar.start_sleep()
        else:
            print("❌ Invalid choice.")

    except KeyboardInterrupt:
        print()
        if adhkar is not None:
            adhkar.stop()

    finally:
        if adhkar is not None:
            adhkar.close()
        voice.close()


if __name__ == "__main__":
    test_adhkar()