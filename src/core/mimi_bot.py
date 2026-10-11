import time
import threading
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.behavior.response_manager import ResponseManager

from src.core.child_session import (
    create_child_session,
    show_session,
    get_session_gender,
)

from src.database.activity_history import (
    complete_activity,
    start_activity,
)

from src.database.mongodb import (
    close_connection,
)

from src.database.rewards import (
    add_points,
    get_points,
)

from src.dialogue.hybrid_dialogue_manager import (
    HybridDialogueManager,
)

from src.modules.achievement_module import (
    AchievementModule,
)

from src.modules.adhkar_module import (
    AdhkarModule,
)

from src.modules.learning_module import (
    LearningModule,
)

from src.modules.quran_module import (
    QuranModule,
)

from src.modules.riddle_module import (
    RiddleModule,
)

from src.modules.safety_module import (
    SafetyModule,
)

from src.modules.story_module import (
    StoryModule,
)

from src.modules.task_module import (
    TaskModule,
)

from src.modules.vision_module import (
    VisionModule,
)

from src.modules.voice_module import (
    VoiceModule,
)

from src.ui.mimi_face import (
    MimiFace,
)

try:
    from src.voice import listener as voice_listener
except Exception:
    voice_listener = None


# =========================================================
# SETTINGS
# =========================================================

UNKNOWN_REQUIRED_COUNT = 2

PRESENCE_LOST_SECONDS = 15.0

# مدة قصيرة لظهور وجه التفكير بعد انتهاء الاستماع.
THINKING_MIN_SECONDS = 0.80

# Listening profiles: short activities stay responsive; Quran adapts
# to the length of the ayah. The listener module applies these values.
LISTENING_PROFILES = {
    "short": {
        "start_timeout": 6.0,
        "end_silence": 0.80,
        "max_speech": 10.0,
    },
    "story_answer": {
        "start_timeout": 7.0,
        "end_silence": 0.90,
        "max_speech": 12.0,
    },
    # Adhkar: child replies/short recitations should stay responsive.
    "adhkar_short": {
        "start_timeout": 6.0,
        "end_silence": 0.80,
        "max_speech": 10.0,
    },
    "quran_short": {
        "start_timeout": 8.0,
        "end_silence": 1.20,
        "max_speech": 16.0,
    },
    "quran_medium": {
        "start_timeout": 10.0,
        "end_silence": 1.35,
        "max_speech": 28.0,
    },
    "quran_long": {
        "start_timeout": 12.0,
        "end_silence": 1.60,
        "max_speech": 50.0,
    },
}


# =========================================================
# MIMI BOT INTERACTION V3
# =========================================================


class MimiBot:

    def __init__(self):

        # =================================================
        # HARDWARE
        # =================================================

        self.vision = VisionModule()

        self.voice = VoiceModule()

        # شاشة وجه Mimi.
        # الكاميرا تبقى تعمل بالخلفية للتعرّف فقط.
        self.face = MimiFace(
            fullscreen=True
        )

        # =================================================
        # BRAIN
        # =================================================

        self.dialogue = HybridDialogueManager()

        # =================================================
        # PERSONALITY / RESPONSES
        # =================================================

        self.responses = ResponseManager()

        # آخر جملة صوتية قالتها Mimi.
        #
        # تستخدم مع:
        #   عيدي
        #   شو قلتي؟
        #   ما فهمت
        self.last_response_text = ""

        # =================================================
        # ACTIVITIES
        # =================================================

        self.stories = StoryModule(
            voice_module=self.voice
        )

        self.riddles = RiddleModule(
            voice_module=self.voice
        )

        self.quran = QuranModule(
            voice_module=self.voice,
            child_id=None,
            reader="alafasy",
            repeat_target=3,
            pass_threshold=85.0,
        )

        self.adhkar = AdhkarModule(
            voice_module=self.voice,
            face_module=self.face,
        )

        self.learning = LearningModule(
            voice_module=self.voice,
            face_module=self.face,
        )

        self.tasks = TaskModule(
            voice_module=self.voice
        )

        self.achievements = AchievementModule(
            voice_module=self.voice
        )

        self.safety = SafetyModule(
            voice_module=self.voice
        )

        # -------------------------------------------------
        # Safety integration
        # -------------------------------------------------
        self._safety_result_lock = threading.Lock()
        self._pending_safety_results = []
        self._last_processed_safety_event_id = None

        try:
            self.safety.set_alert_callback(
                self._on_safety_alert
            )
        except Exception:
            pass

        # =================================================
        # CURRENT PERSON
        # =================================================

        self.current_face_id = None

        self.current_session = None

        self.guest_mode = False

        self.unknown_count = 0

        self.last_face_seen_time = 0.0

        self.last_processed_recognition_time = 0.0

        # هل الشخص موجود أمام الكاميرا الآن؟
        # نحافظ على الجلسة حتى لو ابتعد مؤقتًا،
        # حتى لا نعيد الترحيب كل مرة يرجع فيها.
        self.person_present = False

        # =================================================
        # POINTS
        # =================================================

        self.current_total_points = 0

        # =================================================
        # NLU DISPLAY
        # =================================================

        self.last_intent = ""

        self.last_confidence = 0.0

        self.last_nlu_source = ""

        # =================================================
        # ACTIVITY HISTORY
        # =================================================

        self.active_activity_id = None

        self.active_activity_type = None

        # =================================================
        # STORY TYPE FOLLOW-UP
        # =================================================
        # إذا الطفل قال فقط "بدي قصة"، نسأله عن النوع وننتظر جوابه.
        self.waiting_for_story_type = False

        # =================================================
        # ADHKAR DAILY REMINDERS
        # =================================================

        # أوقات التذكير التلقائي.
        # الصباح: 06:00 - 11:59
        # المساء: 16:00 - 20:59
        # النوم: 21:00 - 01:59
        self.morning_adhkar_start_hour = 6
        self.morning_adhkar_end_hour = 11
        self.evening_adhkar_start_hour = 16
        self.evening_adhkar_end_hour = 20
        self.sleep_adhkar_start_hour = 21
        self.sleep_adhkar_end_hour = 2

        # هل Mimi تنتظر جواب الطفل على سؤال الأذكار؟
        # القيم: None / "morning" / "evening" / "sleep"
        self.waiting_for_adhkar_confirmation = None

        # منع تكرار نفس التذكير بلا داعٍ.
        self.adhkar_reminder_date = None
        self.morning_adhkar_reminded_today = False
        self.evening_adhkar_reminded_today = False
        self.sleep_adhkar_reminded_today = False

        # إذا قال الطفل "لا" أو "بعدين" نرجع بعد ساعة.
        self.adhkar_postponed_mode = None
        self.adhkar_postponed_until = None
        self.adhkar_postpone_seconds = 60 * 60
        self.adhkar_followup_used = False

        # نحفظ حالة التذكير على القرص، حتى لو سكّرنا Mimi
        # وفتحناها مرة ثانية ما تعيد نفس السؤال.
        self.adhkar_state_file = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "adhkar"
            / "reminder_state.json"
        )

        # لا نحتاج نفحص الساعة في كل frame.
        self.last_adhkar_clock_check = 0.0
        self.adhkar_clock_check_interval = 1.0

        # =================================================
        # APPLICATION
        # =================================================

        self.running = False

        # Current listener profile.
        self.current_listening_profile = "short"

        # Used by say(): audio runs in a worker while the main Pygame
        # thread keeps rendering the animated face.
        self._speech_result = None
        self._speech_error = None

    # =====================================================
    # FACE UI
    # =====================================================

    def set_face(
        self,
        expression,
        render=True,
    ):

        try:

            self.face.set_expression(
                expression
            )

            if render:

                self.face.update()

            return True

        except Exception as error:

            print(
                "⚠️ Mimi face error:",
                error,
            )

            return False

    def get_resting_face(self):

        try:

            if self.safety.is_active():

                return "alert"

        except Exception:

            pass

        if (
            self.current_session
            or
            self.guest_mode
        ):

            return "listening"

        return "idle"

    # =====================================================
    # INTERACTION POLISH HELPERS
    # =====================================================

    def show_thinking_briefly(self, seconds=THINKING_MIN_SECONDS):
        """Show thinking long enough to be visible before Mimi reacts."""
        self.set_face("thinking")
        try:
            delay = max(0.0, float(seconds))
        except Exception:
            delay = THINKING_MIN_SECONDS
        if delay > 0:
            time.sleep(delay)

    def pause_listener_for_content(self):
        """
        Keep the SAME microphone stream alive during long content.

        Story/Quran/Learning/Adhkar own their live barge-in control and
        need the listener enabled for: وقف / وطي الصوت / علي الصوت.
        """

        try:
            self.voice.clear_commands()
        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception:
            pass

        return True

    def restore_listener_after_content(self):
        """Return Mimi to listening when it is the child's turn again."""
        try:
            self.voice.clear_commands()
        except Exception:
            pass
        if self.current_session is not None or self.guest_mode:
            try:
                self.voice.enable()
            except Exception:
                pass
            self.set_face("listening")
        else:
            self.set_face("idle")

    # =====================================================
    # CHILD GENDER / PERSONALITY
    # =====================================================

    def get_current_gender(self):
        try:
            return get_session_gender(
                self.current_session
            )
        except Exception:
            return "unknown"

    def child_word(
        self,
        boy_word,
        girl_word,
        neutral_word=None,
    ):
        gender = self.get_current_gender()

        if gender == "girl":
            return girl_word

        if gender == "boy":
            return boy_word

        if neutral_word is not None:
            return neutral_word

        return boy_word

    # =====================================================
    # LISTENING PROFILE
    # =====================================================

    def set_listening_profile(self, profile):
        if profile not in LISTENING_PROFILES:
            profile = "short"

        self.current_listening_profile = profile

        try:
            if voice_listener is not None:
                voice_listener.set_listening_profile(
                    profile,
                    LISTENING_PROFILES[profile],
                )
        except Exception as error:
            print(
                "⚠️ Could not update listening profile:",
                error,
            )

    def get_quran_listening_profile(self):
        """Choose listening time from the current ayah text when available."""
        try:
            state = self.quran.get_state() or {}
        except Exception:
            state = {}

        candidates = [
            state.get("ayah_text"),
            state.get("current_ayah_text"),
            state.get("text"),
        ]

        for value in candidates:
            if isinstance(value, str) and value.strip():
                words = len(value.split())
                if words <= 8:
                    return "quran_short"
                if words <= 18:
                    return "quran_medium"
                return "quran_long"

        # Some QuranModule versions expose the current ayah as an object.
        try:
            ayah = getattr(self.quran, "current_ayah", None)
            if isinstance(ayah, dict):
                value = ayah.get("text") or ayah.get("ayah_text")
                if isinstance(value, str) and value.strip():
                    words = len(value.split())
                    if words <= 8:
                        return "quran_short"
                    if words <= 18:
                        return "quran_medium"
                    return "quran_long"
        except Exception:
            pass

        return "quran_medium"

    def update_listening_profile_for_state(self):
        try:
            if self.quran.is_waiting_for_child():
                self.set_listening_profile(
                    self.get_quran_listening_profile()
                )
                return
        except Exception:
            pass

        try:
            if self.stories.is_waiting_for_answer():
                self.set_listening_profile("story_answer")
                return
        except Exception:
            pass

        try:
            if (
                self.learning.is_waiting_for_topic()
                or self.learning.is_waiting_for_answer()
                or self.riddles.is_active()
            ):
                self.set_listening_profile("short")
                return
        except Exception:
            pass

        # Adhkar replies/recitation: keep listening short and responsive.
        try:
            if (
                self.adhkar.is_morning()
                or self.adhkar.is_evening()
                or self.adhkar.is_sleep()
            ):
                self.set_listening_profile("adhkar_short")
                return
        except Exception:
            pass

        self.set_listening_profile("short")

    # =====================================================
    # MIMI SAY
    # =====================================================
    #
    # من هسا قدر الإمكان controller يستخدم هذه الدالة
    # بدل self.voice.say مباشرة.
    #
    # السبب:
    # نحفظ آخر جملة قالتها Mimi.
    # =====================================================

    def say(
        self,
        text,
        resume_listening=True,
        remember=True,
    ):

        text = str(text).strip()

        if not text:
            return False

        if remember:
            self.last_response_text = text

        self.set_face("talking")

        # Keep Pygame's main thread rendering while VoiceModule blocks
        # during audio generation/playback.
        done = threading.Event()
        holder = {"result": False, "error": None}

        def speak_worker():
            try:
                try:
                    holder["result"] = self.voice.say(
                        text,
                        resume_listening=resume_listening,
                    )
                except TypeError:
                    holder["result"] = self.voice.say(text)
            except Exception as error:
                holder["error"] = error
            finally:
                done.set()

        worker = threading.Thread(
            target=speak_worker,
            name="mimi-tts",
            daemon=True,
        )
        worker.start()

        try:
            while not done.is_set() and self.running:
                try:
                    if not self.face.update():
                        self.running = False
                        break
                except Exception:
                    time.sleep(0.01)

            worker.join(timeout=0.25)

            if holder["error"] is not None:
                print()
                print("❌ Mimi speech error:")
                print(holder["error"])
                return False

            return holder["result"]

        finally:
            self.set_face(
                self.get_resting_face()
            )

    # =====================================================
    # SPEAK LEARNING PROMPT
    # =====================================================

    def speak_prompt_after_audio(
        self,
        text,
    ):
        """
        يستخدم بعد MP3 مباشرة.
        يبقي نفس المايك شغالًا، وينتظر تحرير جهاز الصوت
        ثم ينطق السؤال. إذا فشل التشغيل بسبب انشغال
        جهاز الصوت، يعيد المحاولة مرة واحدة.
        """

        text = str(
            text or ""
        ).strip()

        if not text:
            return False

        self.pause_listener_for_content()
        self.set_face(
            "talking"
        )

        # MP3 modules now release ALSA cleanly through ffmpeg -> aplay.
        wait_until = (
            time.monotonic()
            + 0.60
        )

        while (
            time.monotonic()
            <
            wait_until
        ):
            try:
                self.face.update()
            except Exception:
                pass

            time.sleep(
                0.03
            )

        self.set_face(
            "talking"
        )

        first_ok = self.say(
            text,
            resume_listening=False,
        )

        if first_ok:
            return True

        print()
        print(
            "⚠️ Question audio did not play. Retrying once..."
        )

        retry_until = (
            time.monotonic()
            + 0.75
        )

        while (
            time.monotonic()
            <
            retry_until
        ):
            try:
                self.face.update()
            except Exception:
                pass

            time.sleep(
                0.03
            )

        self.set_face(
            "talking"
        )

        return bool(
            self.say(
                text,
                resume_listening=False,
            )
        )

    # =====================================================
    # PERSONALITY RESPONSE
    # =====================================================

    def response(
        self,
        key,
        fallback,
        **values,
    ):

        try:

            text = self.responses.choose(
                key,
                **values,
            )

        except Exception:

            text = ""

        if not text:

            text = fallback

        return text

    # =====================================================
    # REPEAT LAST RESPONSE
    # =====================================================

    def repeat_last_response(self):

        if self.last_response_text:

            text = self.last_response_text

            print()
            print(
                "🔁 Repeating last Mimi response."
            )

            self.say(
                text,
                remember=False,
            )

            return True

        self.say(
            "لسا ما حكيت إشي. "
            "شو بتحب نعمل؟"
        )

        return False

    # =====================================================
    # START
    # =====================================================

    def start(self):

        print()
        print("=" * 70)
        print("🤖 MIMI BOT - INTERACTION V3")
        print("=" * 70)

        print()
        print("🎀 Starting Mimi Face...")
        self.set_face(
            "idle"
        )

        print()
        print("📷 Starting Vision in background...")
        self.vision.start()

        print()
        print("🎤 Starting Voice...")
        self.voice.start(
            listening=False
        )

        print()
        print("🧠 Starting Mimi Brain V3...")
        self.dialogue.start()

        print()
        print("📚 Starting Stories...")
        self.stories.start_module()

        print()
        print("🧩 Starting Riddles...")
        self.riddles.start_module()

        print()
        print("📖 Starting Quran...")
        self.quran.start_module()

        print()
        print("🤲 Starting Adhkar...")
        self.adhkar.start_module()

        print()
        print("🎓 Starting Learning...")
        self.learning.start_module()

        print()
        print("📋 Starting Tasks...")
        self.tasks.start_module()

        print()
        print("🏆 Starting Achievements...")
        self.achievements.start_module()

        print()
        print("🚨 Starting Safety...")
        self.safety.start_module()

        try:
            self.safety.set_alert_callback(
                self._on_safety_alert
            )
        except Exception:
            pass

        print()
        print("=" * 70)
        print("✅ MIMI INTERACTION V3 READY")
        print("=" * 70)

        print()
        print(
            "👀 Mimi is waiting for someone..."
        )

        # لا نحكي ترحيب تجريبي عند تشغيل البرنامج.
        # الترحيب الحقيقي يصير مرة واحدة فقط بعد التعرف على الطفل.
        self.set_face(
            "idle"
        )

    # =====================================================
    # CURRENT CHILD
    # =====================================================

    def get_current_child_id(self):

        if self.current_session is None:

            return None

        child = self.current_session.get(
            "child",
            {},
        )

        return child.get(
            "child_id"
        )

    # =====================================================
    # SAFE ACTIVITY DETAILS
    # =====================================================

    def get_safe_slots(
        self,
        slots,
    ):

        if not isinstance(
            slots,
            dict,
        ):

            return {}

        allowed = {
            "quran_mode",
            "surah_number",
            "surah_name",
            "surah_confidence",
            "surah_supported",
            "learning_topic",
            "story_type",
            "task_action",
            "universal_command",
        }

        result = {}

        for key in allowed:

            value = slots.get(
                key
            )

            if value is not None:

                result[key] = value

        return result

    # =====================================================
    # ACHIEVEMENTS
    # =====================================================

    def achievement_event(
        self,
        event_type,
        **data,
    ):

        if self.current_session is None:

            return []

        try:

            result = (
                self.achievements.check_event(
                    event_type,
                    **data,
                )
            )

            if result:

                print()
                print(
                    f"🏆 New achievements: "
                    f"{len(result)}"
                )

            return result

        except Exception as error:

            print()
            print(
                "⚠️ Achievement error:"
            )
            print(
                error
            )

            return []

    # =====================================================
    # ACTIVITY HISTORY
    # =====================================================

    def begin_activity(
        self,
        activity_type,
        details=None,
    ):

        child_id = (
            self.get_current_child_id()
        )

        if not child_id:

            self.active_activity_id = None
            self.active_activity_type = (
                activity_type
            )

            print()
            print(
                f"👤 Guest activity: "
                f"{activity_type}"
            )

            return None

        try:

            activity_id = start_activity(
                child_id=child_id,
                activity_type=activity_type,
                details=details or {},
            )

            self.active_activity_id = (
                activity_id
            )

            self.active_activity_type = (
                activity_type
            )

            return activity_id

        except Exception as error:

            print()
            print(
                "⚠️ Activity start error:"
            )
            print(
                error
            )

            self.active_activity_id = None
            self.active_activity_type = (
                activity_type
            )

            return None

    def finish_activity(
        self,
        status="completed",
        score=None,
        details=None,
    ):

        activity_id = (
            self.active_activity_id
        )

        activity_type = (
            self.active_activity_type
        )

        self.active_activity_id = None
        self.active_activity_type = None

        if not activity_id:

            return None

        try:

            result = complete_activity(
                activity_id=activity_id,
                status=status,
                score=score,
                details=details,
            )

            print()
            print(
                f"📝 Activity saved: "
                f"{activity_type}"
            )

            return result

        except Exception as error:

            print()
            print(
                "⚠️ Activity finish error:"
            )
            print(
                error
            )

            return None

    # =====================================================
    # RESET ACTIVITIES
    # =====================================================

    def reset_activities(self):

        modules = [
            self.stories,
            self.riddles,
            self.quran,
            self.adhkar,
            self.learning,
            self.tasks,
        ]

        for module in modules:

            try:

                module.reset()

            except Exception:

                pass

    # =====================================================
    # RESET BRAIN
    # =====================================================

    def reset_brain_state(self):

        self.waiting_for_story_type = False

        self.last_intent = ""
        self.last_confidence = 0.0
        self.last_nlu_source = ""

        try:

            self.dialogue.reset()

        except Exception:

            pass

    # =====================================================
    # PREPARE ACTIVITY
    # =====================================================

    def prepare_activity(
        self,
        activity_type,
        details=None,
    ):

        if self.safety.is_active():

            return False

        if self.active_activity_id:

            self.finish_activity(
                status="interrupted",
                details={
                    "reason":
                        "new_activity_started"
                },
            )

        self.reset_activities()

        self.begin_activity(
            activity_type,
            details=
                details or {},
        )

        return True

    # =====================================================
    # SAFETY
    # =====================================================

    def _interrupt_activity_audio_for_safety(self):
        """Stop current output immediately without closing the mic."""

        try:
            self.voice.stop_speaking()
        except Exception:
            pass

        try:
            self.stories.stop_requested = True
            self.stories.last_control_command = "safety"
            stopper = getattr(self.stories, "_stop_player", None)
            if callable(stopper):
                stopper()
        except Exception:
            pass

        try:
            self.quran.quran_stop_requested = True
            self.quran.last_control_command = "safety"
            player = getattr(self.quran, "player", None)
            if player is not None:
                stop = getattr(player, "stop", None)
                if callable(stop):
                    stop()
        except Exception:
            pass

        try:
            self.learning.learning_stop_requested = True
            self.learning.last_control_command = "safety"
            stopper = getattr(self.learning, "_stop_lesson_player", None)
            if callable(stopper):
                stopper()
        except Exception:
            pass

        try:
            self.adhkar.adhkar_stop_requested = True
            self.adhkar.last_control_command = "safety"
            stopper = getattr(self.adhkar, "stop_audio", None)
            if callable(stopper):
                stopper()
        except Exception:
            pass

        return True

    def _queue_safety_result(self, result):

        if not isinstance(result, dict):
            return False

        with self._safety_result_lock:
            self._pending_safety_results.append(dict(result))

        return True

    def _on_safety_alert(self, payload):
        """Called asynchronously by SafetyModule real-audio detection."""

        payload = dict(payload) if isinstance(payload, dict) else {}

        self._interrupt_activity_audio_for_safety()

        self._queue_safety_result({
            "handled": True,
            "triggered": True,
            "trigger_type": payload.get("trigger_type"),
            "event_id": payload.get("event_id"),
        })

    def process_pending_safety_results(self):

        pending = []

        with self._safety_result_lock:
            if self._pending_safety_results:
                pending = list(self._pending_safety_results)
                self._pending_safety_results.clear()

        for result in pending:
            self.process_safety_result(result)

        return len(pending)

    def process_safety_result(
        self,
        result,
    ):

        if not isinstance(
            result,
            dict,
        ):

            return False

        if result.get(
            "triggered",
            False,
        ):

            event_id = result.get("event_id")

            if (
                event_id
                and event_id == self._last_processed_safety_event_id
            ):
                return True

            if event_id:
                self._last_processed_safety_event_id = event_id

            self._interrupt_activity_audio_for_safety()

            if self.active_activity_id:

                self.finish_activity(
                    status="interrupted",
                    details={
                        "reason":
                            "safety_triggered",

                        "trigger_type":
                            result.get(
                                "trigger_type"
                            ),
                    },
                )

            self.reset_activities()
            self.reset_brain_state()

            print()
            print(
                "🚨 Mimi entered SAFETY MODE."
            )

            self.set_face(
                "alert"
            )

            return True

        if result.get(
            "alert_active",
            False,
        ):

            self.set_face(
                "alert"
            )

            return True

        if result.get(
            "cleared",
            False,
        ):

            self.reset_brain_state()

            print()
            print(
                "✅ Safety Mode cleared."
            )

            self.set_face(
                self.get_resting_face()
            )

            return True

        return False

    def handle_loud_sound(
        self,
        sound_level=None,
    ):

        result = (
            self.safety.trigger_loud_sound(
                sound_level=
                    sound_level
            )
        )

        self.process_safety_result(
            result
        )

        return result

    # =====================================================
    # GREETING GUEST
    # =====================================================

    def greet_guest(self):

        print()
        print("=" * 60)
        print("👤 GUEST MODE")
        print("=" * 60)

        text = (
            self.responses.greeting()
        )

        self.say(
            text
        )

        try:

            self.voice.enable()

        except Exception:

            pass

    # =====================================================
    # GREETING CHILD
    # =====================================================

    def greet_child(self):

        if self.current_session is None:

            return

        child = self.current_session.get(
            "child",
            {},
        )

        name = child.get(
            "name",
            "صديقي",
        )

        greeting = (
            self.responses.greeting(
                name
            )
        )

        # نجعل الترحيب سريع.
        # ما نقرأ كل معلومات DB كل مرة.
        self.say(
            greeting
        )

        try:

            self.voice.enable()

        except Exception:

            pass

        # بعد الترحيب، إذا الوقت مناسب وما في نشاط شغال،
        # ذكّر الطفل بأذكار الصباح أو المساء مرة واحدة فقط.
        self.check_adhkar_reminder()

    # =====================================================
    # LOAD CHILD
    # =====================================================

    def load_child(
        self,
        face_id,
    ):

        print()
        print("=" * 70)
        print(
            f"🔎 Loading child: {face_id}"
        )
        print("=" * 70)

        if self.active_activity_id:

            self.finish_activity(
                status="interrupted",
                details={
                    "reason":
                        "child_changed"
                },
            )

        self.reset_brain_state()

        try:

            session = (
                create_child_session(
                    face_id
                )
            )

        except Exception as error:

            print()
            print(
                "⚠️ Database unavailable:"
            )
            print(
                error
            )

            session = None

        # =================================================
        # REGISTERED CHILD
        # =================================================

        if session is not None:

            self.current_face_id = face_id
            self.person_present = True

            self.current_session = session

            self.guest_mode = False

            self.unknown_count = 0

            self.reset_activities()

            child_id = session[
                "child"
            ][
                "child_id"
            ]

            child_name = (
                session
                .get(
                    "child",
                    {},
                )
                .get(
                    "name"
                )
            )

            # -------------------------------------------------
            # Hybrid AI child context
            # -------------------------------------------------
            # The child name is kept locally and is used only
            # by the privacy sanitizer to remove it from any
            # open-domain question before sending it to Gemini.
            # -------------------------------------------------

            try:

                self.dialogue.set_child(
                    child_name
                )

            except Exception:

                pass

            try:

                self.quran.set_child(
                    child_id
                )

            except Exception:

                pass

            try:

                self.tasks.set_session(
                    session
                )

            except Exception:

                pass

            try:

                self.achievements.set_child(
                    child_id
                )

            except Exception:

                pass

            try:

                self.safety.set_child(
                    child_id
                )

            except Exception:

                pass

            try:

                self.current_total_points = (
                    get_points(
                        child_id
                    )
                )

            except Exception:

                self.current_total_points = 0

            try:

                show_session(
                    session
                )

            except Exception:

                pass

            self.greet_child()

            return

        # =================================================
        # GUEST
        # =================================================

        self.current_face_id = face_id
        self.person_present = True

        self.current_session = None

        self.current_total_points = 0

        self.guest_mode = True

        self.reset_activities()

        try:
            self.dialogue.clear_child()
        except Exception:
            pass

        try:
            self.quran.set_child(None)
        except Exception:
            pass

        try:
            self.tasks.set_session(None)
        except Exception:
            pass

        try:
            self.achievements.clear_child()
        except Exception:
            pass

        try:
            self.safety.set_child(None)
        except Exception:
            pass

        self.greet_guest()

    # =====================================================
    # ACTIVATE GUEST
    # =====================================================

    def activate_guest(self):

        if self.guest_mode:
            return

        print()
        print("=" * 60)
        print("👤 ACTIVATING GUEST MODE")
        print("=" * 60)

        if self.active_activity_id:

            self.finish_activity(
                status="interrupted",
                details={
                    "reason":
                        "guest_mode_started"
                },
            )

        self.current_face_id = None
        self.current_session = None
        self.current_total_points = 0
        self.guest_mode = True

        self.reset_brain_state()
        self.reset_activities()

        try:
            self.dialogue.clear_child()
        except Exception:
            pass

        try:
            self.quran.set_child(None)
        except Exception:
            pass

        try:
            self.tasks.set_session(None)
        except Exception:
            pass

        try:
            self.achievements.clear_child()
        except Exception:
            pass

        try:
            self.safety.set_child(None)
        except Exception:
            pass

        self.greet_guest()

    # =====================================================
    # ACTIVE CONTENT PROTECTION
    # =====================================================

    def has_active_content(self):
        """
        True while Mimi is in an activity that must NOT be stopped
        just because the camera temporarily loses the child's face.

        The activity continues until it finishes normally or the child
        explicitly says a stop command such as "وقف حكي".
        """

        checks = [
            lambda: self.stories.is_active(),
            lambda: self.riddles.is_active(),
            lambda: self.quran.is_active(),
            lambda: self.learning.is_active(),
            lambda: self.tasks.is_active(),
            lambda: self.adhkar.is_morning(),
            lambda: self.adhkar.is_evening(),
            lambda: self.adhkar.is_sleep(),
            lambda: self.safety.is_active(),
        ]

        for check in checks:
            try:
                if check():
                    return True
            except Exception:
                pass

        return False

    # =====================================================
    # CLEAR PERSON
    # =====================================================

    def clear_person(self):

        print()
        print("=" * 60)
        print("👀 PERSON LEFT MIMI")
        print("=" * 60)

        # مهم للديمو:
        # لا نمسح current_session ولا current_face_id عند ابتعاد الطفل.
        # نحافظ على هوية الطفل حتى لو رجع بعد ثواني، وبذلك لا
        # نعيد جملة الترحيب ولا نعمل load_child من جديد.
        self.person_present = False
        self.unknown_count = 0
        self.last_face_seen_time = 0.0

        # إذا ما في نشاط شغال والشخص غادر، نوقف الاستماع مؤقتًا.
        # أثناء كلام/محتوى Mimi نفسه، المايك يبقى شغال.
        if not self.has_active_content():

            try:
                self.voice.disable()
            except Exception:
                pass

            try:
                self.voice.clear_commands()
            except Exception:
                pass

            self.set_face(
                "idle"
            )

        try:
            self.vision.reset_recognition()
        except Exception:
            pass

        print()
        print(
            "🤖 Mimi is waiting for the same child to return..."
        )

    # =====================================================
    # RIDDLE POINTS
    # =====================================================

    def save_riddle_points(
        self,
        points,
    ):

        child_id = (
            self.get_current_child_id()
        )

        if (
            not child_id
            or
            points <= 0
        ):

            return 0

        try:

            result = add_points(
                child_id=child_id,
                points=points,
                reason=
                    "حل لغز بشكل صحيح",
                activity_type=
                    "riddle",
            )

            if isinstance(
                result,
                (int, float),
            ):

                self.current_total_points = int(
                    result
                )

            else:

                self.current_total_points = (
                    get_points(
                        child_id
                    )
                )

            self.achievement_event(
                "riddle_correct",
                points=points,
                total_points=
                    self.current_total_points,
            )

            return self.current_total_points

        except Exception as error:

            print()
            print(
                "⚠️ Reward error:"
            )
            print(
                error
            )

            return 0

    # =====================================================
    # GLOBAL COMMAND
    # =====================================================

    def detect_global_command(
        self,
        text,
    ):

        try:

            result = (
                self.dialogue.nlu
                .normalizer
                .normalize(
                    text
                )
            )

            canonical = (
                result.get(
                    "canonical",
                    "",
                )
            )

        except Exception:

            return None

        if canonical in {
            "وقف",
            "توقف",
            "وقفي",
            "وقف حكي",
            "وقفي حكي",
            "توقف حكي",
            "خلص حكي",
            "خلص",
            "اسكت",
            "اسكتي",
            "وقف القصه",
            "وقفي القصه",
            "وقف القصة",
            "وقفي القصة",
        }:

            return "stop"

        if canonical in {
            "وطي الصوت",
            "وطي صوتك",
            "خفض الصوت",
            "خفضي الصوت",
            "قلل الصوت",
            "قللي الصوت",
            "نزل الصوت",
            "نزلي الصوت",
        }:

            return "volume_down"

        if canonical in {
            "علي الصوت",
            "علي صوتك",
            "ارفع الصوت",
            "ارفعي الصوت",
            "زيد الصوت",
            "زيدي الصوت",
        }:

            return "volume_up"

        if canonical in {
            "عيدي",
            "كرر",
            "كرري",
            "عيد",
            "مره ثانيه",
            "كمان مره",
        }:

            return "repeat"

        if canonical in {
            "ارجع",
            "رجع",
            "ارجعي",
        }:

            return "back"

        return None

    # =====================================================
    # CONVERSATION CONTROL
    # =====================================================

    def detect_conversation_control(
        self,
        text,
    ):

        try:

            result = (
                self.dialogue
                .nlu
                .conversation_signals
                .detect(
                    text
                )
            )

        except Exception:

            return None

        if not result.get(
            "matched",
            False,
        ):

            return None

        intent = result.get(
            "intent"
        )

        if intent in {
            "wait",
            "did_not_understand",
            "change",
        }:

            return intent

        return None

    # =====================================================
    # HANDLE GLOBAL COMMAND
    # =====================================================

    def handle_global_command(
        self,
        command,
    ):

        print()
        print(
            f"🌍 Global command: {command}"
        )

        if command == "volume_down":

            try:
                self.voice.lower_volume(step=15)
            except Exception as error:
                print("⚠️ Volume down error:", error)

            self.say(
                "تمام، وطيت الصوت شوي.",
                remember=False,
            )
            return

        if command == "volume_up":

            try:
                self.voice.raise_volume(step=15)
            except Exception as error:
                print("⚠️ Volume up error:", error)

            self.say(
                "تمام، عليت الصوت شوي.",
                remember=False,
            )
            return

        if command == "repeat":

            self.repeat_last_response()
            return

        if command == "stop":

            if self.active_activity_id:

                self.finish_activity(
                    status="interrupted",
                    details={
                        "reason":
                            "child_requested_stop"
                    },
                )

            self.reset_activities()
            self.reset_brain_state()

            self.say(
                self.responses.stop()
            )

            return

        if command == "back":

            if self.active_activity_id:

                self.finish_activity(
                    status="interrupted",
                    details={
                        "reason":
                            "child_requested_back"
                    },
                )

            self.reset_activities()
            self.reset_brain_state()

            self.say(
                self.responses.back()
            )

            return

    # =====================================================
    # ACTIVE CONVERSATION CONTROL
    # =====================================================

    def handle_conversation_control(
        self,
        intent,
    ):

        if intent == "wait":

            self.say(
                "تمام، بستنى."
            )

            return True

        if intent == "did_not_understand":

            self.repeat_last_response()

            return True

        if intent == "change":

            if self.active_activity_id:

                self.finish_activity(
                    status="interrupted",
                    details={
                        "reason":
                            "child_requested_change"
                    },
                )

            self.reset_activities()
            self.reset_brain_state()

            self.say(
                "أكيد، شو بتحب نعمل بدلها؟"
            )

            return True

        return False

    # =====================================================
    # BUILD QURAN REQUEST
    # =====================================================

    def build_quran_request(
        self,
        intent,
        slots,
    ):

        surah_name = slots.get(
            "surah_name"
        )

        if intent == "quran_memorize":

            if surah_name:

                return (
                    f"احفظ سورة {surah_name}"
                )

            return "احفظ قرآن"

        if surah_name:

            return (
                f"اقري سورة {surah_name}"
            )

        return "اقري قرآن"

    # =====================================================
    # BUILD LEARNING REQUEST
    # =====================================================

    def build_learning_request(
        self,
        slots,
    ):

        topic = slots.get(
            "learning_topic"
        )

        names = {
            "colors":
                "الالوان",

            "numbers":
                "الارقام",

            "letters":
                "الحروف",

            "addition":
                "الجمع",
        }

        if topic in names:

            return (
                "تعلم "
                +
                names[
                    topic
                ]
            )

        return "تعلم"

    # =====================================================
    # STORY TYPE FOLLOW-UP
    # =====================================================

    def detect_story_type_from_text(self, text):
        """فهم نوع القصة من جواب الطفل بدون إرسال الجواب للـNLU."""

        normalized = str(text or "").strip().lower()

        for char in ("؟", "?", "!", ".", ",", "،"):
            normalized = normalized.replace(char, "")

        normalized = " ".join(normalized.split())

        groups = {
            "adventure": (
                "مغامرة", "مغامره", "مغامرات",
                "قصة مغامرة", "قصه مغامره",
                "النملة", "النمله", "القمح",
            ),
            "funny": (
                "مضحكة", "مضحكه", "مضحك", "ضحك",
                "قصة مضحكة", "قصه مضحكه", "زوزو",
            ),
            "animals": (
                "حيوانات", "حيوان", "حيوانية", "حيوانيه",
                "قصة حيوانات", "قصه حيوانات",
                "ارنب", "أرنب", "سلحفاة", "سلحفاه",
            ),
            "educational": (
                "تربوية", "تربويه", "تعليمية", "تعليميه",
                "مفيدة", "مفيده", "تعليم",
                "كتكوت", "كوك", "وعد",
            ),
        }

        for story_type, phrases in groups.items():
            if any(phrase in normalized for phrase in phrases):
                return story_type

        return None

    def ask_for_story_type(self):
        """نسأل عن النوع ونترك Mimi في listening حتى يجيب الطفل."""

        self.waiting_for_story_type = True

        self.say(
            "أكيد! شو نوع القصة اللي بدك ياها؟ "
            "مغامرة، مضحكة، حيوانات، ولا تربوية؟",
            resume_listening=True,
        )

        # مهم: بعد انتهاء السؤال نظل Listening فعلًا حتى يصل جواب الطفل.
        self.set_face("listening")

        try:
            self.voice.enable()
        except Exception:
            pass

        return True

    def handle_story_type_answer(self, text):
        """يتعامل مع جواب سؤال نوع القصة."""

        if not self.waiting_for_story_type:
            return False

        story_type = self.detect_story_type_from_text(text)

        if story_type is None:
            self.say(
                "اختاريلي نوع واحد: مغامرة، مضحكة، حيوانات، ولا تربوية؟",
                resume_listening=True,
            )
            self.set_face("listening")
            return True

        self.waiting_for_story_type = False

        return self.handle_story({
            "story_type": story_type,
        })

    # =====================================================
    # BUILD STORY REQUEST
    # =====================================================

    def build_story_request(
        self,
        slots,
    ):

        story_type = slots.get(
            "story_type"
        )

        if story_type == "animals":

            return "قصة عن حيوانات"

        if story_type == "funny":

            return "قصة مضحكة"

        if story_type == "educational":

            return "قصة تعليمية"

        if story_type == "adventure":

            return "قصة مغامرة"

        return "قصة"

    # =====================================================
    # GREETING
    # =====================================================

    def handle_greeting(self):

        name = None

        if self.current_session:

            name = (
                self.current_session
                .get(
                    "child",
                    {},
                )
                .get(
                    "name"
                )
            )

        self.say(
            self.responses.greeting(
                name
            )
        )

    # =====================================================
    # SOCIAL CONVERSATION
    # =====================================================

    def handle_how_are_you(self):

        self.say(
            self.responses.how_are_you()
        )

    def handle_robot_name(self):

        self.say(
            self.responses.name_response()
        )

    def handle_capabilities(self):

        self.say(
            self.responses.capabilities()
        )

    def handle_thanks(self):

        self.say(
            self.responses.thanks()
        )

    def handle_compliment(self):

        self.say(
            self.responses.compliment()
        )

    def handle_affection(self):

        text = self.response(
            "affection",

            "وأنا مبسوطة إني موجودة معك."
        )

        self.say(
            text
        )

    # =====================================================
    # CHILD EMOTIONS
    # =====================================================

    def handle_child_happy(self):

        text = self.response(
            "child_happy",

            "حلو! مبسوطة إن يومك حلو. "
            "شو بتحب نعمل؟"
        )

        self.say(
            text
        )

    def handle_child_sad(self):

        text = self.response(
            "child_sad",

            "آه، فهمت. "
            "بدك نحكي قصة "
            "ولا نعمل لغز يغير جوك؟"
        )

        self.say(
            text
        )

    def handle_child_scared(self):

        text = self.response(
            "child_scared",

            "أنا معك. "
            "إذا في خطر أو بدك مساعدة، "
            "احكي ساعدني. "
            "وإذا لا، احكيلي شو مخوفك."
        )

        self.say(
            text
        )

    def handle_child_tired(self):

        text = self.response(
            "child_tired",

            "تمام. ما بدنا نتعبك. "
            "بدك قصة هادية "
            "ولا نوقف شوي؟"
        )

        self.say(
            text
        )

    def handle_child_bored(self):

        text = self.response(
            "child_bored",

            "طيب نغير الجو! "
            "بدك قصة ولا لغز؟"
        )

        self.say(
            text
        )

    # =====================================================
    # DIALOGUE SIGNALS
    # =====================================================

    def handle_yes(self):

        self.say(
            self.responses.choose(
                "yes"
            )
            or
            "تمام."
        )

    def handle_no(self):

        self.say(
            "تمام. "
            "شو بتحب نعمل بدل هيك؟"
        )

    def handle_continue(self):

        self.say(
            "أكيد. "
            "شو بدك نكمل؟"
        )

    def handle_change(self):

        self.handle_conversation_control(
            "change"
        )

    def handle_wait(self):

        self.handle_conversation_control(
            "wait"
        )

    def handle_repeat_signal(self):

        self.repeat_last_response()

    def handle_did_not_understand(self):

        self.repeat_last_response()

    # =====================================================
    # HELP
    # =====================================================

    def handle_help(self):

        self.say(
            self.responses.capabilities()
        )

    # =====================================================
    # TASKS
    # =====================================================

    def handle_tasks(
        self,
        slots=None,
    ):

        slots = slots or {}

        if not self.prepare_activity(
            "tasks",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        result = self.tasks.start(
            request_text=
                "مهامي"
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {}

        count = int(
            result.get(
                "count",
                0,
            )
            or 0
        )

        self.finish_activity(
            status="completed",
            details={
                "task_count":
                    count,

                "slots":
                    self.get_safe_slots(
                        slots
                    ),
            },
        )

        self.achievement_event(
            "tasks_viewed",
            task_count=count,
        )

    # =====================================================
    # DAILY ADHKAR REMINDER
    # =====================================================

    def _adhkar_logical_date(self):
        """
        بعد منتصف الليل وحتى 01:59 نعتبرها امتدادًا لفترة النوم
        لليوم السابق حتى لا نكرر تذكير النوم عند 00:00.
        """

        now = datetime.now().astimezone()

        if now.hour < self.sleep_adhkar_end_hour:
            now = now - timedelta(days=1)

        return now.date().isoformat()

    def _get_adhkar_child_key(self):

        child_id = self.get_current_child_id()

        if child_id is None:
            return None

        return str(child_id)

    def _read_adhkar_state_file(self):

        try:

            if not self.adhkar_state_file.exists():
                return {}

            with open(
                self.adhkar_state_file,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if isinstance(data, dict):
                return data

        except Exception as error:

            print(
                "⚠️ Could not read adhkar reminder state:",
                error,
            )

        return {}

    def _write_adhkar_state_file(self, data):

        try:

            self.adhkar_state_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with open(
                self.adhkar_state_file,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            return True

        except Exception as error:

            print(
                "⚠️ Could not save adhkar reminder state:",
                error,
            )

            return False

    def _save_adhkar_reminder_state(self):

        child_key = self._get_adhkar_child_key()

        if child_key is None:
            return False

        data = self._read_adhkar_state_file()

        data[child_key] = {
            "date": self.adhkar_reminder_date,
            "morning_reminded": self.morning_adhkar_reminded_today,
            "evening_reminded": self.evening_adhkar_reminded_today,
            "sleep_reminded": self.sleep_adhkar_reminded_today,
            "postponed_mode": self.adhkar_postponed_mode,
            "postponed_until": self.adhkar_postponed_until,
            "followup_used": self.adhkar_followup_used,
        }

        return self._write_adhkar_state_file(
            data
        )

    def reset_daily_adhkar_reminders_if_needed(self):

        today = self._adhkar_logical_date()

        if self.adhkar_reminder_date == today:
            return

        self.adhkar_reminder_date = today
        self.morning_adhkar_reminded_today = False
        self.evening_adhkar_reminded_today = False
        self.sleep_adhkar_reminded_today = False
        self.waiting_for_adhkar_confirmation = None
        self.adhkar_postponed_mode = None
        self.adhkar_postponed_until = None
        self.adhkar_followup_used = False

        child_key = self._get_adhkar_child_key()

        if child_key is None:
            return

        data = self._read_adhkar_state_file()
        saved = data.get(
            child_key,
            {},
        )

        if (
            isinstance(saved, dict)
            and saved.get("date") == today
        ):

            self.morning_adhkar_reminded_today = bool(
                saved.get("morning_reminded", False)
            )
            self.evening_adhkar_reminded_today = bool(
                saved.get("evening_reminded", False)
            )
            self.sleep_adhkar_reminded_today = bool(
                saved.get("sleep_reminded", False)
            )

            self.adhkar_postponed_mode = saved.get(
                "postponed_mode"
            )
            self.adhkar_postponed_until = saved.get(
                "postponed_until"
            )
            self.adhkar_followup_used = bool(
                saved.get("followup_used", False)
            )

        else:

            self._save_adhkar_reminder_state()

    def get_adhkar_reminder_mode(self):

        self.reset_daily_adhkar_reminders_if_needed()

        hour = datetime.now().astimezone().hour

        if (
            self.morning_adhkar_start_hour
            <= hour
            <= self.morning_adhkar_end_hour
            and
            not self.morning_adhkar_reminded_today
        ):
            return "morning"

        if (
            self.evening_adhkar_start_hour
            <= hour
            <= self.evening_adhkar_end_hour
            and
            not self.evening_adhkar_reminded_today
        ):
            return "evening"

        if (
            hour >= self.sleep_adhkar_start_hour
            or
            hour < self.sleep_adhkar_end_hour
        ):
            if not self.sleep_adhkar_reminded_today:
                return "sleep"

        return None

    def _mark_adhkar_reminded(self, mode):

        if mode == "morning":
            self.morning_adhkar_reminded_today = True

        elif mode == "evening":
            self.evening_adhkar_reminded_today = True

        elif mode == "sleep":
            self.sleep_adhkar_reminded_today = True

        self._save_adhkar_reminder_state()

    def _adhkar_invitation_text(self, mode, name, followup=False):

        if followup:
            if mode == "sleep":
                return (
                    f"يا {name}، قبل ما ننام خلينا ما ننسى أذكار النوم. "
                    "يلا نقرأهم ونكسب حسنات سوا. هسا ولا بعدين؟"
                )

            return (
                f"يا {name}، بتتذكر أذكارنا؟ "
                "يلا نقرأهم هسا ونكسب حسنات سوا. هسا ولا بعدين؟"
            )

        if mode == "morning":
            return (
                f"صباح الخير يا {name}. "
                "شو رأيك نبدأ يومنا بأذكار الصباح ونكسب حسنات سوا؟ "
                "هسا ولا بعدين؟"
            )

        if mode == "evening":
            return (
                f"مساء الخير يا {name}. "
                "شو رأيك نقرأ أذكار المساء سوا ونكسب حسنات؟ "
                "هسا ولا بعدين؟"
            )

        return (
            f"يا {name}، قرب وقت النوم. "
            "شو رأيك نقرأ أذكار النوم سوا قبل ما ننام؟ "
            "هسا ولا بعدين؟"
        )

    def check_adhkar_reminder(self):
        """
        يسأل الطفل مرة في الفترة المناسبة.
        إذا اختار "بعدين"، يرجع له بعد 30 دقيقة بدون مقاطعة نشاط.
        """

        self.reset_daily_adhkar_reminders_if_needed()

        # لا نذكّر بدون طفل معروف حاضر في الجلسة.
        if self.current_session is None:
            return False

        # لا نقاطع قصة/قرآن/تعلم/أذكار أو أي محتوى شغال.
        if self.has_active_content():
            return False

        if self.waiting_for_adhkar_confirmation:
            return False

        now_mono = time.time()

        # =================================================
        # FOLLOW-UP AFTER "بعدين"
        # =================================================

        if (
            self.adhkar_postponed_mode
            and
            self.adhkar_postponed_until is not None
            and
            now_mono >= self.adhkar_postponed_until
        ):
            mode = self.adhkar_postponed_mode
            self.adhkar_postponed_mode = None
            self.adhkar_postponed_until = None
            self.adhkar_followup_used = True
            self._save_adhkar_reminder_state()

            child = self.current_session.get("child", {})
            name = child.get("name", "صديقي")

            self.waiting_for_adhkar_confirmation = mode

            print()
            print(f"🤲 Adhkar follow-up: {mode}")

            self.say(
                self._adhkar_invitation_text(
                    mode,
                    name,
                    followup=True,
                ),
                resume_listening=True,
            )

            return True

        # =================================================
        # FIRST REMINDER
        # =================================================

        mode = self.get_adhkar_reminder_mode()

        if mode is None:
            return False

        child = self.current_session.get("child", {})
        name = child.get("name", "صديقي")

        self.waiting_for_adhkar_confirmation = mode
        self._mark_adhkar_reminded(mode)
        self.adhkar_followup_used = False
        self._save_adhkar_reminder_state()

        print()
        print(f"🤲 Adhkar reminder: {mode}")

        self.say(
            self._adhkar_invitation_text(
                mode,
                name,
                followup=False,
            ),
            resume_listening=True,
        )

        return True

    def handle_adhkar_confirmation(self, text):
        """
        يفهم: هسا/يلا/نعم، بعدين، أو لا.
        """

        mode = self.waiting_for_adhkar_confirmation

        if mode is None:
            return False

        normalized = str(text).strip().lower()

        for char in ("؟", "?", "!", ".", ",", "،"):
            normalized = normalized.replace(char, "")

        normalized = " ".join(normalized.split())

        yes_phrases = {
            "هسا", "الان", "الآن",
            "يلا", "اه", "آه", "نعم", "ايوه", "أيوه",
            "اوكي", "أوكي", "تمام", "خلينا",
            "خلينا نقرا", "خلينا نقرأ", "يلا نقرا", "يلا نقرأ",
            "اقرأي", "اقري", "ابدأي", "ابداي",
        }

        # أحيانًا Google STT يسمع جواب الطفل مثل
        # "اذكار الصباح" بدل "يلا". بما أن Mimi أصلًا
        # تنتظر موافقة على نوع محدد، نعتبر اسم الذكر نفسه موافقة.
        mode_accept_phrases = {
            "morning": {
                "اذكار الصباح", "أذكار الصباح",
                "الصباح", "اذكار صباح", "أذكار صباح",
            },
            "evening": {
                "اذكار المساء", "أذكار المساء",
                "المساء", "اذكار مساء", "أذكار مساء",
            },
            "sleep": {
                "اذكار النوم", "أذكار النوم",
                "النوم", "اذكار نوم", "أذكار نوم",
            },
        }

        postpone_phrases = {
            "بعدين", "بعد شوي", "بعد شوية", "مش هسا", "مو هسا",
            "مش الان", "مش الآن",
        }

        decline_phrases = {
            "لا", "لا شكرا", "لا شكرًا", "مش بدي", "ما بدي",
        }

        is_yes = (
            normalized in yes_phrases
            or normalized in mode_accept_phrases.get(mode, set())
            or normalized.startswith("يلا ")
            or normalized.startswith("هسا ")
            or normalized.startswith("نعم ")
            or normalized.startswith("اه ")
            or normalized.startswith("آه ")
        )

        is_postpone = (
            normalized in postpone_phrases
            or normalized.startswith("بعدين ")
            or normalized.startswith("بعد شوي")
        )

        is_decline = (
            normalized in decline_phrases
            or normalized.startswith("لا ")
        )

        if is_yes:
            self.waiting_for_adhkar_confirmation = None
            self.adhkar_postponed_mode = None
            self.adhkar_postponed_until = None
            self._save_adhkar_reminder_state()

            print()
            print(f"✅ Child accepted {mode} adhkar.")

            if mode == "morning":
                self.handle_morning_adhkar()
            elif mode == "evening":
                self.handle_evening_adhkar()
            else:
                self.handle_sleep_adhkar()

            return True

        if is_postpone:
            self.waiting_for_adhkar_confirmation = None

            # بعد المتابعة الثانية لا نلاحق الطفل مرة ثالثة.
            if self.adhkar_followup_used:
                self.adhkar_postponed_mode = None
                self.adhkar_postponed_until = None
                self._save_adhkar_reminder_state()
                self.say(
                    "تمام، بنخلي أذكارنا لوقت ثاني.",
                    resume_listening=True,
                )
            else:
                self.adhkar_postponed_mode = mode
                self.adhkar_postponed_until = (
                    time.time()
                    + self.adhkar_postpone_seconds
                )
                self._save_adhkar_reminder_state()

                self.say(
                    "تمام، بعد ساعة بذكرك.",
                    resume_listening=True,
                )

            return True

        if is_decline:
            self.waiting_for_adhkar_confirmation = None

            if self.adhkar_followup_used:

                self.adhkar_postponed_mode = None
                self.adhkar_postponed_until = None
                self._save_adhkar_reminder_state()

                self.say(
                    "تمام، بنخلي أذكارنا لوقت ثاني.",
                    resume_listening=True,
                )

            else:

                self.adhkar_postponed_mode = mode
                self.adhkar_postponed_until = (
                    time.time()
                    + self.adhkar_postpone_seconds
                )
                self._save_adhkar_reminder_state()

                self.say(
                    "تمام، بعد ساعة بذكرك.",
                    resume_listening=True,
                )

            return True

        self.say(
            "بدك نقرأ الأذكار هسا ولا بعدين؟",
            resume_listening=True,
        )

        return True

    # =====================================================
    # ADHKAR
    # =====================================================

    def handle_morning_adhkar(
        self,
        slots=None,
    ):

        if not self.prepare_activity(
            "morning_adhkar",
            details={
                "slots":
                    self.get_safe_slots(
                        slots or {}
                    )
            },
        ):

            return

        result = (
            self.adhkar.start_morning()
        )

        completed = (
            isinstance(result, dict)
            and result.get("completed", False)
        )

        self.finish_activity(
            status=("completed" if completed else "interrupted"),
            details={"mode": "morning"},
        )

        if completed:
            self.achievement_event(
                "adhkar_completed",
                mode="morning",
            )

        return result

    def handle_evening_adhkar(
        self,
        slots=None,
    ):

        if not self.prepare_activity(
            "evening_adhkar",
            details={
                "slots":
                    self.get_safe_slots(
                        slots or {}
                    )
            },
        ):

            return

        result = (
            self.adhkar.start_evening()
        )

        completed = (
            isinstance(result, dict)
            and result.get("completed", False)
        )

        self.finish_activity(
            status=("completed" if completed else "interrupted"),
            details={"mode": "evening"},
        )

        if completed:
            self.achievement_event(
                "adhkar_completed",
                mode="evening",
            )

        return result

    def handle_sleep_adhkar(
        self,
        slots=None,
    ):

        if not self.prepare_activity(
            "sleep_adhkar",
            details={
                "slots":
                    self.get_safe_slots(
                        slots or {}
                    )
            },
        ):
            return

        result = self.adhkar.start_sleep()

        completed = (
            isinstance(result, dict)
            and result.get("completed", False)
        )

        self.finish_activity(
            status=("completed" if completed else "interrupted"),
            details={"mode": "sleep"},
        )

        if completed:
            self.achievement_event(
                "adhkar_completed",
                mode="sleep",
            )

        return result

    # =====================================================
    # LEARNING
    # =====================================================

    def handle_learning(
        self,
        slots,
    ):

        self.set_listening_profile("short")

        if not self.prepare_activity(
            "learning",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        request_text = (
            self.build_learning_request(
                slots
            )
        )

        # أثناء مقدمة التعليم ودرس MP3 يكون Mimi talking،
        # ونفس المايك يبقى شغال للتحكم المباشر.
        self.pause_listener_for_content()
        self.set_face(
            "talking"
        )

        result = self.learning.start(
            request_text=
                request_text
        )

        # إذا LearningModule جهز سؤالًا، MimiBot تنطقه كاملًا
        # مع بقاء المايك فعالًا أثناء الكلام.
        pending_prompt = ""

        try:
            pending_prompt = (
                self.learning.pop_pending_prompt()
            )
        except Exception:
            pending_prompt = ""

        if pending_prompt:

            self.set_face(
                "talking"
            )

            self.speak_prompt_after_audio(
                pending_prompt
            )

        if (
            isinstance(result, dict)
            and result.get("stopped", False)
        ):

            self.finish_activity(
                status="interrupted",
                details={"reason": "child_requested_stop"},
            )

            self.restore_listener_after_content()
            return result

        # فقط بعد انتهاء السؤال نرجع للاستماع.
        if (
            self.learning.is_waiting_for_topic()
            or
            self.learning.is_waiting_for_answer()
        ):

            self.set_listening_profile(
                "short"
            )

            self.restore_listener_after_content()

        return result

    # =====================================================
    # STORY
    # =====================================================

    def handle_story(
        self,
        slots,
    ):

        slots = slots or {}

        # إذا الطفل قال فقط "بدي قصة" بدون نوع، لا نختار عشوائيًا.
        # نسأله أولًا وننتظر جوابه.
        if not slots.get("story_type"):
            return self.ask_for_story_type()

        self.waiting_for_story_type = False

        # -------------------------------------------------
        # إذا القصة شغالة بالفعل، لا نبدأها من جديد.
        # هذا يمنع تكرار أمر "بدي قصة" أو أي نص عابر
        # من إعادة القصة إلى البداية أثناء السرد.
        # -------------------------------------------------
        if self.stories.is_active():

            print()
            print(
                "📚 Story already active - "
                "duplicate start ignored."
            )

            return False

        self.set_listening_profile("story_answer")

        if not self.prepare_activity(
            "story",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        request_text = (
            self.build_story_request(
                slots
            )
        )

        # أثناء سرد القصة: وجه talking ونفس المايك يبقى شغال
        # لأوامر وقف / وطي الصوت / علي الصوت.
        self.pause_listener_for_content()
        self.set_face("talking")

        result = self.stories.start(
            request_text
        )

        result_type = (
            result.get("type")
            if isinstance(result, dict)
            else None
        )

        if result_type == "story_finished":
            self.finish_activity(status="completed")
            self.achievement_event("story_completed")

        elif result_type == "story_stopped":
            self.finish_activity(
                status="interrupted",
                details={"reason": "child_requested_stop"},
            )

        elif result_type == "story_error":
            self.finish_activity(status="failed")

        if self.stories.is_active() and self.stories.is_waiting_for_answer():
            self.restore_listener_after_content()
        elif self.stories.is_active():
            self.set_face("talking")
        else:
            self.restore_listener_after_content()

        return result

    # =====================================================
    # RIDDLE
    # =====================================================

    def handle_riddle(
        self,
        slots,
    ):

        self.set_listening_profile("short")

        if not self.prepare_activity(
            "riddle",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        return self.riddles.start()

    # =====================================================
    # QURAN READ
    # =====================================================

    def handle_quran_read(
        self,
        slots,
    ):

        if not self.prepare_activity(
            "quran_read",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        request_text = (
            self.build_quran_request(
                "quran_read",
                slots,
            )
        )

        # التلاوة صوت محتوى طويل، لكن نفس المايك يبقى شغال
        # للتحكم المباشر أثناء صوت الشيخ.
        self.pause_listener_for_content()
        self.set_face("talking")

        result = (
            self.quran.start_reading(
                request_text=
                    request_text
            )
        )

        self.restore_listener_after_content()

        if (
            isinstance(
                result,
                dict,
            )
            and
            result.get(
                "completed",
                False,
            )
        ):

            self.finish_activity(
                status="completed",
                details={
                    "surah_number":
                        slots.get(
                            "surah_number"
                        ),

                    "surah_name":
                        slots.get(
                            "surah_name"
                        ),
                },
            )

            self.achievement_event(
                "quran_read_completed",
                surah_number=
                    slots.get(
                        "surah_number"
                    ),
                surah_name=
                    slots.get(
                        "surah_name"
                    ),
            )

        elif (
            isinstance(result, dict)
            and result.get("stopped", False)
        ):
            self.finish_activity(
                status="interrupted",
                details={"reason": "child_requested_stop"},
            )

        return result

    # =====================================================
    # QURAN MEMORIZE
    # =====================================================

    def handle_quran_memorize(
        self,
        slots,
    ):

        self.set_listening_profile("quran_medium")

        if not self.prepare_activity(
            "quran_memorize",
            details={
                "slots":
                    self.get_safe_slots(
                        slots
                    )
            },
        ):

            return

        request_text = (
            self.build_quran_request(
                "quran_memorize",
                slots,
            )
        )

        # أثناء صوت الشيخ يكون talking، والمايك يبقى فعالًا للتحكم،
        # وبعده يرجع listening لدور الطفل.
        self.pause_listener_for_content()
        self.set_face("talking")

        result = (
            self.quran.start_memorization(
                request_text=
                    request_text
            )
        )

        if self.quran.is_waiting_for_child() or self.quran.is_waiting_for_surah():
            self.set_listening_profile(
                self.get_quran_listening_profile()
            )
            self.restore_listener_after_content()
        elif self.quran.is_active():
            self.set_face("talking")
        else:
            self.restore_listener_after_content()

        if not isinstance(
            result,
            dict,
        ):

            return result

        if result.get(
            "stopped",
            False,
        ):
            self.finish_activity(
                status="interrupted",
                details={"reason": "child_requested_stop"},
            )
            self.restore_listener_after_content()
            return result

        if result.get(
            "already_mastered",
            False,
        ):

            self.finish_activity(
                status="completed",
                details={
                    "surah_number":
                        slots.get(
                            "surah_number"
                        ),

                    "surah_name":
                        slots.get(
                            "surah_name"
                        ),

                    "already_mastered":
                        True,
                },
            )

        return result

    # =====================================================
    # GOODBYE
    # =====================================================

    def handle_goodbye(self):

        if self.active_activity_id:

            self.finish_activity(
                status="interrupted",
                details={
                    "reason":
                        "goodbye"
                },
            )

        self.reset_activities()
        self.reset_brain_state()

        self.say(
            self.responses.goodbye(),
            resume_listening=False,
        )

        try:

            self.voice.disable()

        except Exception:

            pass

    # =====================================================
    # EXECUTE INTENT
    # =====================================================

    def execute_dialogue_intent(
        self,
        intent,
        slots,
    ):

        print()
        print("=" * 70)
        print(
            f"🚀 EXECUTING INTENT: {intent}"
        )
        print(
            f"📦 Slots: "
            f"{self.get_safe_slots(slots)}"
        )
        print("=" * 70)

        handlers = {

            # =================================================
            # ORIGINAL ACTIVITIES
            # =================================================

            "greeting":
                lambda:
                    self.handle_greeting(),

            "story":
                lambda:
                    self.handle_story(
                        slots
                    ),

            "riddle":
                lambda:
                    self.handle_riddle(
                        slots
                    ),

            "quran_read":
                lambda:
                    self.handle_quran_read(
                        slots
                    ),

            "quran_memorize":
                lambda:
                    self.handle_quran_memorize(
                        slots
                    ),

            "tasks":
                lambda:
                    self.handle_tasks(
                        slots
                    ),

            "morning_adhkar":
                lambda:
                    self.handle_morning_adhkar(
                        slots
                    ),

            "evening_adhkar":
                lambda:
                    self.handle_evening_adhkar(
                        slots
                    ),

            "sleep_adhkar":
                lambda:
                    self.handle_sleep_adhkar(
                        slots
                    ),

            "learning":
                lambda:
                    self.handle_learning(
                        slots
                    ),

            "help":
                lambda:
                    self.handle_help(),

            "goodbye":
                lambda:
                    self.handle_goodbye(),

            # =================================================
            # SOCIAL
            # =================================================

            "how_are_you":
                lambda:
                    self.handle_how_are_you(),

            "robot_name":
                lambda:
                    self.handle_robot_name(),

            "capabilities":
                lambda:
                    self.handle_capabilities(),

            "thanks":
                lambda:
                    self.handle_thanks(),

            "compliment":
                lambda:
                    self.handle_compliment(),

            "affection":
                lambda:
                    self.handle_affection(),

            # =================================================
            # CHILD EMOTIONS
            # =================================================

            "child_happy":
                lambda:
                    self.handle_child_happy(),

            "child_sad":
                lambda:
                    self.handle_child_sad(),

            "child_scared":
                lambda:
                    self.handle_child_scared(),

            "child_tired":
                lambda:
                    self.handle_child_tired(),

            "child_bored":
                lambda:
                    self.handle_child_bored(),

            # =================================================
            # DIALOGUE CONTROL
            # =================================================

            "yes":
                lambda:
                    self.handle_yes(),

            "no":
                lambda:
                    self.handle_no(),

            "continue":
                lambda:
                    self.handle_continue(),

            "change":
                lambda:
                    self.handle_change(),

            "wait":
                lambda:
                    self.handle_wait(),

            "repeat":
                lambda:
                    self.handle_repeat_signal(),

            "did_not_understand":
                lambda:
                    self.handle_did_not_understand(),
        }

        handler = handlers.get(
            intent
        )

        if handler is not None:

            try:

                return handler()

            except Exception as error:

                print()
                print(
                    f"❌ Intent handler error "
                    f"({intent}):"
                )
                print(
                    error
                )

                self.say(
                    self.responses.system_error()
                )

                return None

        print()
        print(
            f"⚠️ No handler for intent: "
            f"{intent}"
        )

        self.say(
            self.responses.unknown()
        )

    # =====================================================
    # PROCESS DIALOGUE RESULT
    # =====================================================

    def process_dialogue_result(
        self,
        result,
    ):

        if not isinstance(
            result,
            dict,
        ):

            return

        action = result.get(
            "action"
        )

        intent = result.get(
            "intent",
            "unknown",
        )

        slots = result.get(
            "slots",
            {},
        )

        nlu_result = result.get(
            "nlu"
        )

        self.last_intent = (
            intent or ""
        )

        if isinstance(
            nlu_result,
            dict,
        ):

            try:

                self.last_confidence = float(
                    nlu_result.get(
                        "confidence",
                        0.0,
                    )
                    or 0.0
                )

            except Exception:

                self.last_confidence = 0.0

            self.last_nlu_source = (
                nlu_result.get(
                    "source",
                    "",
                )
                or ""
            )

        print()
        print("=" * 70)
        print("🧠 MIMI BRAIN RESULT")
        print("=" * 70)
        print(
            f"Action     : {action}"
        )
        print(
            f"Intent     : {intent}"
        )
        print(
            f"Confidence : "
            f"{self.last_confidence:.3f}"
        )
        print(
            f"Source     : "
            f"{self.last_nlu_source}"
        )
        print(
            f"Slots      : "
            f"{self.get_safe_slots(slots)}"
        )
        print("=" * 70)

        # =================================================
        # ASK FOLLOW-UP
        # =================================================

        if action == "ask":

            response = (
                result.get(
                    "response"
                )
                or
                result.get(
                    "question"
                )
            )

            if response:

                self.say(
                    response
                )

            return

        # =================================================
        # UNIVERSAL
        # =================================================

        if action == "universal":

            command = slots.get(
                "command"
            )

            self.handle_global_command(
                command
            )

            return

        # =================================================
        # EXECUTE
        # =================================================

        if (
            action == "execute"
            and
            result.get(
                "ready_to_execute",
                False,
            )
        ):

            self.execute_dialogue_intent(
                intent,
                slots,
            )

    # =====================================================
    # NORMAL DIALOGUE INPUT
    # =====================================================

    def handle_dialogue_input(
        self,
        text,
    ):

        started = time.monotonic()

        try:

            result = (
                self.dialogue.process(
                    text
                )
            )

        except Exception as error:

            print()
            print(
                "❌ Dialogue Manager error:"
            )
            print(
                error
            )

            self.say(
                self.responses.system_error()
            )

            return

        elapsed = (
            time.monotonic()
            -
            started
        )

        print(
            f"⚡ Brain processing: "
            f"{elapsed:.3f}s"
        )

        self.process_dialogue_result(
            result
        )

    # =====================================================
    # QURAN CHILD INPUT
    # =====================================================

    def handle_quran_child_input(
        self,
        text,
    ):

        # handle_voice أظهر thinking بالفعل بعد وصول كلام الطفل.
        # الآن ننتقل مباشرة إلى talking أثناء رد/تلاوة Mimi.
        self.pause_listener_for_content()
        self.set_face("talking")

        self.set_listening_profile(
            self.get_quran_listening_profile()
        )
        result = (
            self.quran.handle_input(
                text
            )
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {}

        print()
        print(
            "📖 Quran result:"
        )
        print(
            result
        )

        if result.get(
            "stopped",
            False,
        ):
            self.finish_activity(
                status="interrupted",
                details={"reason": "child_requested_stop"},
            )
            self.restore_listener_after_content()
            return

        if result.get(
            "ayah_completed",
            False,
        ):

            self.achievement_event(
                "quran_ayah_mastered",
                surah_number=
                    result.get(
                        "surah_number"
                    ),
                ayah_number=
                    result.get(
                        "completed_ayah"
                    ),
                score=
                    result.get(
                        "score"
                    ),
            )

        if result.get(
            "surah_completed",
            False,
        ):

            self.finish_activity(
                status="completed",
                score=
                    result.get(
                        "score"
                    ),
                details={
                    "surah_number":
                        result.get(
                            "surah_number"
                        ),

                    "surah_name":
                        result.get(
                            "surah_name"
                        ),
                },
            )

            self.achievement_event(
                "quran_surah_completed",
                surah_number=
                    result.get(
                        "surah_number"
                    ),
                surah_name=
                    result.get(
                        "surah_name"
                    ),
            )

        elif result.get(
            "completed",
            False,
        ):

            self.finish_activity(
                status="completed",
                score=
                    result.get(
                        "score"
                    ),
            )

        if self.quran.is_waiting_for_child() or self.quran.is_waiting_for_surah():
            self.restore_listener_after_content()
        elif self.quran.is_active():
            self.set_face("talking")
        else:
            self.restore_listener_after_content()

    # =====================================================
    # ANSWER REACTION FACE
    # =====================================================

    def show_answer_reaction(
        self,
        correct,
    ):

        # نخلي ردّة الفعل واضحة وممتعة للطفل قبل السؤال التالي.
        expression = "love" if correct else "oops"
        duration = 1.60 if correct else 1.30

        self.set_face(expression)

        end_time = time.monotonic() + duration
        while time.monotonic() < end_time:
            try:
                self.face.update()
            except Exception:
                pass
            time.sleep(0.03)

    # =====================================================
    # LEARNING CHILD INPUT
    # =====================================================

    def handle_learning_child_input(
        self,
        text,
    ):

        # نحفظ السكور قبل الإجابة حتى نعرف إذا الجواب صح،
        # حتى لو LearningModule ما رجع مفتاح correct صراحة.
        try:
            before_state = (
                self.learning.get_state()
                or {}
            )
            before_score = int(
                before_state.get(
                    "score",
                    0,
                )
                or 0
            )
        except Exception:
            before_score = 0

        self.pause_listener_for_content()
        self.set_face("thinking")
        self.show_thinking_briefly()
        self.set_face("talking")

        result = (
            self.learning.handle_input(
                text
            )
        )

        if not isinstance(
            result,
            dict,
        ):
            result = {}

        # أولًا نظهر ردة الفعل على جواب الطفل.
        # بعد انتهائها مباشرة ننتقل إلى talking وننطق
        # السؤال التالي، حتى لا يظهر love/oops أثناء السؤال.
        if "correct" in result:

            self.show_answer_reaction(
                bool(
                    result.get(
                        "correct",
                        False,
                    )
                )
            )

        # قد يكون LearningModule جهز ردًا أو السؤال التالي.
        # ننطقه من MimiBot حتى يبقى وجه talking متحركًا
        # طوال مدة الكلام.
        pending_prompt = ""

        try:
            pending_prompt = (
                self.learning.pop_pending_prompt()
            )
        except Exception:
            pending_prompt = ""

        if pending_prompt:

            self.set_face(
                "talking"
            )

            self.speak_prompt_after_audio(
                pending_prompt
            )

        try:
            after_state = (
                self.learning.get_state()
                or {}
            )
            after_score = int(
                after_state.get(
                    "score",
                    before_score,
                )
                or 0
            )
        except Exception:
            after_score = before_score

        # إذا الموديول أعطانا correct نستعمله،
        # وإلا ارتفاع السكور يعني الإجابة كانت صحيحة.
        if "correct" in result:
            answer_correct = bool(
                result.get(
                    "correct"
                )
            )
        else:
            answer_correct = (
                after_score
                >
                before_score
            )

        # لا نظهر love/oops عند اختيار الموضوع نفسه؛
        # فقط عندما يكون هناك جواب لسؤال تعليمي.
        was_answer = not bool(
            result.get(
                "topic_selected",
                False,
            )
        )


        if not self.learning.is_active():

            score = result.get(
                "score",
                after_score,
            )

            self.finish_activity(
                status="completed",
                score=score,
                details={
                    "score": score
                },
            )

            self.achievement_event(
                "learning_completed",
                score=score,
            )

            self.restore_listener_after_content()

        elif (
            self.learning.is_waiting_for_topic()
            or
            self.learning.is_waiting_for_answer()
        ):

            self.set_listening_profile("short")
            self.restore_listener_after_content()

        else:

            self.set_face(
                "talking"
            )

    # =====================================================
    # STORY CHILD INPUT
    # =====================================================

    def handle_story_child_input(
        self,
        text,
    ):

        # handle_voice أظهر thinking بالفعل بعد وصول جواب الطفل.
        self.pause_listener_for_content()
        self.set_face("thinking")
        self.show_thinking_briefly()
        self.set_face("talking")

        result = (
            self.stories.answer(
                text
            )
        )

        if not self.stories.is_active():

            self.finish_activity(
                status="completed"
            )

            self.achievement_event(
                "story_completed"
            )

            # نهاية واضحة ومضمونة بعد القصة.
            # لا نترك المايك مغلقًا ولا Mimi ساكتة.
            self.set_face(
                "talking"
            )
            self.say(
                "حلوة القصة صح؟ شو بتحب نعمل هسا؟",
                resume_listening=True,
            )
            self.restore_listener_after_content()

        elif self.stories.is_waiting_for_answer():
            self.set_listening_profile("story_answer")
            self.restore_listener_after_content()

        else:
            self.set_face("talking")

        return result

    # =====================================================
    # RIDDLE CHILD INPUT
    # =====================================================

    def handle_riddle_child_input(
        self,
        text,
    ):

        self.pause_listener_for_content()
        self.set_face("thinking")
        self.show_thinking_briefly()
        self.set_face("talking")

        result = (
            self.riddles.answer(
                text
            )
        )

        if not isinstance(
            result,
            dict,
        ):
            self.restore_listener_after_content()
            return

        points = int(
            result.get(
                "points",
                0,
            )
            or 0
        )

        correct = bool(
            result.get(
                "correct",
                False,
            )
        )

        # بعد ما Mimi تعطي ردها الصوتي على اللغز:
        # صح = Love ❤️ ، غلط = Oops.
        self.show_answer_reaction(
            correct
        )

        if (
            correct
            and
            points > 0
        ):

            self.save_riddle_points(
                points
            )

        if (
            result.get(
                "finished",
                False,
            )
            or
            not self.riddles.is_active()
        ):

            self.finish_activity(
                status="completed",
                score=points,
                details={
                    "correct": correct,
                    "points": points,
                },
            )

        # سواء في لغز جديد أو انتهى النشاط،
        # نرجع للحالة الطبيعية ونفتح المايك.
        self.restore_listener_after_content()

    # =====================================================
    # HANDLE VOICE
    # =====================================================

    def handle_voice(self):

        while self.voice.has_command():

            text = self.voice.get_command()

            if not text:

                continue

            text = str(
                text
            ).strip()

            if not text:

                continue

            print()
            print("=" * 70)
            print(
                f"🎤 Mimi heard: {text}"
            )
            print("=" * 70)

            # =================================================
            # 1. SAFETY - ABSOLUTE PRIORITY
            # =================================================
            # Emergency phrases are checked before thinking/follow-up logic.

            try:
                priority_handler = getattr(
                    self.safety,
                    "handle_priority_voice",
                    self.safety.handle_voice,
                )

                safety_result = priority_handler(text)

            except Exception as error:

                print(
                    "⚠️ Safety voice error:",
                    error,
                )

                safety_result = {}

            if safety_result.get(
                "handled",
                False,
            ):

                self.process_safety_result(
                    safety_result
                )

                return

            self.show_thinking_briefly()

            # =================================================
            # STORY TYPE FOLLOW-UP
            # =================================================
            if self.waiting_for_story_type:
                if self.handle_story_type_answer(text):
                    return

            # =================================================
            # 2. GLOBAL COMMANDS
            # =================================================

            global_command = (
                self.detect_global_command(
                    text
                )
            )

            if global_command:

                self.handle_global_command(
                    global_command
                )

                return

            # =================================================
            # 3. ADHKAR REMINDER CONFIRMATION
            # =================================================
            # إذا Mimi سألت الطفل: "يلا نقرأ الأذكار سوا؟"
            # نعالج "يلا/نعم/لا" هنا قبل إرسال الكلام للـNLU.

            if self.waiting_for_adhkar_confirmation:

                if self.handle_adhkar_confirmation(
                    text
                ):
                    return

            # =================================================
            # 4. CONTROL DURING ACTIVITY
            # =================================================

            conversation_control = (
                self.detect_conversation_control(
                    text
                )
            )

            if conversation_control:

                if self.handle_conversation_control(
                    conversation_control
                ):

                    return

            # =================================================
            # STORY IS CURRENTLY NARRATING
            # =================================================
            #
            # أثناء سرد القصة وقبل الوصول إلى سؤال،
            # لا نرسل أي كلام عابر للـ NLU حتى لا يُفسر
            # مرة ثانية كأمر "story" ويعيد القصة من البداية.
            #
            # أوامر الإيقاف/الإعادة العامة تم فحصها فوق بالفعل.
            # =================================================

            if (
                self.stories.is_active()
                and
                not self.stories.is_waiting_for_answer()
            ):

                print()
                print(
                    "📚 Story is narrating - "
                    "ignoring stray voice input."
                )

                return

            # =================================================
            # 4. QURAN RECITATION
            # =================================================
            #
            # القرآن لا يذهب للـintent classifier أثناء
            # التسميع.
            # =================================================

            if (
                self.quran.is_waiting_for_child()
                or
                self.quran.is_waiting_for_surah()
            ):

                self.handle_quran_child_input(
                    text
                )

                return

            # =================================================
            # 5. LEARNING ANSWER
            # =================================================

            if (
                self.learning.is_waiting_for_topic()
                or
                self.learning.is_waiting_for_answer()
            ):

                self.handle_learning_child_input(
                    text
                )

                return

            # =================================================
            # 6. STORY ANSWER
            # =================================================

            if (
                self.stories.is_active()
                and
                self.stories.is_waiting_for_answer()
            ):

                self.handle_story_child_input(
                    text
                )

                return

            # =================================================
            # 7. RIDDLE ANSWER
            # =================================================

            if self.riddles.is_active():

                self.handle_riddle_child_input(
                    text
                )

                return

            # =================================================
            # 8. NLU V3
            # =================================================

            if (
                self.current_session
                is not None
                or
                self.guest_mode
            ):

                self.handle_dialogue_input(
                    text
                )

                return

    # =====================================================
    # FACE RECOGNITION
    # =====================================================

    def handle_recognition(
        self,
        result,
    ):

        if not result:

            return

        name = result.get(
            "name"
        )

        known = bool(
            result.get(
                "known",
                False,
            )
        )

        if known:

            self.unknown_count = 0

            # أول مرة أو طفل مختلف: حمّل الجلسة واعمل الترحيب.
            if (
                name
                and
                name
                !=
                self.current_face_id
            ):

                self.person_present = True

                self.load_child(
                    name
                )

                return

            # نفس الطفل رجع بعد ما ابتعد عن الكاميرا:
            # لا نعيد الترحيب ولا نعيد تحميل الجلسة.
            if (
                name
                and
                name
                ==
                self.current_face_id
            ):

                was_absent = (
                    not self.person_present
                )

                self.person_present = True

                if was_absent:

                    try:
                        self.voice.clear_commands()
                    except Exception:
                        pass

                    try:
                        self.voice.enable()
                    except Exception:
                        pass

                    if not self.has_active_content():
                        self.set_face(
                            "listening"
                        )

                    print()
                    print(
                        "👋 Child returned - session resumed without greeting."
                    )

            return

        # شخص غير مسجل مر أمام الكاميرا:
        # لا نبدأ حوارًا ولا نسأل "شو بتحب نعمل؟".
        # هذا مهم للديمو حتى لا تتفاعل Mimi مع كل شخص يمر.
        self.unknown_count = 0

        print()
        print(
            "👤 Unknown face ignored - no automatic greeting."
        )

        # إذا لا يوجد طفل معروف في الجلسة، تبقى Mimi هادئة.
        if (
            self.current_session is None
            and
            not self.guest_mode
        ):
            try:
                self.voice.disable()
            except Exception:
                pass

            try:
                self.voice.clear_commands()
            except Exception:
                pass

            self.set_face(
                "idle"
            )

        return

    # =====================================================
    # DRAW SCREEN
    # =====================================================

    def draw_screen(
        self,
        frame,
        face,
    ):

        if face is not None:

            if self.current_session:

                label = (
                    self.current_session
                    .get(
                        "child",
                        {},
                    )
                    .get(
                        "name",
                        "Child",
                    )
                )

                color = (
                    0,
                    255,
                    0,
                )

            elif self.guest_mode:

                label = "Guest"

                color = (
                    0,
                    165,
                    255,
                )

            else:

                label = "Checking..."

                color = (
                    255,
                    255,
                    255,
                )

            try:

                self.vision.draw_face(
                    frame,
                    face,
                    label,
                    color,
                )

            except Exception:

                pass

        # =================================================
        # PERSON
        # =================================================

        if self.current_session:

            name = (
                self.current_session
                .get(
                    "child",
                    {},
                )
                .get(
                    "name",
                    "Child",
                )
            )

            gender = self.get_current_gender()
            gender_label = "👧" if gender == "girl" else "👦" if gender == "boy" else ""
            mode_text = (
                f"CHILD: {name} {gender_label}"
            )

        elif self.guest_mode:

            mode_text = (
                "GUEST MODE"
            )

        else:

            mode_text = (
                "WAITING..."
            )

        # =================================================
        # ACTIVITY
        # =================================================

        if self.safety.is_active():

            activity_text = (
                "!!! SAFETY ALERT !!!"
            )

        elif self.quran.is_memorizing():

            state = (
                self.quran.get_state()
            )

            activity_text = (
                f"QURAN MEM "
                f"A{state.get('current_ayah', 1)} "
                f"{state.get('current_repeat', 0)}/"
                f"{state.get('repeat_target', 3)}"
            )

        elif self.quran.is_reading():

            activity_text = (
                "QURAN READ"
            )

        elif self.learning.is_active():

            state = (
                self.learning.get_state()
            )

            activity_text = (
                f"LEARNING "
                f"{state.get('topic') or 'SELECT'} "
                f"SCORE:{state.get('score', 0)}"
            )

        elif self.adhkar.is_morning():

            activity_text = (
                "MORNING ADHKAR"
            )

        elif self.adhkar.is_evening():

            activity_text = (
                "EVENING ADHKAR"
            )

        elif self.adhkar.is_sleep():

            activity_text = (
                "SLEEP ADHKAR"
            )

        elif self.tasks.is_active():

            activity_text = (
                "TASK MODE"
            )

        elif self.stories.is_active():

            activity_text = (
                "STORY MODE"
            )

        elif self.riddles.is_active():

            activity_text = (
                "RIDDLE MODE"
            )

        elif (
            self.dialogue.context
            .is_waiting()
        ):

            waiting_for = (
                self.dialogue
                .context
                .waiting_for
            )

            activity_text = (
                f"WAITING: {waiting_for}"
            )

        elif self.last_intent:

            activity_text = (
                f"NLU: {self.last_intent} "
                f"{self.last_confidence:.2f}"
            )

        elif (
            self.current_session
            or
            self.guest_mode
        ):

            activity_text = (
                "LISTENING"
            )

        else:

            activity_text = ""

        points = (
            self.current_total_points
            if self.current_session
            else None
        )

        try:

            self.vision.draw_status(
                frame,
                mode_text=
                    mode_text,
                activity_text=
                    activity_text,
                points=
                    points,
            )

        except Exception:

            pass

    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        self.start()

        self.running = True

        try:

            while self.running:

                self.process_pending_safety_results()

                # =================================================
                # FACE SCREEN
                # =================================================
                # وجه Mimi هو الذي يظهر على الشاشة.
                # لا نعرض فيديو الكاميرا.

                if not self.face.update():

                    self.running = False
                    break

                # =================================================
                # VISION - BACKGROUND ONLY
                # =================================================

                result = (
                    self.vision.process()
                )

                if result is not None:

                    (
                        frame,
                        detected_face,
                        recognition_result,
                    ) = result

                    now = (
                        time.monotonic()
                    )

                    # =================================================
                    # FACE PRESENT
                    # =================================================

                    if detected_face is not None:

                        self.last_face_seen_time = now

                        recognition_time = getattr(
                            self.vision,
                            "last_recognition_time",
                            0.0,
                        )

                        if (
                            recognition_time > 0
                            and
                            recognition_time
                            !=
                            self.last_processed_recognition_time
                        ):

                            self.last_processed_recognition_time = (
                                recognition_time
                            )

                            self.handle_recognition(
                                recognition_result
                            )

                    # =================================================
                    # FACE LOST
                    # =================================================

                    else:

                        if (
                            self.last_face_seen_time > 0
                            and
                            now
                            -
                            self.last_face_seen_time
                            >=
                            PRESENCE_LOST_SECONDS
                        ):

                            if (
                                self.current_session
                                or
                                self.guest_mode
                                or
                                self.current_face_id
                            ):

                                # لا نوقف قصة/قرآن/نشاط فقط لأن الطفل
                                # أبعد وجهه عن الكاميرا. النشاط يظل شغال
                                # إلى أن ينتهي أو يقول الطفل أمر Stop.
                                if self.has_active_content():

                                    # نحافظ على الجلسة والمايك والنشاط.
                                    # فقط لا نعيد التعرف كل فريم.
                                    self.last_processed_recognition_time = (
                                        0.0
                                    )

                                else:

                                    self.clear_person()

                                    self.last_processed_recognition_time = (
                                        0.0
                                    )

                                    self.set_face(
                                        "idle"
                                    )

                # =================================================
                # ADHKAR CLOCK / POSTPONED REMINDER
                # =================================================

                now_clock_check = time.monotonic()

                if (
                    now_clock_check
                    - self.last_adhkar_clock_check
                    >= self.adhkar_clock_check_interval
                ):
                    self.last_adhkar_clock_check = now_clock_check
                    self.check_adhkar_reminder()

                # =================================================
                # VOICE
                # =================================================

                self.update_listening_profile_for_state()
                self.handle_voice()
                self.process_pending_safety_results()

                time.sleep(
                    0.01
                )

        except KeyboardInterrupt:

            print()
            print(
                "🛑 Mimi stopped by user."
            )

        finally:

            self.close()

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        print()
        print("=" * 70)
        print("🧹 CLOSING MIMI BOT")
        print("=" * 70)

        self.running = False

        if self.active_activity_id:

            self.finish_activity(
                status="interrupted",
                details={
                    "reason":
                        "application_closed"
                },
            )

        try:

            self.face.close()

        except Exception:

            pass

        modules = [
            self.safety,
            self.stories,
            self.riddles,
            self.quran,
            self.adhkar,
            self.learning,
            self.tasks,
            self.achievements,
            self.dialogue,
            self.voice,
            self.vision,
        ]

        for module in modules:

            try:

                module.close()

            except Exception:

                pass

        try:

            close_connection()

        except Exception:

            pass

        print()
        print("=" * 70)
        print(
            "✅ Mimi Bot closed safely."
        )
        print("=" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    mimi = MimiBot()

    mimi.run()


if __name__ == "__main__":

    main()