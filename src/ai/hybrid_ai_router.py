from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.ai.gemini_open_domain_ai import (
    GeminiOpenDomainAI,
)


# =========================================================
# MIMI HYBRID AI ROUTER
# =========================================================
#
# الهدف:
#
# LOCAL MIMI AI
#     مسؤول عن أوامر الروبوت والأنشطة
#
# OPEN DOMAIN AI
#     مسؤول عن الأسئلة العامة والمحادثة المفتوحة
#
#
# مثال:
#
# بدي قصة
# -> LOCAL
#
# بدي أحفظ سورة الملك
# -> LOCAL
#
# ليش السما زرقا؟
# -> OPEN DOMAIN
#
# مين اخترع الطيارة؟
# -> OPEN DOMAIN
#
# ساعدني
# -> NEVER OPEN DOMAIN
#    SafetyModule يتعامل معها
#
# =========================================================


@dataclass
class RouteDecision:

    route: str

    reason: str

    intent: Optional[str] = None

    confidence: float = 0.0

    source: Optional[str] = None

    use_open_domain: bool = False

    nlu_result: Optional[
        Dict[str, Any]
    ] = None


# =========================================================
# ROUTER
# =========================================================


class HybridAIRouter:

    def __init__(
        self,
        open_domain_ai=None,
        weak_local_threshold=0.55,
    ):

        self.open_domain_ai = (
    open_domain_ai
    if open_domain_ai is not None
    else GeminiOpenDomainAI()
)

        self.weak_local_threshold = float(
            weak_local_threshold
        )

        self.started = False

        # =================================================
        # LOCAL MIMI INTENTS
        # =================================================

        self.activity_intents = {
            "story",
            "riddle",
            "quran",
            "quran_read",
            "quran_memorize",
            "tasks",
            "morning_adhkar",
            "evening_adhkar",
            "learning",
            "help",
            "goodbye",
        }

        # =================================================
        # SOCIAL INTENTS
        # =================================================

        self.social_intents = {
            "greeting",
            "how_are_you",
            "robot_name",
            "capabilities",
            "thanks",
            "compliment",
            "affection",
        }

        # =================================================
        # EMOTION INTENTS
        # =================================================

        self.emotion_intents = {
            "child_happy",
            "child_sad",
            "child_scared",
            "child_tired",
            "child_bored",
        }

        # =================================================
        # DIALOGUE INTENTS
        # =================================================

        self.dialogue_intents = {
            "yes",
            "no",
            "continue",
            "change",
            "wait",
            "repeat",
            "did_not_understand",
            "universal_command",
        }

        # =================================================
        # TRUSTED SOURCES
        # =================================================
        #
        # هاي مصادر نثق فيها أكثر من prediction عام.
        # =================================================

        self.trusted_local_sources = {
            "strong_rule",
            "conversation_exact",
            "conversation_tokens",
        }

        # =================================================
        # LOCAL KEYWORDS
        # =================================================

        self.local_keywords = {

            # Quran
            "قران",
            "القران",
            "سوره",
            "سورة",
            "ايه",
            "اية",
            "ايات",
            "آيات",
            "احفظ",
            "نحفظ",
            "تسميع",

            # Stories
            "قصه",
            "قصة",
            "قصص",
            "حكايه",
            "حكاية",

            # Riddles
            "لغز",
            "الغاز",
            "ألغاز",
            "فزوره",
            "فزورة",

            # Learning
            "اتعلم",
            "تعلم",
            "نتعلم",
            "الوان",
            "الألوان",
            "ارقام",
            "الأرقام",
            "حروف",
            "الجمع",

            # Tasks
            "مهامي",
            "مهام",
            "واجباتي",
            "واجب",

            # Adhkar
            "اذكار",
            "أذكار",
        }

        # =================================================
        # OPEN DOMAIN QUESTION SIGNALS
        # =================================================

        self.general_question_phrases = {
            "ليش",
            "لماذا",
            "شو يعني",
            "ايش يعني",
            "ما معنى",
            "مين اخترع",
            "من اخترع",
            "كيف بصير",
            "كيف بيصير",
            "كيف يعمل",
            "كيف بتشتغل",
            "وين",
            "اين",
            "أين",
            "متى",
            "قديش",
            "كم عمر",
            "شو هو",
            "شو هي",
            "ما هو",
            "ما هي",
            "احكيلي عن",
            "خبريني عن",
            "عرفيني عن",
        }

        # =================================================
        # SAFETY
        # =================================================

        self.safety_phrases = {
            "ساعدني",
            "الحقني",
            "الحقوني",
            "انا بخطر",
            "أنا بخطر",
            "في خطر",
            "خايف كثير",
            "خايفة كثير",
        }

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:

            return True

        print()
        print("=" * 70)
        print(
            "🧠 STARTING MIMI HYBRID AI ROUTER"
        )
        print("=" * 70)

        # Open AI is optional.
        #
        # Mimi still works without internet/API.

        try:

            self.open_domain_ai.start()

        except Exception as error:

            print(
                "⚠️ Open-domain AI unavailable:"
            )

            print(
                error
            )

        self.started = True

        print(
            "✅ Local-first routing ready."
        )

        print(
            "✅ Open-domain fallback ready."
        )

        print("=" * 70)

        return True

    # =====================================================
    # NORMALIZE SIMPLE
    # =====================================================

    def normalize(
        self,
        text,
    ):

        text = str(
            text
            or ""
        )

        text = (
            text
            .strip()
            .lower()
        )

        replacements = {
            "أ":
                "ا",

            "إ":
                "ا",

            "آ":
                "ا",

            "ة":
                "ه",

            "ى":
                "ي",
        }

        for (
            old,
            new,
        ) in replacements.items():

            text = (
                text.replace(
                    old,
                    new
                )
            )

        while "  " in text:

            text = (
                text.replace(
                    "  ",
                    " "
                )
            )

        return text

    # =====================================================
    # CONTAINS LOCAL KEYWORD
    # =====================================================

    def has_local_keyword(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        tokens = set(
            normalized.split()
        )

        for keyword in (
            self.local_keywords
        ):

            normalized_keyword = (
                self.normalize(
                    keyword
                )
            )

            # Exact token for short keywords.

            if (
                " "
                not in normalized_keyword
                and
                normalized_keyword
                in tokens
            ):

                return True

            # Phrase.

            if (
                " "
                in normalized_keyword
                and
                normalized_keyword
                in normalized
            ):

                return True

        return False

    # =====================================================
    # GENERAL QUESTION
    # =====================================================

    def looks_like_general_question(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        for phrase in (
            self.general_question_phrases
        ):

            phrase = (
                self.normalize(
                    phrase
                )
            )

            if (
                normalized.startswith(
                    phrase
                )
                or
                f" {phrase} "
                in
                f" {normalized} "
            ):

                return True

        return False

    # =====================================================
    # SAFETY TEXT
    # =====================================================

    def looks_like_safety(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        for phrase in (
            self.safety_phrases
        ):

            if (
                self.normalize(
                    phrase
                )
                in
                normalized
            ):

                return True

        return False

    # =====================================================
    # SLOT PRESENT
    # =====================================================

    def has_meaningful_local_slot(
        self,
        slots,
    ):

        if not isinstance(
            slots,
            dict,
        ):

            return False

        important = {
            "surah_number",
            "quran_mode",
            "learning_topic",
            "story_type",
            "task_action",
            "universal_command",
        }

        for key in important:

            if (
                slots.get(
                    key
                )
                is not None
            ):

                return True

        return False

    # =====================================================
    # LOCAL INTENT
    # =====================================================

    def is_known_local_intent(
        self,
        intent,
    ):

        return (
            intent
            in
            self.activity_intents
            or
            intent
            in
            self.social_intents
            or
            intent
            in
            self.emotion_intents
            or
            intent
            in
            self.dialogue_intents
        )

    # =====================================================
    # DECIDE
    # =====================================================

    def decide(
        self,
        text,
        nlu_result,
        *,
        dialogue_waiting=False,
        activity_active=False,
    ):

        text = str(
            text
            or ""
        ).strip()

        nlu_result = (
            nlu_result
            if isinstance(
                nlu_result,
                dict,
            )
            else {}
        )

        intent = (
            nlu_result.get(
                "intent"
            )
            or
            "unknown"
        )

        try:

            confidence = float(
                nlu_result.get(
                    "confidence",
                    0.0,
                )
                or 0.0
            )

        except Exception:

            confidence = 0.0

        source = (
            nlu_result.get(
                "source"
            )
        )

        slots = (
            nlu_result.get(
                "slots"
            )
            or
            {}
        )

        needs_clarification = bool(
            nlu_result.get(
                "needs_clarification",
                False,
            )
        )

        # =================================================
        # 1. SAFETY NEVER GOES TO CLOUD AI
        # =================================================

        if self.looks_like_safety(
            text
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "safety_text",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 2. ACTIVE DIALOGUE MUST STAY LOCAL
        # =================================================
        #
        # Example:
        #
        # Mimi: أي سورة؟
        # Child: الملك
        #
        # "الملك" must NOT go to ChatGPT.
        # =================================================

        if dialogue_waiting:

            return RouteDecision(
                route=
                    "local",

                reason=
                    "dialogue_waiting",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 3. ACTIVE ACTIVITY STAYS LOCAL
        # =================================================

        if activity_active:

            return RouteDecision(
                route=
                    "local",

                reason=
                    "activity_active",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 4. STRONG LOCAL SLOTS
        # =================================================

        if self.has_meaningful_local_slot(
            slots
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "local_slot",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 5. STRONG LOCAL SOURCE
        # =================================================

        if (
            source
            in
            self.trusted_local_sources
            and
            self.is_known_local_intent(
                intent
            )
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "trusted_local_source",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 6. LOCAL KEYWORD
        # =================================================

        if (
            self.has_local_keyword(
                text
            )
            and
            self.is_known_local_intent(
                intent
            )
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "local_keyword",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 7. SOCIAL / EMOTIONS STAY LOCAL
        # =================================================

        if (
            intent
            in
            self.social_intents
            or
            intent
            in
            self.emotion_intents
            or
            intent
            in
            self.dialogue_intents
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "local_conversation",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 8. UNKNOWN → OPEN DOMAIN
        # =================================================

        if intent == "unknown":

            return RouteDecision(
                route=
                    "open_domain",

                reason=
                    "unknown_local_intent",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    True,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 9. GENERAL QUESTION → OPEN DOMAIN
        # =================================================
        #
        # Critical:
        #
        # Local classifier may say:
        #
        # story 0.31
        #
        # for:
        #
        # "ليش السما زرقا؟"
        #
        # We don't want that false positive.
        # =================================================

        if (
            self.looks_like_general_question(
                text
            )
            and
            not self.has_local_keyword(
                text
            )
        ):

            return RouteDecision(
                route=
                    "open_domain",

                reason=
                    "general_question",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    True,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 10. WEAK CUSTOM AI WITHOUT LOCAL EVIDENCE
        # =================================================

        if (
            source
            in {
                "custom_ai",
                "weak_ai",
                "intent_fuzzy",
            }
            and
            confidence
            <
            self.weak_local_threshold
            and
            not self.has_local_keyword(
                text
            )
        ):

            return RouteDecision(
                route=
                    "open_domain",

                reason=
                    "weak_local_prediction",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    True,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 11. LOCAL CLARIFICATION
        # =================================================
        #
        # If activity is known but missing a slot:
        #
        # "بدي قرآن"
        #
        # we want:
        #
        # "نقرأ ولا نحفظ؟"
        #
        # NOT ChatGPT.
        # =================================================

        if (
            needs_clarification
            and
            intent
            in
            self.activity_intents
        ):

            return RouteDecision(
                route=
                    "local",

                reason=
                    "local_activity_clarification",

                intent=
                    intent,

                confidence=
                    confidence,

                source=
                    source,

                use_open_domain=
                    False,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 12. DEFAULT LOCAL
        # =================================================

        return RouteDecision(
            route=
                "local",

            reason=
                "local_default",

            intent=
                intent,

            confidence=
                confidence,

            source=
                source,

            use_open_domain=
                False,

            nlu_result=
                nlu_result,
        )

    # =====================================================
    # ASK OPEN DOMAIN AI
    # =====================================================

    def ask_open_domain(
        self,
        text,
    ):

        if not self.started:

            self.start()

        try:

            result = (
                self.open_domain_ai.answer(
                    text
                )
            )

        except Exception as error:

            print()
            print(
                "❌ Hybrid AI fallback error:"
            )

            print(
                error
            )

            return {
                "success":
                    False,

                "text":
                    None,

                "source":
                    "open_domain_ai",

                "error":
                    str(
                        error
                    ),
            }

        return result

    # =====================================================
    # ROUTE + OPTIONAL ANSWER
    # =====================================================

    def route(
        self,
        text,
        nlu_result,
        *,
        dialogue_waiting=False,
        activity_active=False,
        call_open_domain=True,
    ):

        decision = (
            self.decide(
                text,
                nlu_result,

                dialogue_waiting=
                    dialogue_waiting,

                activity_active=
                    activity_active,
            )
        )

        print()
        print("=" * 70)
        print("🧠 MIMI HYBRID AI ROUTER")
        print("=" * 70)

        print(
            f"Text       : {text}"
        )

        print(
            f"Local intent: "
            f"{decision.intent}"
        )

        print(
            f"Confidence : "
            f"{decision.confidence:.3f}"
        )

        print(
            f"Source     : "
            f"{decision.source}"
        )

        print(
            f"Route      : "
            f"{decision.route}"
        )

        print(
            f"Reason     : "
            f"{decision.reason}"
        )

        print("=" * 70)

        result = {
            "route":
                decision.route,

            "reason":
                decision.reason,

            "intent":
                decision.intent,

            "confidence":
                decision.confidence,

            "source":
                decision.source,

            "use_open_domain":
                decision.use_open_domain,

            "nlu":
                decision.nlu_result,

            "ai":
                None,
        }

        if (
            decision.use_open_domain
            and
            call_open_domain
        ):

            result[
                "ai"
            ] = (
                self.ask_open_domain(
                    text
                )
            )

        return result

    # =====================================================
    # CHILD
    # =====================================================

    def set_child(
        self,
        child_name=None,
    ):

        try:

            self.open_domain_ai.set_child(
                child_name
            )

        except Exception:

            pass

    # =====================================================
    # CLEAR CHILD
    # =====================================================

    def clear_child(self):

        try:

            self.open_domain_ai.clear_child()

        except Exception:

            pass

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        try:

            self.open_domain_ai.close()

        except Exception:

            pass

        self.started = False


# =========================================================
# STANDALONE ROUTING TEST
# =========================================================


def print_test(
    router,
    text,
    nlu_result,
    **kwargs,
):

    result = (
        router.route(
            text,
            nlu_result,

            call_open_domain=
                False,

            **kwargs,
        )
    )

    print(
        f"{text:<35} "
        f"-> {result['route']:<12} "
        f"({result['reason']})"
    )


def run_tests():

    router = (
        HybridAIRouter()
    )

    print()
    print("=" * 80)
    print(
        "MIMI HYBRID AI ROUTER TEST"
    )
    print("=" * 80)

    # =====================================================
    # LOCAL
    # =====================================================

    print_test(
        router,
        "بدي قصة",

        {
            "intent":
                "story",

            "confidence":
                0.99,

            "source":
                "strong_rule",

            "slots":
                {},
        },
    )

    print_test(
        router,
        "بدي احفظ سورة الملك",

        {
            "intent":
                "quran_memorize",

            "confidence":
                0.99,

            "source":
                "strong_rule",

            "slots": {
                "surah_number":
                    67,

                "quran_mode":
                    "memorize",
            },
        },
    )

    print_test(
        router,
        "كيفك",

        {
            "intent":
                "how_are_you",

            "confidence":
                1.0,

            "source":
                "conversation_exact",

            "slots":
                {},
        },
    )

    print_test(
        router,
        "انا زعلان",

        {
            "intent":
                "child_sad",

            "confidence":
                0.96,

            "source":
                "conversation_tokens",

            "slots":
                {},
        },
    )

    # =====================================================
    # OPEN DOMAIN
    # =====================================================

    print_test(
        router,
        "ليش السما زرقا",

        {
            "intent":
                "story",

            "confidence":
                0.31,

            "source":
                "custom_ai",

            "slots":
                {},
        },
    )

    print_test(
        router,
        "مين اخترع الطيارة",

        {
            "intent":
                "help",

            "confidence":
                0.29,

            "source":
                "custom_ai",

            "slots":
                {},
        },
    )

    print_test(
        router,
        "شو هو كوكب المريخ",

        {
            "intent":
                "unknown",

            "confidence":
                0.12,

            "source":
                "unknown",

            "slots":
                {},
        },
    )

    # =====================================================
    # SAFETY
    # =====================================================

    print_test(
        router,
        "ساعدني",

        {
            "intent":
                "help",

            "confidence":
                0.40,

            "source":
                "custom_ai",

            "slots":
                {},
        },
    )

    # =====================================================
    # DIALOGUE CONTEXT
    # =====================================================

    print_test(
        router,
        "الملك",

        {
            "intent":
                "unknown",

            "confidence":
                0.10,

            "source":
                "unknown",

            "slots":
                {},
        },

        dialogue_waiting=
            True,
    )

    print()
    print("=" * 80)


if __name__ == "__main__":

    run_tests()
