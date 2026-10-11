from difflib import SequenceMatcher

from src.modules.ai_module import (
    AIModule,
)

from src.nlu.child_language_normalizer import (
    ChildLanguageNormalizer,
)

from src.nlu.conversation_signals import (
    ConversationSignals,
)

from src.nlu.slot_extractor import (
    SlotExtractor,
)


# =========================================================
# MIMI NLU ENGINE V3
# =========================================================
#
# Pipeline:
#
# Raw child speech
#       ↓
# ChildLanguageNormalizer
#       ↓
# Exact conversation signals
#       ↓
# Slot extraction
#       ↓
# Strong activity rules
#       ↓
# Emotion / social detection
#       ↓
# Custom trained AI
#       ↓
# Fuzzy intent prototypes
#       ↓
# Hybrid decision
#       ↓
# Intent + Slots + Confidence
#
# =========================================================


class NLUEngine:

    def __init__(
        self,
        ai_module=None,
        accept_threshold=0.25,
        clarification_threshold=0.15,
        fuzzy_threshold=0.72,
    ):

        # =================================================
        # NORMALIZER
        # =================================================

        self.normalizer = (
            ChildLanguageNormalizer()
        )

        # =================================================
        # SLOT EXTRACTOR
        # =================================================

        self.slot_extractor = (
            SlotExtractor()
        )

        # =================================================
        # SOCIAL / EMOTION / DIALOGUE SIGNALS
        # =================================================

        self.conversation_signals = (
            ConversationSignals()
        )

        # =================================================
        # CUSTOM AI
        # =================================================

        self.ai = (
            ai_module
            if ai_module is not None
            else AIModule()
        )

        self.owns_ai = (
            ai_module is None
        )

        # =================================================
        # THRESHOLDS
        # =================================================

        self.accept_threshold = float(
            accept_threshold
        )

        self.clarification_threshold = float(
            clarification_threshold
        )

        self.fuzzy_threshold = float(
            fuzzy_threshold
        )

        self.started = False

        # =================================================
        # FUZZY INTENT PROTOTYPES
        # =================================================
        #
        # هاي fallback، مش المصدر الرئيسي.
        #
        # =================================================

        self.intent_prototypes = {

            "greeting": [
                "مرحبا",
                "اهلا",
                "هاي",
                "السلام عليكم",
                "صباح الخير",
                "مساء الخير",
            ],

            "story": [
                "بدي قصه",
                "احكيلي قصه",
                "قصه",
                "حكايه",
                "احكيلي حكايه",
                "بدي اسمع قصه",
            ],

            "riddle": [
                "بدي لغز",
                "احكيلي لغز",
                "لغز",
                "فزوره",
                "اعطيني فزوره",
                "بدنا نحل لغز",
            ],

            "quran_read": [
                "اقري قران",
                "اقري سوره",
                "بدي اسمع قران",
                "شغلي سوره",
                "اسمعيني قران",
            ],

            "quran_memorize": [
                "بدي احفظ قران",
                "نحفظ سوره",
                "ساعديني احفظ",
                "بدي تسميع",
                "راجع معي قران",
            ],

            "tasks": [
                "شو مهامي",
                "شو واجباتي",
                "احكيلي مهامي",
                "عندي واجبات",
                "عندي مهام",
            ],

            "morning_adhkar": [
                "اذكار الصباح",
                "اقري اذكار الصباح",
                "بدي اذكار الصباح",
            ],

            "evening_adhkar": [
                "اذكار المساء",
                "اقري اذكار المساء",
                "بدي اذكار المساء",
            ],

            "learning": [
                "بدي اتعلم",
                "يلا نتعلم",
                "علّميني",
                "نتعلم الالوان",
                "نتعلم الارقام",
                "نتعلم الحروف",
                "نتعلم الجمع",
            ],

            "help": [
                "ساعديني",
                "شو اعمل",
                "بدي مساعده",
                "ساعديني بشي",
            ],

            "goodbye": [
                "مع السلامه",
                "باي",
                "اشوفك بعدين",
                "خلص باي",
            ],
        }

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:
            return

        print()
        print("=" * 70)
        print("🧠 STARTING MIMI NLU ENGINE V3")
        print("=" * 70)

        if self.owns_ai:

            try:

                self.ai.start()

            except AttributeError:

                pass

        self.started = True

        print(
            "✅ Child language normalizer ready."
        )

        print(
            "✅ Conversation signals ready."
        )

        print(
            "✅ Slot extractor ready."
        )

        print(
            "✅ Custom AI ready."
        )

        print(
            "✅ Hybrid NLU ready."
        )

        print("=" * 70)

    # =====================================================
    # NORMALIZE
    # =====================================================

    def normalize(
        self,
        text,
    ):

        result = (
            self.normalizer.normalize(
                text
            )
        )

        canonical = (
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

        return (
            canonical,
            result,
        )

    # =====================================================
    # SIMILARITY
    # =====================================================

    def similarity(
        self,
        first,
        second,
    ):

        if not first or not second:

            return 0.0

        return (
            SequenceMatcher(
                None,
                first,
                second,
            ).ratio()
        )

    # =====================================================
    # TOKEN HELPERS
    # =====================================================

    def tokens(
        self,
        text,
    ):

        return set(
            str(text).split()
        )

    def contains_any(
        self,
        text,
        values,
    ):

        tokens = self.tokens(
            text
        )

        return bool(
            tokens
            &
            set(values)
        )

    # =====================================================
    # QURAN CONTEXT
    # =====================================================
    #
    # مهم:
    #
    # SlotExtractor يعتبر "شغلي" read word،
    # لكن "شغلي قصة" مش قرآن.
    #
    # لذلك ما بنقرر Quran من quran_mode لحاله.
    #
    # =====================================================

    def has_quran_context(
        self,
        normalized_text,
        slots,
    ):

        if slots.get(
            "surah_number"
        ) is not None:

            return True

        quran_words = {
            "قران",
            "القران",
            "سوره",
            "سور",
            "ايه",
            "ايات",
            "تسميع",
            "سمعلي",
            "مراجعه",
        }

        if self.contains_any(
            normalized_text,
            quran_words,
        ):

            return True

        return False

    # =====================================================
    # STRONG ACTIVITY RULES
    # =====================================================

    def apply_strong_rules(
        self,
        normalized_text,
        slots,
    ):

        tokens = self.tokens(
            normalized_text
        )

        # =================================================
        # UNIVERSAL COMMAND
        # =================================================

        universal = (
            slots.get(
                "universal_command"
            )
        )

        if universal:

            return {
                "matched":
                    True,

                "intent":
                    "universal_command",

                "confidence":
                    1.0,

                "source":
                    "strong_rule",

                "reason":
                    "universal_command",
            }

        # =================================================
        # QURAN
        # =================================================

        quran_context = (
            self.has_quran_context(
                normalized_text,
                slots,
            )
        )

        quran_mode = (
            slots.get(
                "quran_mode"
            )
        )

        if quran_context:

            if quran_mode == "memorize":

                return {
                    "matched":
                        True,

                    "intent":
                        "quran_memorize",

                    "confidence":
                        0.99,

                    "source":
                        "strong_rule",

                    "reason":
                        "quran_memorize",
                }

            if quran_mode == "read":

                return {
                    "matched":
                        True,

                    "intent":
                        "quran_read",

                    "confidence":
                        0.99,

                    "source":
                        "strong_rule",

                    "reason":
                        "quran_read",
                }

            # Quran mentioned but mode unknown
            return {
                "matched":
                    True,

                "intent":
                    "quran",

                "confidence":
                    0.98,

                "source":
                    "strong_rule",

                "reason":
                    "quran_missing_mode",
            }

        # =================================================
        # STORY
        # =================================================

        story_words = {
            "قصه",
            "قصص",
            "حكايه",
            "حكايه",
        }

        if tokens & story_words:

            return {
                "matched":
                    True,

                "intent":
                    "story",

                "confidence":
                    0.99,

                "source":
                    "strong_rule",

                "reason":
                    "story_word",
            }

        # =================================================
        # RIDDLE
        # =================================================

        riddle_words = {
            "لغز",
            "الغاز",
            "فزوره",
            "فوازير",
        }

        if tokens & riddle_words:

            return {
                "matched":
                    True,

                "intent":
                    "riddle",

                "confidence":
                    0.99,

                "source":
                    "strong_rule",

                "reason":
                    "riddle_word",
            }

        # =================================================
        # LEARNING
        # =================================================

        if slots.get(
            "learning_topic"
        ) is not None:

            return {
                "matched":
                    True,

                "intent":
                    "learning",

                "confidence":
                    0.99,

                "source":
                    "strong_rule",

                "reason":
                    "learning_topic",
            }

        learning_words = {
            "اتعلم",
            "نتعلم",
            "تعلم",
            "درس",
            "ندرس",
        }

        if tokens & learning_words:

            return {
                "matched":
                    True,

                "intent":
                    "learning",

                "confidence":
                    0.96,

                "source":
                    "strong_rule",

                "reason":
                    "learning_word",
            }

        # =================================================
        # TASKS
        # =================================================

        if slots.get(
            "task_action"
        ) is not None:

            return {
                "matched":
                    True,

                "intent":
                    "tasks",

                "confidence":
                    0.99,

                "source":
                    "strong_rule",

                "reason":
                    "task_slot",
            }

        task_words = {
            "مهامي",
            "مهماتي",
            "مهام",
            "واجباتي",
            "واجب",
        }

        if tokens & task_words:

            return {
                "matched":
                    True,

                "intent":
                    "tasks",

                "confidence":
                    0.98,

                "source":
                    "strong_rule",

                "reason":
                    "task_word",
            }

        # =================================================
        # ADHKAR
        # =================================================

        adhkar_words = {
            "اذكار",
            "الاذكار",
        }

        morning_words = {
            "الصباح",
            "صباح",
        }

        evening_words = {
            "المساء",
            "مساء",
            "الليل",
        }

        if tokens & adhkar_words:

            if tokens & morning_words:

                return {
                    "matched":
                        True,

                    "intent":
                        "morning_adhkar",

                    "confidence":
                        0.99,

                    "source":
                        "strong_rule",

                    "reason":
                        "morning_adhkar",
                }

            if tokens & evening_words:

                return {
                    "matched":
                        True,

                    "intent":
                        "evening_adhkar",

                    "confidence":
                        0.99,

                    "source":
                        "strong_rule",

                    "reason":
                        "evening_adhkar",
                }

        # =================================================
        # GREETING
        # =================================================

        greeting_words = {
            "مرحبا",
            "اهلا",
            "هاي",
        }

        if tokens & greeting_words:

            return {
                "matched":
                    True,

                "intent":
                    "greeting",

                "confidence":
                    0.98,

                "source":
                    "strong_rule",

                "reason":
                    "greeting",
            }

        # =================================================
        # GOODBYE
        # =================================================

        goodbye_words = {
            "باي",
            "وداعا",
        }

        if tokens & goodbye_words:

            return {
                "matched":
                    True,

                "intent":
                    "goodbye",

                "confidence":
                    0.98,

                "source":
                    "strong_rule",

                "reason":
                    "goodbye",
            }

        if (
            "مع السلامه"
            in normalized_text
        ):

            return {
                "matched":
                    True,

                "intent":
                    "goodbye",

                "confidence":
                    0.99,

                "source":
                    "strong_rule",

                "reason":
                    "goodbye_phrase",
            }

        return {
            "matched":
                False,

            "intent":
                None,

            "confidence":
                0.0,

            "source":
                None,

            "reason":
                None,
        }

    # =====================================================
    # CUSTOM AI PREDICTION
    # =====================================================

    def predict_ai(
        self,
        text,
    ):

        try:

            raw = (
                self.ai.predict(
                    text
                )
            )

        except Exception as error:

            print()
            print(
                "⚠️ Custom AI prediction error:"
            )

            print(
                error
            )

            return {
                "intent":
                    "unknown",

                "confidence":
                    0.0,

                "raw":
                    None,
            }

        # =================================================
        # DICT FORMAT
        # =================================================

        if isinstance(
            raw,
            dict,
        ):

            intent = (
                raw.get(
                    "intent"
                )
                or
                raw.get(
                    "label"
                )
                or
                raw.get(
                    "prediction"
                )
                or
                "unknown"
            )

            confidence = (
                raw.get(
                    "confidence"
                )
            )

            if confidence is None:

                confidence = (
                    raw.get(
                        "score",
                        0.0,
                    )
                )

            try:

                confidence = float(
                    confidence
                )

            except Exception:

                confidence = 0.0

            return {
                "intent":
                    intent,

                "confidence":
                    confidence,

                "raw":
                    raw,
            }

        # =================================================
        # TUPLE / LIST FORMAT
        # =================================================

        if isinstance(
            raw,
            (tuple, list),
        ):

            if len(raw) >= 2:

                try:

                    confidence = float(
                        raw[1]
                    )

                except Exception:

                    confidence = 0.0

                return {
                    "intent":
                        raw[0],

                    "confidence":
                        confidence,

                    "raw":
                        raw,
                }

            if len(raw) == 1:

                return {
                    "intent":
                        raw[0],

                    "confidence":
                        1.0,

                    "raw":
                        raw,
                }

        # =================================================
        # STRING FORMAT
        # =================================================

        if isinstance(
            raw,
            str,
        ):

            return {
                "intent":
                    raw,

                "confidence":
                    1.0,

                "raw":
                    raw,
            }

        return {
            "intent":
                "unknown",

            "confidence":
                0.0,

            "raw":
                raw,
        }

    # =====================================================
    # FUZZY INTENT
    # =====================================================

    def fuzzy_intent(
        self,
        normalized_text,
    ):

        if not normalized_text:

            return {
                "intent":
                    "unknown",

                "confidence":
                    0.0,

                "matched_phrase":
                    None,
            }

        best_intent = (
            "unknown"
        )

        best_score = 0.0

        best_phrase = None

        for (
            intent,
            phrases,
        ) in self.intent_prototypes.items():

            for phrase in phrases:

                normalized_phrase = (
                    self.normalizer
                    .basic_normalize(
                        phrase
                    )
                )

                score = (
                    self.similarity(
                        normalized_text,
                        normalized_phrase,
                    )
                )

                if score > best_score:

                    best_score = (
                        score
                    )

                    best_intent = (
                        intent
                    )

                    best_phrase = (
                        normalized_phrase
                    )

        return {
            "intent":
                best_intent,

            "confidence":
                best_score,

            "matched_phrase":
                best_phrase,
        }

    # =====================================================
    # BUILD CLARIFICATION
    # =====================================================

    def build_clarification(
        self,
        intent,
        slots,
    ):

        # =================================================
        # QURAN
        # =================================================

        if intent == "quran":

            if slots.get(
                "quran_mode"
            ) is None:

                return (
                    "بدك نقرأ القرآن "
                    "ولا نحفظ؟"
                )

            if slots.get(
                "surah_number"
            ) is None:

                return (
                    "أي سورة بتحب؟"
                )

        # =================================================
        # LEARNING
        # =================================================

        if (
            intent == "learning"
            and
            slots.get(
                "learning_topic"
            )
            is None
        ):

            return (
                "شو بتحب نتعلم؟ "
                "ألوان، أرقام، حروف، ولا جمع؟"
            )

        # =================================================
        # UNKNOWN
        # =================================================

        return (
            "ما فهمتك منيح. "
            "ممكن تحكيلي بطريقة ثانية؟"
        )

    # =====================================================
    # BUILD BASE RESULT
    # =====================================================

    def build_result(
        self,
        original_text,
        normalized_text,
        normalization,
        slots,
        intent,
        confidence,
        source,
        needs_clarification=False,
        question=None,
        ai_result=None,
        fuzzy_result=None,
        conversation_result=None,
        rule_result=None,
    ):

        return {
            "original_text":
                original_text,

            "normalized_text":
                normalized_text,

            "normalization":
                normalization,

            "intent":
                intent,

            "confidence":
                float(
                    confidence
                    or 0.0
                ),

            "source":
                source,

            "slots":
                slots,

            "needs_clarification":
                bool(
                    needs_clarification
                ),

            "question":
                question,

            "ai":
                ai_result,

            "fuzzy":
                fuzzy_result,

            "conversation":
                conversation_result,

            "rule":
                rule_result,
        }

    # =====================================================
    # UNDERSTAND
    # =====================================================

    def understand(
        self,
        text,
    ):

        if not self.started:

            self.start()

        original_text = str(
            text
        ).strip()

        # =================================================
        # EMPTY
        # =================================================

        if not original_text:

            return self.build_result(
                original_text=
                    "",

                normalized_text=
                    "",

                normalization=
                    {},

                slots=
                    {},

                intent=
                    "unknown",

                confidence=
                    0.0,

                source=
                    "empty",

                needs_clarification=
                    True,

                question=
                    "ممكن تحكيلي مرة ثانية؟",
            )

        # =================================================
        # 1. NORMALIZE CHILD SPEECH
        # =================================================

        (
            normalized_text,
            normalization,
        ) = self.normalize(
            original_text
        )

        # =================================================
        # 2. CONVERSATION SIGNALS
        # =================================================

        conversation_result = (
            self.conversation_signals
            .detect(
                original_text
            )
        )

        # =================================================
        # EXACT SOCIAL/DIALOGUE MATCH FIRST
        # =================================================
        #
        # Example:
        #   كيفك
        #   شو اسمك
        #   شكرا
        #
        # =================================================

        if (
            conversation_result.get(
                "matched",
                False,
            )
            and
            conversation_result.get(
                "source"
            )
            ==
            "conversation_exact"
        ):

            slots = (
                self.slot_extractor
                .extract(
                    normalized_text
                )
            )

            return self.build_result(
                original_text=
                    original_text,

                normalized_text=
                    normalized_text,

                normalization=
                    normalization,

                slots=
                    slots,

                intent=
                    conversation_result.get(
                        "intent"
                    ),

                confidence=
                    conversation_result.get(
                        "confidence",
                        1.0,
                    ),

                source=
                    conversation_result.get(
                        "source"
                    ),

                conversation_result=
                    conversation_result,
            )

        # =================================================
        # 3. SLOT EXTRACTION
        # =================================================

        slots = (
            self.slot_extractor
            .extract(
                normalized_text
            )
        )

        # =================================================
        # 4. STRONG ACTIVITY RULES
        # =================================================

        rule_result = (
            self.apply_strong_rules(
                normalized_text,
                slots,
            )
        )

        if rule_result.get(
            "matched",
            False,
        ):

            intent = (
                rule_result.get(
                    "intent"
                )
            )

            needs_clarification = (
                intent
                ==
                "quran"
            )

            question = None

            if needs_clarification:

                question = (
                    self.build_clarification(
                        intent,
                        slots,
                    )
                )

            return self.build_result(
                original_text=
                    original_text,

                normalized_text=
                    normalized_text,

                normalization=
                    normalization,

                slots=
                    slots,

                intent=
                    intent,

                confidence=
                    rule_result.get(
                        "confidence",
                        1.0,
                    ),

                source=
                    rule_result.get(
                        "source",
                        "strong_rule",
                    ),

                needs_clarification=
                    needs_clarification,

                question=
                    question,

                conversation_result=
                    conversation_result,

                rule_result=
                    rule_result,
            )

        # =================================================
        # 5. EMOTION / SOCIAL / DIALOGUE SIGNAL
        # =================================================
        #
        # Token/fuzzy detection happens AFTER activity
        # rules to protect:
        #
        #   بدي قصة
        #   بدي قرآن
        #
        # =================================================

        if conversation_result.get(
            "matched",
            False,
        ):

            return self.build_result(
                original_text=
                    original_text,

                normalized_text=
                    normalized_text,

                normalization=
                    normalization,

                slots=
                    slots,

                intent=
                    conversation_result.get(
                        "intent"
                    ),

                confidence=
                    conversation_result.get(
                        "confidence",
                        0.0,
                    ),

                source=
                    conversation_result.get(
                        "source"
                    ),

                conversation_result=
                    conversation_result,

                rule_result=
                    rule_result,
            )

        # =================================================
        # 6. CUSTOM TRAINED AI
        # =================================================

        ai_result = (
            self.predict_ai(
                normalized_text
            )
        )

        # =================================================
        # 7. FUZZY FALLBACK
        # =================================================

        fuzzy_result = (
            self.fuzzy_intent(
                normalized_text
            )
        )

        ai_intent = (
            ai_result.get(
                "intent",
                "unknown",
            )
        )

        ai_confidence = float(
            ai_result.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        fuzzy_intent = (
            fuzzy_result.get(
                "intent",
                "unknown",
            )
        )

        fuzzy_confidence = float(
            fuzzy_result.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        # =================================================
        # 8. HYBRID DECISION
        # =================================================

        final_intent = (
            "unknown"
        )

        final_confidence = 0.0

        final_source = (
            "unknown"
        )

        # -------------------------------------------------
        # AI confidently knows
        # -------------------------------------------------

        if (
            ai_intent
            !=
            "unknown"
            and
            ai_confidence
            >=
            self.accept_threshold
        ):

            final_intent = (
                ai_intent
            )

            final_confidence = (
                ai_confidence
            )

            final_source = (
                "custom_ai"
            )

        # -------------------------------------------------
        # Fuzzy strongly knows
        # -------------------------------------------------

        if (
            fuzzy_intent
            !=
            "unknown"
            and
            fuzzy_confidence
            >=
            self.fuzzy_threshold
            and
            fuzzy_confidence
            >
            final_confidence
        ):

            final_intent = (
                fuzzy_intent
            )

            final_confidence = (
                fuzzy_confidence
            )

            final_source = (
                "intent_fuzzy"
            )

        # -------------------------------------------------
        # Weak AI candidate
        # -------------------------------------------------

        if (
            final_intent
            ==
            "unknown"
            and
            ai_intent
            !=
            "unknown"
            and
            ai_confidence
            >=
            self.clarification_threshold
        ):

            final_intent = (
                ai_intent
            )

            final_confidence = (
                ai_confidence
            )

            final_source = (
                "weak_ai"
            )

        # =================================================
        # 9. POSTPROCESS QURAN AI RESULT
        # =================================================
        #
        # AI may classify:
        #
        #   "اقريلي اشي"
        #
        # as quran_read even without explicit "قران".
        #
        # That's allowed if model confidence is enough.
        #
        # =================================================

        if final_intent == "quran_read":

            if slots.get(
                "quran_mode"
            ) is None:

                slots[
                    "quran_mode"
                ] = "read"

        elif final_intent == "quran_memorize":

            if slots.get(
                "quran_mode"
            ) is None:

                slots[
                    "quran_mode"
                ] = "memorize"

        # =================================================
        # 10. CLARIFICATION
        # =================================================

        needs_clarification = False

        question = None

        if final_intent == "unknown":

            needs_clarification = True

            question = (
                self.build_clarification(
                    "unknown",
                    slots,
                )
            )

        elif (
            final_source
            ==
            "weak_ai"
        ):

            needs_clarification = True

            question = (
                "مش متأكدة إني فهمتك. "
                "ممكن تحكيلي بطريقة ثانية؟"
            )

        elif (
            final_intent
            in {
                "quran_read",
                "quran_memorize",
            }
            and
            slots.get(
                "surah_number"
            )
            is None
        ):

            # DialogueManager can ask for Surah.
            needs_clarification = True

            question = (
                "أي سورة بتحب؟"
            )

        elif (
            final_intent
            ==
            "learning"
            and
            slots.get(
                "learning_topic"
            )
            is None
        ):

            needs_clarification = True

            question = (
                self.build_clarification(
                    "learning",
                    slots,
                )
            )

        # =================================================
        # RESULT
        # =================================================

        return self.build_result(
            original_text=
                original_text,

            normalized_text=
                normalized_text,

            normalization=
                normalization,

            slots=
                slots,

            intent=
                final_intent,

            confidence=
                final_confidence,

            source=
                final_source,

            needs_clarification=
                needs_clarification,

            question=
                question,

            ai_result=
                ai_result,

            fuzzy_result=
                fuzzy_result,

            conversation_result=
                conversation_result,

            rule_result=
                rule_result,
        )

    # =====================================================
    # PRINT RESULT
    # =====================================================

    def print_result(
        self,
        result,
    ):

        print()
        print("=" * 72)
        print("🧠 MIMI NLU V3 RESULT")
        print("=" * 72)

        print(
            f"Original    : "
            f"{result.get('original_text')}"
        )

        print(
            f"Normalized  : "
            f"{result.get('normalized_text')}"
        )

        print(
            f"Intent      : "
            f"{result.get('intent')}"
        )

        print(
            f"Confidence  : "
            f"{result.get('confidence', 0.0):.3f}"
        )

        print(
            f"Source      : "
            f"{result.get('source')}"
        )

        print(
            f"Clarify     : "
            f"{result.get('needs_clarification')}"
        )

        if result.get(
            "question"
        ):

            print(
                f"Question    : "
                f"{result.get('question')}"
            )

        print()
        print("Slots:")

        for (
            key,
            value,
        ) in (
            result.get(
                "slots",
                {}
            ).items()
        ):

            if value is not None:

                print(
                    f"  {key}: {value}"
                )

        conversation = (
            result.get(
                "conversation"
            )
        )

        if (
            isinstance(
                conversation,
                dict,
            )
            and
            conversation.get(
                "matched"
            )
        ):

            print()
            print(
                "Conversation signal:"
            )

            print(
                f"  intent: "
                f"{conversation.get('intent')}"
            )

            print(
                f"  category: "
                f"{conversation.get('category')}"
            )

        print("=" * 72)

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        if self.owns_ai:

            try:

                self.ai.close()

            except Exception:

                pass

        self.started = False

        print(
            "✅ Mimi NLU V3 closed."
        )


# =========================================================
# STANDALONE TEST
# =========================================================

def run_tests():

    engine = (
        NLUEngine()
    )

    engine.start()

    tests = [

        # =================================================
        # NORMAL ACTIVITIES
        # =================================================

        "بدي قصة",
        "احكيلي قصة عن قطة",
        "اعطيني فزوره",
        "شو واجباتي",
        "بدي اتعلم الالوان",

        # =================================================
        # QURAN
        # =================================================

        "بدي قران",
        "اقري سورة الفلق",
        "بدي احفظ سورة الناس",
        "شغلي الناص",
        "اقري سورة الملك",

        # =================================================
        # SOCIAL
        # =================================================

        "كيفك",
        "ميمي كيفك اليوم",
        "شو اسمك",
        "مين انتي",
        "شو بتقدري تعملي",
        "شكرا ميمي",
        "انتي شطوره",
        "بحبك ميمي",

        # =================================================
        # EMOTIONS
        # =================================================

        "انا مبسوط",
        "انا زعلان اليوم",
        "انا خايفه",
        "انا تعبانه",
        "انا زهقان",

        # =================================================
        # DIALOGUE CONTROLS
        # =================================================

        "اه",
        "لا",
        "كملي",
        "غيري",
        "استني",
        "عيدي",
        "ما فهمت",

        # =================================================
        # CHILD-LIKE SPEECH
        # =================================================

        "مييييمي بدييي قصصصه",
        "ميمي شو ممكن نعمل",
        "بدي اشي يضحك",
        "مش عارف شو اعمل",
    ]

    try:

        for text in tests:

            print()
            print()
            print("#" * 72)
            print(
                f"👧 CHILD: {text}"
            )
            print("#" * 72)

            result = (
                engine.understand(
                    text
                )
            )

            engine.print_result(
                result
            )

    finally:

        engine.close()


if __name__ == "__main__":

    run_tests()