import json
import os
import random
import re
import subprocess
import time
import unicodedata
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LEARNING_FILE = (
    PROJECT_ROOT
    / "data"
    / "learning"
    / "learning.json"
)

LEARNING_AUDIO_DIR = (
    PROJECT_ROOT
    / "data"
    / "learning"
    / "audio"
)

LEARNING_AUDIO = {
    "colors": LEARNING_AUDIO_DIR / "colors_lesson.mp3",
    "numbers": LEARNING_AUDIO_DIR / "numbers_lesson.mp3",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_arabic(text):

    if text is None:
        return ""

    text = str(text).strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    for char in (
        "أ",
        "إ",
        "آ",
        "ٱ",
    ):
        text = text.replace(
            char,
            "ا",
        )

    text = text.replace(
        "ى",
        "ي",
    )

    text = text.replace(
        "ـ",
        "",
    )

    text = re.sub(
        r"[^\u0600-\u06FF0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# LEARNING MODULE
# =========================================================

# =========================================================
# LEARNING BARGE-IN
# =========================================================

LEARNING_BARGE_PROFILE = {
    "start_timeout": 8.0,
    "end_silence": 0.45,
    "max_speech": 3.5,
}

# يبدأ درس الـMP3 على صوت أهدأ، وبعدها الطفل يقدر يقول
# "علي الصوت" أو "وطي الصوت".
LEARNING_START_VOLUME = 65

LEARNING_STOP_COMMANDS = {
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
}

LEARNING_VOLUME_DOWN_COMMANDS = {
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

LEARNING_VOLUME_UP_COMMANDS = {
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


class LearningModule:

    def __init__(
        self,
        voice_module=None,
        face_module=None,
    ):

        self.voice = voice_module
        self.face = face_module

        self.started = False

        self.data = {}

        # -------------------------------------------------
        # Activity State
        # -------------------------------------------------

        self.active = False

        self.topic = None

        self.waiting_for_topic = False

        self.waiting_for_answer = False

        self.current_question = None

        self.current_question_index = None

        self.attempts = 0

        self.score = 0

        self.questions_answered = 0

        self.used_questions = set()

        # السؤال الجاهز الذي يجب على MimiBot نطقه قبل فتح المايك.
        self.pending_prompt = ""

        # -------------------------------------------------
        # Live lesson playback controls
        # -------------------------------------------------

        self.learning_stop_requested = False
        self.last_control_command = None

        self.ffmpeg_process = None
        self.aplay_process = None

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
        print("🎓 STARTING LEARNING MODULE")
        print("=" * 60)

        if not LEARNING_FILE.exists():

            raise FileNotFoundError(
                f"Learning data not found: "
                f"{LEARNING_FILE}"
            )

        with open(
            LEARNING_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            self.data = (
                json.load(file)
            )

        self.started = True

        print(
            f"📚 Topics: "
            f"{len(self.data)}"
        )

        for key, value in self.data.items():

            print(
                f"  - {key}: "
                f"{len(value.get('questions', []))} questions"
            )

        print(
            "✅ Learning Module ready."
        )

        print("=" * 60)

    # =====================================================
    # SET VOICE
    # =====================================================

    def set_voice(
        self,
        voice_module,
    ):

        self.voice = voice_module

    def set_face_module(
        self,
        face_module,
    ):

        self.face = face_module

    # =====================================================
    # FACE
    # =====================================================

    def set_face(
        self,
        expression,
    ):

        if self.face is None:
            return False

        try:
            self.face.set_expression(
                expression
            )
            self.face.update()
            return True

        except Exception as error:

            print(
                "⚠️ Learning face error:",
                error,
            )

            return False

    def hold_face(
        self,
        expression,
        seconds,
    ):

        self.set_face(
            expression
        )

        if self.face is None:

            time.sleep(
                seconds
            )

            return

        end_time = (
            time.monotonic()
            +
            float(seconds)
        )

        while (
            time.monotonic()
            <
            end_time
        ):

            try:
                self.face.update()
            except Exception:
                pass

            time.sleep(
                0.03
            )

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

        self.set_face(
            "talking"
        )

        result = True

        if self.voice is not None:

            try:

                voice_result = self.voice.say(
                    text,
                    resume_listening=
                        resume_listening,
                )

                result = (
                    True
                    if voice_result is None
                    else bool(voice_result)
                )

            except TypeError:

                voice_result = self.voice.say(
                    text
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

                self.learning_stop_requested = True
                self.last_control_command = "stop"

        else:

            print(
                f"🤖 Mimi: {text}"
            )

        if (
            resume_listening
            and
            not self.learning_stop_requested
        ):

            self.set_face(
                "listening"
            )

        return result


    # =====================================================
    # PENDING QUESTION PROMPT
    # =====================================================

    def set_pending_prompt(
        self,
        text,
    ):
        """
        نخزن السؤال فقط هنا.
        MimiBot هو المسؤول عن نطقه كاملًا،
        وبعد انتهاء الصوت فقط يفتح المايك.
        """

        self.pending_prompt = str(
            text or ""
        ).strip()

        return bool(
            self.pending_prompt
        )

    def pop_pending_prompt(self):
        """
        يرجع السؤال المجهز مرة واحدة ثم يمسحه.
        """

        text = str(
            self.pending_prompt or ""
        ).strip()

        self.pending_prompt = ""

        return text


    # =====================================================
    # LESSON AUDIO
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

    def _enable_lesson_barge_in(self):
        """
        يبقي نفس المايك مفتوحًا أثناء درس الـMP3.
        لا نفتح arecord ثاني.
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
                    "learning_barge_in",
                    dict(
                        LEARNING_BARGE_PROFILE
                    ),
                )

        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception as error:
            print(
                "⚠️ Learning microphone enable error:",
                error,
            )

    def _restore_listener_profile(self):

        if self.voice is None:
            return

        if self._saved_listener_profile:

            try:

                setter = getattr(
                    self.voice,
                    "set_listening_profile",
                    None,
                )

                if callable(setter):

                    setter(
                        self._saved_listener_profile,
                        self._saved_listener_values or {},
                    )

            except Exception:
                pass

        self._saved_listener_profile = None
        self._saved_listener_values = None

    def _poll_lesson_control(self):

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

        if normalized in LEARNING_STOP_COMMANDS:

            self.learning_stop_requested = True
            self.last_control_command = "stop"

            print()
            print(
                f"🛑 Learning command: {text}"
            )

            return "stop"

        if normalized in LEARNING_VOLUME_DOWN_COMMANDS:

            self.last_control_command = "volume_down"

            print()
            print(
                f"🔉 Learning command: {text}"
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
                    "⚠️ Could not lower learning volume:",
                    error,
                )

            return None

        if normalized in LEARNING_VOLUME_UP_COMMANDS:

            self.last_control_command = "volume_up"

            print()
            print(
                f"🔊 Learning command: {text}"
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
                    "⚠️ Could not raise learning volume:",
                    error,
                )

            return None

        # أثناء الدرس نتجاهل الكلام العادي مؤقتًا.
        # بدون AEC السماعة قد تُسمَع على المايك.
        return None

    def _stop_lesson_player(self):

        stopped = False

        for process in (
            self.aplay_process,
            self.ffmpeg_process,
        ):

            if process is None:
                continue

            try:

                if process.poll() is None:

                    process.terminate()
                    stopped = True

                    try:
                        process.wait(
                            timeout=0.6
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(
                            timeout=0.6
                        )

            except Exception:
                pass

        self.aplay_process = None
        self.ffmpeg_process = None

        return stopped

    def play_lesson_audio(
        self,
        topic,
    ):

        audio_file = LEARNING_AUDIO.get(
            topic
        )

        if audio_file is None:
            return False

        audio_file = Path(
            audio_file
        )

        if not audio_file.exists():

            print()
            print(
                f"⚠️ Learning audio missing: {audio_file}"
            )

            return False

        self.learning_stop_requested = False
        self.last_control_command = None

        # Start the lesson at a comfortable volume.
        # If the current volume is already lower, leave it as-is.
        if self.voice is not None:

            try:

                current_volume = self.voice.get_volume()

                if (
                    current_volume is not None
                    and
                    int(current_volume)
                    >
                    LEARNING_START_VOLUME
                ):

                    lower = getattr(
                        self.voice,
                        "lower_volume",
                        None,
                    )

                    if callable(lower):

                        lower(
                            step=
                                int(current_volume)
                                -
                                LEARNING_START_VOLUME
                        )

            except Exception as error:

                print(
                    "⚠️ Could not set learning start volume:",
                    error,
                )

        self._enable_lesson_barge_in()

        print()
        print(
            f"🎧 Playing learning lesson: {audio_file.name}"
        )
        print(
            "🎤 Microphone stays ON: "
            "وقف / وطي الصوت / علي الصوت"
        )

        self.set_face(
            "talking"
        )

        # MP3 -> ffmpeg -> PCM -> aplay.
        speaker_device = "plughw:2,0"

        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
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

            self.aplay_process = aplay_process

            if ffmpeg_process.stdout is not None:
                ffmpeg_process.stdout.close()

            while aplay_process.poll() is None:

                command = self._poll_lesson_control()

                if command == "stop":

                    self._stop_lesson_player()

                    print()
                    print(
                        "🛑 Learning lesson stopped by child."
                    )

                    return False

                if self.face is not None:
                    try:
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

            self.aplay_process = None
            self.ffmpeg_process = None

            # Small ALSA handoff delay before Mimi TTS.
            time.sleep(
                0.60
            )

            if aplay_rc != 0:

                print(
                    f"⚠️ Learning aplay exited with code "
                    f"{aplay_rc}"
                )

                return False

            if ffmpeg_rc not in (
                0,
                None,
            ):

                print(
                    f"⚠️ Learning ffmpeg exited with code "
                    f"{ffmpeg_rc}"
                )

                return False

            print(
                "✅ Learning lesson finished."
            )

            return True

        except FileNotFoundError as error:

            print(
                "❌ ffmpeg/aplay not found:",
                error,
            )

            return False

        except Exception as error:

            print(
                "❌ Learning audio error:",
                error,
            )

            return False

        finally:

            self._stop_lesson_player()
            self._restore_listener_profile()


    # =====================================================
    # DETECT TOPIC
    # =====================================================

    def detect_topic(
        self,
        text,
    ):

        text = normalize_arabic(
            text
        )

        # -------------------------------------------------
        # Numbers
        # -------------------------------------------------

        if any(
            word in text
            for word in (
                "ارقام",
                "الارقام",
                "عد",
                "العد",
                "رقم",
            )
        ):

            return "numbers"

        # -------------------------------------------------
        # Colors
        # -------------------------------------------------

        if any(
            word in text
            for word in (
                "الوان",
                "الالوان",
                "لون",
            )
        ):

            return "colors"

        # -------------------------------------------------
        # Addition
        # -------------------------------------------------

        if any(
            word in text
            for word in (
                "جمع",
                "الجمع",
                "زائد",
                "رياضيات",
                "حساب",
            )
        ):

            return "addition"

        # -------------------------------------------------
        # Letters
        # -------------------------------------------------

        if any(
            word in text
            for word in (
                "حروف",
                "الحروف",
                "حرف",
                "ابجدية",
            )
        ):

            return "letters"

        return None

    # =====================================================
    # START ACTIVITY
    # =====================================================

    def start(
        self,
        request_text="",
    ):

        if not self.started:

            self.start_module()

        self.reset()

        self.learning_stop_requested = False
        self.last_control_command = None

        self.active = True

        topic = (
            self.detect_topic(
                request_text
            )
        )

        # -------------------------------------------------
        # Need Topic
        # -------------------------------------------------

        if topic is None:

            self.waiting_for_topic = True

            self.say(
                "أكيد. "
                "شو بتحب نتعلم؟ "
                "الأرقام، "
                "الألوان، "
                "الحروف، "
                "ولا الجمع؟"
            )

            return {
                "started": True,
                "needs_topic": True,
            }

        return (
            self.start_topic(
                topic
            )
        )

    # =====================================================
    # START TOPIC
    # =====================================================

    def start_topic(
        self,
        topic,
    ):

        if topic not in self.data:

            self.say(
                "هذا النشاط مش موجود "
                "عندي حاليًا."
            )

            return {
                "started": False,
                "error":
                    "topic_not_found",
            }

        self.active = True

        self.topic = topic

        self.waiting_for_topic = False

        self.waiting_for_answer = False

        self.current_question = None

        self.current_question_index = None

        self.attempts = 0

        self.score = 0

        self.questions_answered = 0

        self.used_questions.clear()

        title = (
            self.data[
                topic
            ].get(
                "title",
                "التعلم",
            )
        )

        print()
        print("=" * 60)

        print(
            f"🎓 LEARNING: "
            f"{title}"
        )

        print("=" * 60)

        self.say(
            f"ممتاز. "
            f"خلينا نتعلم "
            f"{title} سوا.",
            resume_listening=False,
        )

        if self.learning_stop_requested:

            self.active = False
            self.waiting_for_topic = False
            self.waiting_for_answer = False

            return {
                "started": False,
                "stopped": True,
                "topic":
                    topic,
            }

        # للألوان والأرقام نشغّل درس MP3 أولًا.
        # أثناء الـMP3 يبقى المايك مغلقًا، وبعد انتهاء
        # الدرس ask_question تفتح الاستماع من خلال VoiceModule.
        if topic in (
            "colors",
            "numbers",
        ):

            lesson_ok = (
                self.play_lesson_audio(
                    topic
                )
            )

            if lesson_ok:

                self.ask_question(
                    prefix=
                        "خلصنا الدرس. يلا نبدأ بأول سؤال. "
                )

            elif self.learning_stop_requested:

                self.active = False
                self.waiting_for_topic = False
                self.waiting_for_answer = False

                return {
                    "started": False,
                    "stopped": True,
                    "topic":
                        topic,
                }

            else:

                self.ask_question()

        else:

            self.ask_question()

        return {
            "started": True,
            "topic":
                topic,
            "title":
                title,
        }

    # =====================================================
    # GET QUESTIONS
    # =====================================================

    def get_questions(self):

        if self.topic is None:

            return []

        return (
            self.data.get(
                self.topic,
                {}
            ).get(
                "questions",
                []
            )
        )

    # =====================================================
    # ASK QUESTION
    # =====================================================

    def ask_question(
        self,
        prefix="",
    ):

        questions = (
            self.get_questions()
        )

        if not questions:

            self.say(
                "ما في أسئلة بهذا النشاط."
            )

            self.reset()

            return False

        # -------------------------------------------------
        # Finished all questions
        # -------------------------------------------------

        if (
            len(self.used_questions)
            >= len(questions)
        ):

            self.finish()

            return False

        available_indexes = [
            index
            for index in range(
                len(questions)
            )
            if index
            not in self.used_questions
        ]

        question_index = (
            random.choice(
                available_indexes
            )
        )

        self.used_questions.add(
            question_index
        )

        self.current_question_index = (
            question_index
        )

        self.current_question = (
            questions[
                question_index
            ]
        )

        self.attempts = 0

        self.waiting_for_answer = True

        question_text = (
            self.current_question.get(
                "question",
                ""
            )
        )

        print()
        print("=" * 60)

        print(
            f"❓ Learning question "
            f"{self.questions_answered + 1}"
        )

        print(
            question_text
        )

        print("=" * 60)

        spoken_text = (
            f"{prefix}{question_text}"
        ).strip()

        # مهم:
        # لا ننطق السؤال ولا نفتح المايك من داخل LearningModule.
        # نخزنه، وMimiBot ينطقه كاملًا ثم يفتح الاستماع.
        self.set_pending_prompt(
            spoken_text
        )

        return True

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    def check_answer(
        self,
        child_text,
    ):

        if (
            not self.active
            or
            not self.waiting_for_answer
            or
            self.current_question is None
        ):

            return {
                "handled": False,
            }

        self.waiting_for_answer = False

        self.attempts += 1

        child_normalized = (
            normalize_arabic(
                child_text
            )
        )

        accepted_answers = (
            self.current_question.get(
                "answers",
                []
            )
        )

        normalized_answers = [
            normalize_arabic(
                answer
            )
            for answer
            in accepted_answers
        ]

        print()
        print("=" * 60)

        print(
            f"🎤 Child answer: "
            f"{child_text}"
        )

        print(
            f"✅ Accepted: "
            f"{accepted_answers}"
        )

        # =================================================
        # CORRECT
        # =================================================

        if (
            child_normalized
            in normalized_answers
        ):

            self.score += 1

            self.questions_answered += 1

            success_message = (
                self.current_question.get(
                    "success",
                    "ممتاز، إجابتك صحيحة.",
                )
            )

            print(
                "✅ CORRECT"
            )

            print("=" * 60)

            # ---------------------------------------------
            # Next question
            # ---------------------------------------------
            # لا نحكي من داخل LearningModule حتى لا تتجمد
            # حركة الفم. نجهز الرد + السؤال معًا وMimiBot
            # ينطقهم وهو يحدث الوجه باستمرار.

            self.ask_question(
                prefix=
                    f"{success_message} "
            )

            return {
                "handled": True,
                "correct": True,
                "score":
                    self.score,
                "answered":
                    self.questions_answered,
            }

        # =================================================
        # WRONG - FIRST ATTEMPT
        # =================================================

        if self.attempts < 2:

            print(
                "❌ WRONG - TRY AGAIN"
            )

            print("=" * 60)

            self.set_pending_prompt(
                "قريبة، جرب مرة ثانية."
            )

            self.waiting_for_answer = True

            return {
                "handled": True,
                "correct": False,
                "retry": True,
            }

        # =================================================
        # WRONG - SECOND ATTEMPT
        # =================================================

        correct_answer = (
            accepted_answers[0]
            if accepted_answers
            else ""
        )

        print(
            "❌ WRONG - ANSWER SHOWN"
        )

        print(
            f"Correct answer: "
            f"{correct_answer}"
        )

        print("=" * 60)

        self.questions_answered += 1

        self.ask_question(
            prefix=(
                f"الإجابة الصحيحة هي "
                f"{correct_answer}. "
                "خلينا نجرب سؤال ثاني. "
            )
        )

        return {
            "handled": True,
            "correct": False,
            "retry": False,
            "correct_answer":
                correct_answer,
            "score":
                self.score,
            "answered":
                self.questions_answered,
        }

    # =====================================================
    # HANDLE INPUT
    # =====================================================

    def handle_input(
        self,
        text,
    ):

        # -------------------------------------------------
        # Waiting For Topic
        # -------------------------------------------------

        if self.waiting_for_topic:

            topic = (
                self.detect_topic(
                    text
                )
            )

            if topic is None:

                self.say(
                    "ما عرفت شو بدك نتعلم. "
                    "احكي الأرقام، "
                    "الألوان، "
                    "الحروف، "
                    "أو الجمع."
                )

                return {
                    "handled": True,
                    "needs_topic": True,
                }

            return (
                self.start_topic(
                    topic
                )
            )

        # -------------------------------------------------
        # Waiting For Answer
        # -------------------------------------------------

        if self.waiting_for_answer:

            return (
                self.check_answer(
                    text
                )
            )

        return {
            "handled": False,
        }

    # =====================================================
    # FINISH
    # =====================================================

    def finish(self):

        topic_title = ""

        if self.topic:

            topic_title = (
                self.data.get(
                    self.topic,
                    {}
                ).get(
                    "title",
                    ""
                )
            )

        total = (
            self.questions_answered
        )

        score = (
            self.score
        )

        print()
        print("=" * 60)
        print("🏆 LEARNING ACTIVITY FINISHED")
        print("=" * 60)

        print(
            f"Topic: "
            f"{topic_title}"
        )

        print(
            f"Score: "
            f"{score}/{total}"
        )

        print("=" * 60)

        self.hold_face(
            "proud",
            1.80,
        )

        self.say(
            f"ممتاز! خلصنا "
            f"{topic_title}. "
            f"جاوبت صح على "
            f"{score} "
            f"من أصل "
            f"{total}. "
            "شو بدك نعمل الآن؟",
            resume_listening=True,
        )

        result = {
            "completed": True,
            "topic":
                self.topic,
            "score":
                score,
            "total":
                total,
        }

        self.reset()

        return result

    # =====================================================
    # STATE
    # =====================================================

    def is_active(self):

        return (
            self.active
        )

    def is_waiting_for_topic(self):

        return (
            self.waiting_for_topic
        )

    def is_waiting_for_answer(self):

        return (
            self.waiting_for_answer
        )

    def get_state(self):

        return {
            "active":
                self.active,

            "topic":
                self.topic,

            "waiting_for_topic":
                self.waiting_for_topic,

            "waiting_for_answer":
                self.waiting_for_answer,

            "score":
                self.score,

            "questions_answered":
                self.questions_answered,

            "pending_prompt":
                self.pending_prompt,

            "learning_stop_requested":
                self.learning_stop_requested,

            "last_control_command":
                self.last_control_command,
        }

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self._stop_lesson_player()

        self.active = False

        self.topic = None

        self.waiting_for_topic = False

        self.waiting_for_answer = False

        self.current_question = None

        self.current_question_index = None

        self.attempts = 0

        self.score = 0

        self.questions_answered = 0

        self.used_questions.clear()

        self.pending_prompt = ""

        self.learning_stop_requested = False
        self.last_control_command = None

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.reset()

        self.started = False

        print(
            "✅ Learning Module closed."
        )


# =========================================================
# STANDALONE TEST
# =========================================================

def test_learning():

    from src.modules.voice_module import (
        VoiceModule
    )

    voice = VoiceModule()

    learning = None

    try:

        voice.start(
            listening=False
        )

        learning = (
            LearningModule(
                voice_module=voice
            )
        )

        learning.start_module()

        learning.start(
            "ميمي بدي نتعلم الألوان"
        )

        while learning.is_active():

            if (
                learning.is_waiting_for_topic()
                or
                learning.is_waiting_for_answer()
            ):

                print()
                print(
                    "🎤 Listening..."
                )

                text = (
                    voice.wait_for_command(
                        timeout=30
                    )
                )

                if not text:

                    print(
                        "⚠️ No response."
                    )

                    break

                print(
                    f"🎤 Heard: "
                    f"{text}"
                )

                learning.handle_input(
                    text
                )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Learning test stopped."
        )

    finally:

        if learning is not None:

            learning.close()

        voice.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    test_learning()