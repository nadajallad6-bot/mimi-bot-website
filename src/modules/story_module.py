import re
import subprocess
import time
import unicodedata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORY_AUDIO_DIR = PROJECT_ROOT / "data" / "stories" / "audio"


# =========================================================
# STORY DATA
# =========================================================

STORIES = {
    "animals": {
        "title": "الأرنب والسلحفاة",
        "audio": (
            STORY_AUDIO_DIR
            / "animals"
            / "rabbit_turtle"
            / "rabbit_turtle.mp3"
        ),
        "duration": 121.104,
        "checkpoints": [
            {
                "time": 62.0,
                "question": (
                    "أوووه! استنى استنى... صار الموضوع حماااس! "
                    "مين بتتوقع يوصل أول؟ الأرنب السريع، ولا السلحفاة؟"
                ),
                "keywords": [
                    "الأرنب",
                    "الارنب",
                    "ارنب",
                    "السلحفاة",
                    "السلحفاه",
                    "سلحفاة",
                    "سلحفاه",
                ],
                "correct_response": (
                    "يا سلام! حبيت توقعك! يلا نكمل القصة "
                    "ونشوف إذا توقعك صح."
                ),
                "other_response": (
                    "حلووو! فكرة لطيفة. يلا نكمل ونشوف "
                    "مين رح يوصل أول!"
                ),
            },
            {
                "time": 86.0,
                "question": (
                    "واااو! شفت شو صار؟ ساعدني أفكر... "
                    "ليش بتفكر السلحفاة قدرت تكمل وتفوز؟"
                ),
                "keywords": [
                    "ما استسلمت",
                    "ما استسلم",
                    "كملت",
                    "استمرت",
                    "صبرت",
                    "ما وقفت",
                    "مثابرة",
                    "حاولت",
                ],
                "correct_response": (
                    "شاطررر! بالزبط، لأنها ضلت تحاول وما استسلمت. "
                    "يلا نكمل!"
                ),
                "other_response": (
                    "جواب حلو! أهم إشي إنها ضلت تحاول وما وقفت. "
                    "يلا نشوف النهاية."
                ),
            },
        ],
    },
    "funny": {
        "title": "زوزو مش عايز يستحمى",
        "audio": STORY_AUDIO_DIR / "funny" / "funny.mp3",
        "duration": 145.084,
        "checkpoints": [
            {
                "time": 40.0,
                "question": (
                    "ههههه زوزو مش بده يتحمم! إنت شو رأيك؟ "
                    "لازم زوزو يتحمم ويصير نظيف، ولا لأ؟"
                ),
                "keywords": [
                    "آه",
                    "اه",
                    "نعم",
                    "ايوه",
                    "لازم",
                    "يتحمم",
                    "يستحم",
                    "نظيف",
                    "النظافة",
                ],
                "correct_response": (
                    "ييي شاطر! أكيد لازم نهتم بنظافتنا. "
                    "يلا نشوف زوزو شو رح يعمل!"
                ),
                "other_response": (
                    "هههه حلو جوابك! يلا نكمل ونشوف "
                    "إذا زوزو رح يغيّر رأيه."
                ),
            }
        ],
    },
    "educational": {
        "title": "وعد الكتكوت كوك",
        "audio": STORY_AUDIO_DIR / "educational" / "educational.mp3",
        "duration": 122.279,
        "checkpoints": [
            {
                "time": 40.0,
                "question": (
                    "لحظة لحظة! كوك وعد يرجع قبل الساعة خمسة. "
                    "بتتوقع يلتزم بوعده ويرجع عالوقت؟"
                ),
                "keywords": [
                    "آه",
                    "اه",
                    "نعم",
                    "ايوه",
                    "يرجع",
                    "يلتزم",
                    "بوعده",
                    "عالوقت",
                    "على الوقت",
                    "لا",
                    "مش",
                ],
                "correct_response": (
                    "حلو توقعك! يلا نكمل ونشوف إذا كوك رح يلتزم بوعده."
                ),
                "other_response": (
                    "مممم توقع مثير! يلا نكمل ونشوف شو رح يصير."
                ),
            }
        ],
    },
    "adventure": {
        "title": "النملة والقمح",
        "audio": STORY_AUDIO_DIR / "adventure" / "adventure.mp3",
        "duration": 166.165,
        "checkpoints": [
            {
                "time": 102.0,
                "question": (
                    "أوووه! النملة عندها فكرة! "
                    "بتشوفها فكرة ذكية؟ وليش؟"
                ),
                "keywords": [
                    "آه",
                    "اه",
                    "نعم",
                    "ايوه",
                    "ذكية",
                    "ذكي",
                    "فكرة حلوة",
                    "فكره حلوه",
                    "نجحت",
                    "شاطر",
                    "شطرة",
                ],
                "correct_response": (
                    "صح! النملة فكرت بطريقة ذكية. يلا نكمل المغامرة!"
                ),
                "other_response": (
                    "حبيت رأيك! يلا نكمل ونشوف إذا فكرتها رح تنجح."
                ),
            }
        ],
    },
}


# =========================================================
# BARGE-IN COMMANDS DURING STORY MP3
# =========================================================

STORY_BARGE_PROFILE = {
    "start_timeout": 8.0,
    "end_silence": 0.45,
    "max_speech": 3.5,
}

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
# STORY MODULE
# =========================================================

class StoryModule:

    def __init__(
        self,
        voice_module=None,
        face_module=None,
    ):

        self.voice = voice_module
        self.face = face_module

        self.started = False

        self.current_story_key = None
        self.current_story = None
        self.current_checkpoint_index = 0
        self.current_position = 0.0

        self.waiting_for_answer = False
        self.active = False

        self.player_process = None
        self.ffmpeg_process = None

        self.stop_requested = False
        self.last_control_command = None

        self._saved_listener_profile = None
        self._saved_listener_values = None

    # =====================================================
    # START MODULE
    # =====================================================

    def start_module(self):

        if self.started:
            return

        print()
        print("=" * 60)
        print("📚 STARTING MP3 STORY MODULE - BARGE IN")
        print("=" * 60)

        for key, story in STORIES.items():

            path = story["audio"]

            print(
                "✅" if path.exists() else "⚠️",
                key,
                story["title"],
                "->",
                path,
            )

        self.started = True

        print(
            f"📚 Stories available: {len(STORIES)}"
        )
        print(
            "✅ Story barge-in ready: وقف / وطي الصوت / علي الصوت"
        )
        print("=" * 60)

    # =====================================================
    # BASIC SETTERS
    # =====================================================

    def set_voice(
        self,
        voice_module,
    ):

        self.voice = voice_module

    def set_face(
        self,
        face_module,
    ):

        self.face = face_module

    # =====================================================
    # FACE
    # =====================================================

    def _set_face(
        self,
        expression,
    ):

        if self.face is None:
            return

        try:

            self.face.set_expression(
                expression
            )

            self.face.update()

        except Exception:

            pass

    # =====================================================
    # NORMALIZE
    # =====================================================

    @staticmethod
    def _normalize(
        text,
    ):

        text = str(
            text or ""
        ).strip().lower()

        text = unicodedata.normalize(
            "NFKC",
            text,
        )

        text = re.sub(
            r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]",
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

    # =====================================================
    # LISTENER PROFILE WHILE STORY IS PLAYING
    # =====================================================

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

    def _enable_story_listening(self):
        """
        Keep the SAME microphone open during story playback.
        No second arecord process is started.
        """

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
                    "story_barge_in",
                    dict(
                        STORY_BARGE_PROFILE
                    ),
                )

        except Exception:

            pass

        try:
            self.voice.enable()
        except Exception:
            pass

    def _restore_listener_profile(self):

        if self.voice is None:
            return

        profile = self._saved_listener_profile
        values = self._saved_listener_values

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

    # =====================================================
    # CONTROL COMMANDS DURING STORY MP3
    # =====================================================

    def _poll_story_control(self):

        if self.voice is None:
            return None

        try:

            text = self.voice.get_command()

        except Exception:

            text = None

        if not text:
            return None

        normalized = self._normalize(
            text
        )

        if normalized in STOP_COMMANDS:

            self.last_control_command = "stop"
            self.stop_requested = True

            print()
            print(
                f"🛑 Story interrupted by child: {text}"
            )

            return "stop"

        if normalized in VOLUME_DOWN_COMMANDS:

            self.last_control_command = "volume_down"

            print()
            print(
                f"🔉 Story command: {text}"
            )

            try:

                lower = getattr(
                    self.voice,
                    "lower_volume",
                    None,
                )

                if callable(lower):
                    lower(step=15)

            except Exception as error:

                print(
                    "⚠️ Could not lower volume:",
                    error,
                )

            return "volume_down"

        if normalized in VOLUME_UP_COMMANDS:

            self.last_control_command = "volume_up"

            print()
            print(
                f"🔊 Story command: {text}"
            )

            try:

                raise_volume = getattr(
                    self.voice,
                    "raise_volume",
                    None,
                )

                if callable(raise_volume):
                    raise_volume(step=15)

            except Exception as error:

                print(
                    "⚠️ Could not raise volume:",
                    error,
                )

            return "volume_up"

        # During MP3 playback, ignore arbitrary text for now.
        # Without AEC, the microphone can hear the story itself.
        return None

    # =====================================================
    # TTS
    # =====================================================

    def _say(
        self,
        text,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:
            return False

        self._set_face(
            "talking"
        )

        print()
        print(
            f"🤖 Mimi Story: {text}"
        )

        if self.voice is None:
            return True

        try:

            result = self.voice.say(
                text,
                resume_listening=True,
            )

            if getattr(
                self.voice,
                "last_barge_command",
                None,
            ) == "stop":

                self.stop_requested = True
                self.last_control_command = "stop"

            return (
                True
                if result is None
                else bool(result)
            )

        except TypeError:

            try:

                self.voice.say(
                    text
                )

                return True

            except Exception as error:

                print(
                    "❌ Story TTS error:",
                    error,
                )

                return False

        except Exception as error:

            print(
                "❌ Story TTS error:",
                error,
            )

            return False

    def _speak_after_mp3(
        self,
        text,
        delay=0.60,
    ):

        self._set_face(
            "talking"
        )

        end = (
            time.monotonic()
            +
            max(
                0.0,
                float(delay),
            )
        )

        while time.monotonic() < end:

            try:

                if self.face is not None:
                    self.face.update()

            except Exception:

                pass

            time.sleep(
                0.03
            )

        ok = self._say(
            text
        )

        # If the child explicitly said "وقف" while Mimi was asking,
        # do NOT retry the sentence.
        if self.stop_requested:
            return False

        if not ok:

            print(
                "⚠️ Story question audio failed. Retrying once..."
            )

            time.sleep(
                0.75
            )

            ok = self._say(
                text
            )

        return ok

    # =====================================================
    # STORY CHOICE
    # =====================================================

    def choose_story_from_text(
        self,
        text,
    ):

        text = str(
            text or ""
        ).lower()

        if any(
            word in text
            for word in (
                "حيوان",
                "حيوانات",
                "أرنب",
                "ارنب",
                "سلحفاة",
                "سلحفاه",
                "animals",
            )
        ):
            return "animals"

        if any(
            word in text
            for word in (
                "مضحكة",
                "مضحك",
                "ضحك",
                "زوزو",
                "funny",
            )
        ):
            return "funny"

        if any(
            word in text
            for word in (
                "تعليمية",
                "تعليمي",
                "تعلم",
                "الكتكوت",
                "كتكوت",
                "كوك",
                "educational",
            )
        ):
            return "educational"

        if any(
            word in text
            for word in (
                "مغامرة",
                "مغامرات",
                "النملة",
                "نملة",
                "قمح",
                "adventure",
            )
        ):
            return "adventure"

        return None

    # =====================================================
    # PLAYER CONTROL
    # =====================================================

    def _stop_player(self):

        for process in (
            self.player_process,
            self.ffmpeg_process,
        ):

            if process is None:
                continue

            try:

                if process.poll() is None:

                    process.terminate()

                    try:
                        process.wait(timeout=0.7)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=0.7)

            except Exception:

                pass

        self.player_process = None
        self.ffmpeg_process = None

    # =====================================================
    # MP3 PLAYBACK WITH LIVE MICROPHONE
    # =====================================================

    def _play_audio_segment(
        self,
        start_seconds,
        end_seconds=None,
    ):

        if self.current_story is None:
            return False

        audio_path = Path(
            self.current_story["audio"]
        )

        if not audio_path.exists():

            print()
            print(
                "❌ Story audio file not found:"
            )
            print(
                audio_path
            )

            return False

        self._stop_player()
        self._set_face(
            "talking"
        )

        self.stop_requested = False
        self.last_control_command = None

        start_seconds = max(
            0.0,
            float(start_seconds),
        )

        duration = None

        if end_seconds is not None:

            duration = max(
                0.05,
                float(end_seconds)
                -
                start_seconds,
            )

        print()
        print(
            f"🔊 Story MP3: {start_seconds:.1f}s -> "
            f"{'END' if end_seconds is None else f'{float(end_seconds):.1f}s'}"
        )
        print(
            "🎤 Microphone stays ON: وقف / وطي الصوت / علي الصوت"
        )

        speaker_device = "plughw:2,0"

        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start_seconds:.3f}",
            "-i",
            str(audio_path),
        ]

        if duration is not None:

            ffmpeg_cmd += [
                "-t",
                f"{duration:.3f}",
            ]

        ffmpeg_cmd += [
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

        aplay_cmd = [
            "aplay",
            "-q",
            "-D",
            speaker_device,
            "-f",
            "S16_LE",
            "-c",
            "2",
            "-r",
            "48000",
        ]

        ffmpeg_process = None
        aplay_process = None

        playback_started = time.monotonic()

        # Keep the existing VoiceListener alive.
        self._enable_story_listening()

        try:

            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            self.ffmpeg_process = ffmpeg_process

            aplay_process = subprocess.Popen(
                aplay_cmd,
                stdin=ffmpeg_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self.player_process = aplay_process

            if ffmpeg_process.stdout is not None:
                ffmpeg_process.stdout.close()

            while aplay_process.poll() is None:

                command = self._poll_story_control()

                if command == "stop":

                    elapsed = max(
                        0.0,
                        time.monotonic()
                        -
                        playback_started,
                    )

                    if duration is not None:
                        elapsed = min(
                            duration,
                            elapsed,
                        )

                    self.current_position = (
                        start_seconds
                        +
                        elapsed
                    )

                    self._stop_player()

                    return False

                try:

                    if self.face is not None:
                        self.face.update()

                except Exception:

                    pass

                time.sleep(
                    0.03
                )

            aplay_rc = aplay_process.returncode

            try:

                ffmpeg_rc = ffmpeg_process.wait(
                    timeout=2.0
                )

            except subprocess.TimeoutExpired:

                ffmpeg_process.kill()

                ffmpeg_rc = ffmpeg_process.wait(
                    timeout=1.0
                )

            self.player_process = None
            self.ffmpeg_process = None

            # Give ALSA a short moment to release before Mimi TTS.
            time.sleep(
                0.60
            )

            if aplay_rc != 0:

                print(
                    f"❌ Story aplay failed with code: {aplay_rc}"
                )

                return False

            if ffmpeg_rc not in (
                0,
                None,
            ):

                print(
                    f"❌ Story ffmpeg failed with code: {ffmpeg_rc}"
                )

                return False

            return True

        except FileNotFoundError as error:

            print(
                "❌ ffmpeg/aplay is not installed:",
                error,
            )

            self.player_process = None
            self.ffmpeg_process = None

            return False

        except Exception as error:

            print(
                "❌ Story playback error:",
                error,
            )

            self.player_process = None
            self.ffmpeg_process = None

            return False

        finally:

            self._restore_listener_profile()

            if aplay_process is not None:

                try:
                    if aplay_process.poll() is None:
                        aplay_process.terminate()
                except Exception:
                    pass

            if ffmpeg_process is not None:

                try:
                    if ffmpeg_process.poll() is None:
                        ffmpeg_process.terminate()
                except Exception:
                    pass

            self.player_process = None
            self.ffmpeg_process = None

    # =====================================================
    # CHECKPOINTS
    # =====================================================

    def _get_current_checkpoint(self):

        if self.current_story is None:
            return None

        checkpoints = self.current_story.get(
            "checkpoints",
            [],
        )

        if (
            self.current_checkpoint_index
            >=
            len(checkpoints)
        ):
            return None

        return checkpoints[
            self.current_checkpoint_index
        ]

    def _story_stopped_result(self):

        title = (
            self.current_story.get(
                "title",
                "القصة",
            )
            if self.current_story
            else "القصة"
        )

        self.waiting_for_answer = False
        self.active = False

        self._set_face(
            "listening"
        )

        print()
        print(
            "🛑 Story stopped by child."
        )

        return {
            "type": "story_stopped",
            "title": title,
            "position": self.current_position,
            "command": "stop",
        }

    def _play_until_next_question(self):

        checkpoint = self._get_current_checkpoint()

        if checkpoint is None:

            self.waiting_for_answer = False

            ok = self._play_audio_segment(
                self.current_position,
                None,
            )

            if self.stop_requested:
                return self._story_stopped_result()

            self.current_position = float(
                self.current_story.get(
                    "duration",
                    self.current_position,
                )
            )

            title = self.current_story.get(
                "title",
                "القصة",
            )

            self.active = False

            print()
            print(
                "✅ Story MP3 finished."
            )

            return {
                "type": "story_finished",
                "title": title,
                "audio_ok": ok,
            }

        checkpoint_time = float(
            checkpoint["time"]
        )

        ok = self._play_audio_segment(
            self.current_position,
            checkpoint_time,
        )

        if self.stop_requested:
            return self._story_stopped_result()

        self.current_position = checkpoint_time

        if not ok:

            self.active = False
            self.waiting_for_answer = False

            return {
                "type": "story_error",
                "message": "ما قدرت أشغل صوت القصة.",
            }

        question = str(
            checkpoint.get(
                "question",
                "",
            )
        ).strip()

        question_audio_ok = self._speak_after_mp3(
            question,
            delay=0.60,
        )

        if self.stop_requested:
            return self._story_stopped_result()

        self.waiting_for_answer = True

        self._set_face(
            "listening"
        )

        print()
        print(
            "🎤 Story question finished. Waiting for child answer..."
        )

        return {
            "type": "story_question",
            "question": question,
            "question_audio_ok": question_audio_ok,
            "checkpoint_index": self.current_checkpoint_index,
        }

    # =====================================================
    # START STORY
    # =====================================================

    def start(
        self,
        request_text="",
    ):

        if not self.started:
            self.start_module()

        if self.active:

            print(
                "📚 Story already active."
            )

            return False

        key = (
            self.choose_story_from_text(
                request_text
            )
            or
            "animals"
        )

        story = STORIES.get(
            key
        )

        if story is None:

            self._say(
                "آسفة، ما قدرت ألاقي القصة."
            )

            return False

        self.current_story_key = key
        self.current_story = story
        self.current_checkpoint_index = 0
        self.current_position = 0.0

        self.waiting_for_answer = False
        self.active = True
        self.stop_requested = False
        self.last_control_command = None

        print()
        print("=" * 60)
        print(
            f"📖 STORY: {story['title']}"
        )
        print("=" * 60)

        return self._play_until_next_question()

    # =====================================================
    # ANSWER
    # =====================================================

    def _answer_matches(
        self,
        answer,
        checkpoint,
    ):

        answer = self._normalize(
            answer
        )

        return any(
            self._normalize(keyword)
            and
            self._normalize(keyword)
            in
            answer
            for keyword in checkpoint.get(
                "keywords",
                [],
            )
        )

    def answer(
        self,
        child_answer,
    ):

        if not self.active:

            return {
                "type": "no_story",
                "message": "ما في قصة شغالة حاليًا.",
            }

        if not self.waiting_for_answer:

            return {
                "type": "not_waiting",
                "message": "ميمي مش مستنية جواب حاليًا.",
            }

        checkpoint = self._get_current_checkpoint()

        if checkpoint is None:

            return {
                "type": "not_waiting",
                "message": "ما في سؤال حاليًا.",
            }

        child_answer = str(
            child_answer or ""
        ).strip()

        if not child_answer:
            return False

        print()
        print(
            f"👧 Story answer: {child_answer}"
        )

        self.waiting_for_answer = False

        matched = self._answer_matches(
            child_answer,
            checkpoint,
        )

        reaction = checkpoint.get(
            (
                "correct_response"
                if matched
                else "other_response"
            ),
            "حلو! يلا نكمل.",
        )

        self._say(
            reaction
        )

        if self.stop_requested:
            return self._story_stopped_result()

        self.current_checkpoint_index += 1

        time.sleep(
            0.45
        )

        result = self._play_until_next_question()

        if isinstance(
            result,
            dict,
        ):

            result.setdefault(
                "correct",
                matched,
            )

            result.setdefault(
                "reaction",
                reaction,
            )

        return result

    # =====================================================
    # STATE
    # =====================================================

    def is_active(self):

        return bool(
            self.active
        )

    def is_waiting_for_answer(self):

        return bool(
            self.active
            and
            self.waiting_for_answer
        )

    def get_state(self):

        return {
            "active": self.active,
            "story_key": self.current_story_key,
            "title": (
                self.current_story.get(
                    "title"
                )
                if self.current_story
                else None
            ),
            "position": self.current_position,
            "checkpoint_index": self.current_checkpoint_index,
            "waiting_for_answer": self.waiting_for_answer,
            "stop_requested": self.stop_requested,
            "last_control_command": self.last_control_command,
        }

    # =====================================================
    # RESET / CLOSE
    # =====================================================

    def reset(self):

        self._stop_player()

        self.current_story_key = None
        self.current_story = None
        self.current_checkpoint_index = 0
        self.current_position = 0.0

        self.waiting_for_answer = False
        self.active = False

        self.stop_requested = False
        self.last_control_command = None

        print(
            "📚 Story session reset."
        )

    def close(self):

        self.reset()
        self.started = False

        print(
            "✅ Story Module closed."
        )

    def list_stories(self):

        return [
            {
                "story_id": key,
                "title": value["title"],
                "audio": str(
                    value["audio"]
                ),
            }
            for key, value in STORIES.items()
        ]
