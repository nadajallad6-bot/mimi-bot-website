import time
from collections import deque

from src.nlu.child_language_normalizer import (
    ChildLanguageNormalizer,
)

from src.nlu.slot_extractor import (
    SlotExtractor,
)


# =========================================================
# SETTINGS
# =========================================================

CONTEXT_TIMEOUT_SECONDS = 120

MAX_HISTORY = 12


# =========================================================
# MIMI INTERACTION MEMORY V2
# =========================================================


class InteractionMemory:

    def __init__(
        self,
        timeout_seconds=CONTEXT_TIMEOUT_SECONDS,
    ):

        self.timeout_seconds = float(
            timeout_seconds
        )

        self.normalizer = (
            ChildLanguageNormalizer()
        )

        self.slots = (
            SlotExtractor()
        )

        self.history = deque(
            maxlen=MAX_HISTORY
        )

        self.reset()

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.active = False

        self.active_intent = None

        self.active_topic = None

        self.waiting_for = None

        self.pending_slots = {}

        self.last_child_text = ""

        self.last_response = ""

        self.last_intent = None

        self.last_slots = {}

        self.last_activity = None

        self.updated_at = (
            time.monotonic()
        )

    # =====================================================
    # TOUCH
    # =====================================================

    def touch(self):

        self.updated_at = (
            time.monotonic()
        )

    # =====================================================
    # EXPIRED
    # =====================================================

    def is_expired(self):

        if not self.active:

            return False

        elapsed = (
            time.monotonic()
            -
            self.updated_at
        )

        return (
            elapsed
            >
            self.timeout_seconds
        )

    # =====================================================
    # AUTO CLEANUP
    # =====================================================

    def cleanup_if_expired(self):

        if self.is_expired():

            print(
                "🧹 Mimi dialogue context expired."
            )

            self.reset()

            return True

        return False

    # =====================================================
    # NORMALIZE
    # =====================================================

    def normalize(
        self,
        text,
    ):

        try:

            result = (
                self.normalizer.normalize(
                    text
                )
            )

            return (
                result.get(
                    "canonical"
                )
                or
                result.get(
                    "normalized"
                )
                or
                ""
            )

        except Exception:

            return str(
                text
            ).strip()

    # =====================================================
    # RECORD CHILD
    # =====================================================

    def record_child(
        self,
        text,
        intent=None,
        slots=None,
    ):

        text = str(
            text
        ).strip()

        self.last_child_text = text

        if intent is not None:

            self.last_intent = (
                intent
            )

        if isinstance(
            slots,
            dict,
        ):

            self.last_slots = dict(
                slots
            )

        self.history.append(
            {
                "speaker":
                    "child",

                "text":
                    text,

                "intent":
                    intent,

                "slots":
                    dict(
                        slots or {}
                    ),

                "time":
                    time.monotonic(),
            }
        )

        self.touch()

    # =====================================================
    # RECORD MIMI
    # =====================================================

    def record_mimi(
        self,
        text,
    ):

        text = str(
            text
        ).strip()

        if not text:

            return

        self.last_response = text

        self.history.append(
            {
                "speaker":
                    "mimi",

                "text":
                    text,

                "time":
                    time.monotonic(),
            }
        )

        self.touch()

    # =====================================================
    # START CONTEXT
    # =====================================================

    def start_context(
        self,
        intent,
        slots=None,
        topic=None,
    ):

        self.active = True

        self.active_intent = (
            intent
        )

        self.active_topic = (
            topic
        )

        self.pending_slots = dict(
            slots or {}
        )

        self.waiting_for = None

        self.touch()

    # =====================================================
    # SET WAITING
    # =====================================================

    def ask_for(
        self,
        waiting_for,
        intent=None,
        slots=None,
    ):

        self.active = True

        self.waiting_for = (
            waiting_for
        )

        if intent is not None:

            self.active_intent = (
                intent
            )

        if isinstance(
            slots,
            dict,
        ):

            self.pending_slots.update(
                slots
            )

        self.touch()

    # =====================================================
    # CLEAR WAITING
    # =====================================================

    def clear_waiting(self):

        self.waiting_for = None

        self.touch()

    # =====================================================
    # UPDATE SLOT
    # =====================================================

    def set_slot(
        self,
        key,
        value,
    ):

        if value is None:

            return

        self.pending_slots[
            key
        ] = value

        self.touch()

    # =====================================================
    # SET ACTIVITY
    # =====================================================

    def set_activity(
        self,
        activity,
    ):

        self.last_activity = (
            activity
        )

        self.touch()

    # =====================================================
    # SHORT YES / NO
    # =====================================================

    def detect_yes_no(
        self,
        text,
    ):

        text = (
            self.normalize(
                text
            )
        )

        yes_values = {
            "اه",
            "ايوه",
            "ايوا",
            "نعم",
            "تمام",
            "اوك",
            "ماشي",
            "يلا",
            "اكيد",
        }

        no_values = {
            "لا",
            "لأ",
            "مش بدي",
            "ما بدي",
            "مش هيك",
        }

        if text in yes_values:

            return "yes"

        if text in no_values:

            return "no"

        return None

    # =====================================================
    # DIALOGUE COMMAND
    # =====================================================

    def detect_control(
        self,
        text,
    ):

        text = (
            self.normalize(
                text
            )
        )

        mapping = {

            "continue": {
                "كملي",
                "كمل",
                "واصلي",
                "وبعدين",
                "بعدها",
            },

            "repeat": {
                "عيدي",
                "عيد",
                "كرري",
                "كرر",
                "مره ثانيه",
                "كمان مره",
                "شو قلتي",
            },

            "change": {
                "غيري",
                "غير",
                "بدي غيرها",
                "مش هاي",
                "اشي ثاني",
                "شي ثاني",
            },

            "wait": {
                "استني",
                "استنا",
                "لحظه",
                "شوي",
                "اصبري",
            },

            "stop": {
                "وقف",
                "وقفي",
                "توقف",
                "خلص",
            },

            "back": {
                "ارجعي",
                "ارجع",
                "رجع",
            },
        }

        for (
            command,
            values,
        ) in mapping.items():

            if text in values:

                return command

        return None

    # =====================================================
    # QURAN MODE FOLLOWUP
    # =====================================================

    def extract_quran_mode(
        self,
        text,
    ):

        text = (
            self.normalize(
                text
            )
        )

        words = set(
            text.split()
        )

        memorize_words = {
            "احفظ",
            "حفظ",
            "نحفظ",
            "تسميع",
            "سمعلي",
            "راجع",
            "مراجعه",
        }

        read_words = {
            "اقرا",
            "اقري",
            "نقرا",
            "قراءه",
            "اسمع",
            "اسمعيني",
            "شغلي",
        }

        if (
            words
            &
            memorize_words
        ):

            return "memorize"

        if (
            words
            &
            read_words
        ):

            return "read"

        return None

    # =====================================================
    # LEARNING FOLLOWUP
    # =====================================================

    def extract_learning_topic(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        words = set(
            normalized.split()
        )

        topics = {

            "colors": {
                "الوان",
                "الالوان",
                "لون",
            },

            "numbers": {
                "ارقام",
                "الارقام",
                "اعداد",
                "الاعداد",
                "رقم",
            },

            "letters": {
                "حروف",
                "الحروف",
                "حرف",
            },

            "addition": {
                "جمع",
                "الجمع",
                "نجمع",
            },
        }

        for (
            topic,
            values,
        ) in topics.items():

            if (
                words
                &
                values
            ):

                return topic

        return None

    # =====================================================
    # STORY TYPE FOLLOWUP
    # =====================================================

    def extract_story_type(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        words = set(
            normalized.split()
        )

        mappings = {

            "animals": {
                "حيوانات",
                "حيوان",
                "قطه",
                "قطة",
                "اسد",
                "ارنب",
            },

            "funny": {
                "مضحكه",
                "مضحكة",
                "تضحك",
                "ضحك",
                "مضحك",
            },

            "educational": {
                "تعليميه",
                "تعليمية",
                "تعليمي",
                "مفيده",
                "مفيدة",
                "مفيد",
            },
        }

        for (
            story_type,
            values,
        ) in mappings.items():

            if (
                words
                &
                values
            ):

                return story_type

        return None

    # =====================================================
    # SURAH FOLLOWUP
    # =====================================================

    def extract_surah(
        self,
        text,
    ):

        try:

            result = (
                self.slots.extract(
                    text
                )
            )

        except Exception:

            return None

        number = (
            result.get(
                "surah_number"
            )
        )

        if number is None:

            return None

        return {
            "surah_number":
                number,

            "surah_name":
                result.get(
                    "surah_name"
                ),

            "surah_confidence":
                result.get(
                    "surah_confidence"
                ),
        }

    # =====================================================
    # RESOLVE FOLLOWUP
    # =====================================================

    def resolve_followup(
        self,
        text,
    ):

        self.cleanup_if_expired()

        if not self.active:

            return {
                "matched":
                    False
            }

        text = str(
            text
        ).strip()

        if not text:

            return {
                "matched":
                    False
            }

        # =================================================
        # GLOBAL CONTROL FIRST
        # =================================================

        control = (
            self.detect_control(
                text
            )
        )

        if control:

            return {
                "matched":
                    True,

                "type":
                    "control",

                "value":
                    control,
            }

        # =================================================
        # YES / NO
        # =================================================

        yes_no = (
            self.detect_yes_no(
                text
            )
        )

        if (
            yes_no
            and
            self.waiting_for
            in {
                "confirmation",
                "yes_no",
            }
        ):

            return {
                "matched":
                    True,

                "type":
                    "yes_no",

                "value":
                    yes_no,
            }

        # =================================================
        # QURAN MODE
        # =================================================

        if (
            self.waiting_for
            ==
            "quran_mode"
        ):

            mode = (
                self.extract_quran_mode(
                    text
                )
            )

            if mode:

                self.set_slot(
                    "quran_mode",
                    mode,
                )

                self.clear_waiting()

                return {
                    "matched":
                        True,

                    "type":
                        "slot",

                    "slot":
                        "quran_mode",

                    "value":
                        mode,

                    "intent":
                        self.active_intent,

                    "slots":
                        dict(
                            self.pending_slots
                        ),
                }

        # =================================================
        # QURAN SURAH
        # =================================================

        if (
            self.waiting_for
            ==
            "surah"
        ):

            surah = (
                self.extract_surah(
                    text
                )
            )

            if surah:

                for (
                    key,
                    value,
                ) in surah.items():

                    if value is not None:

                        self.set_slot(
                            key,
                            value,
                        )

                self.clear_waiting()

                return {
                    "matched":
                        True,

                    "type":
                        "slot",

                    "slot":
                        "surah",

                    "value":
                        surah,

                    "intent":
                        self.active_intent,

                    "slots":
                        dict(
                            self.pending_slots
                        ),
                }

        # =================================================
        # LEARNING TOPIC
        # =================================================

        if (
            self.waiting_for
            ==
            "learning_topic"
        ):

            topic = (
                self.extract_learning_topic(
                    text
                )
            )

            if topic:

                self.set_slot(
                    "learning_topic",
                    topic,
                )

                self.clear_waiting()

                return {
                    "matched":
                        True,

                    "type":
                        "slot",

                    "slot":
                        "learning_topic",

                    "value":
                        topic,

                    "intent":
                        self.active_intent,

                    "slots":
                        dict(
                            self.pending_slots
                        ),
                }

        # =================================================
        # STORY TYPE
        # =================================================

        if (
            self.waiting_for
            ==
            "story_type"
        ):

            story_type = (
                self.extract_story_type(
                    text
                )
            )

            if story_type:

                self.set_slot(
                    "story_type",
                    story_type,
                )

                self.clear_waiting()

                return {
                    "matched":
                        True,

                    "type":
                        "slot",

                    "slot":
                        "story_type",

                    "value":
                        story_type,

                    "intent":
                        self.active_intent,

                    "slots":
                        dict(
                            self.pending_slots
                        ),
                }

        return {
            "matched":
                False
        }

    # =====================================================
    # SNAPSHOT
    # =====================================================

    def get_state(self):

        self.cleanup_if_expired()

        return {
            "active":
                self.active,

            "active_intent":
                self.active_intent,

            "active_topic":
                self.active_topic,

            "waiting_for":
                self.waiting_for,

            "pending_slots":
                dict(
                    self.pending_slots
                ),

            "last_intent":
                self.last_intent,

            "last_slots":
                dict(
                    self.last_slots
                ),

            "last_activity":
                self.last_activity,

            "last_child_text":
                self.last_child_text,

            "last_response":
                self.last_response,
        }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    memory = (
        InteractionMemory()
    )

    print()
    print("=" * 70)
    print("🧠 MIMI INTERACTION MEMORY V2")
    print("=" * 70)

    # =====================================================
    # QURAN EXAMPLE
    # =====================================================

    print()
    print("TEST: Quran conversation")

    memory.start_context(
        intent="quran",
    )

    memory.ask_for(
        "quran_mode"
    )

    print(
        "Child: نحفظ"
    )

    print(
        memory.resolve_followup(
            "نحفظ"
        )
    )

    memory.active_intent = (
        "quran_memorize"
    )

    memory.ask_for(
        "surah"
    )

    print(
        "Child: الفلق"
    )

    print(
        memory.resolve_followup(
            "الفلق"
        )
    )

    # =====================================================
    # LEARNING EXAMPLE
    # =====================================================

    print()
    print("TEST: Learning conversation")

    memory.reset()

    memory.start_context(
        intent="learning"
    )

    memory.ask_for(
        "learning_topic"
    )

    print(
        "Child: الالوان"
    )

    print(
        memory.resolve_followup(
            "الالوان"
        )
    )

    # =====================================================
    # STORY EXAMPLE
    # =====================================================

    print()
    print("TEST: Story conversation")

    memory.reset()

    memory.start_context(
        intent="story"
    )

    memory.ask_for(
        "story_type"
    )

    print(
        "Child: حيوانات"
    )

    print(
        memory.resolve_followup(
            "حيوانات"
        )
    )

    # =====================================================
    # CONTROL
    # =====================================================

    print()
    print("TEST: Controls")

    memory.start_context(
        intent="story"
    )

    print(
        memory.resolve_followup(
            "استني"
        )
    )

    print(
        memory.resolve_followup(
            "كملي"
        )
    )

    print(
        memory.resolve_followup(
            "غيري"
        )
    )

    print()
    print("=" * 70)
    print(
        memory.get_state()
    )
