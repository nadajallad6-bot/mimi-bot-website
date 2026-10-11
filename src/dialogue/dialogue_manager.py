from src.dialogue.conversation_context import (
    ConversationContext,
)

from src.dialogue.interaction_memory import (
    InteractionMemory,
)

from src.nlu.nlu_engine import (
    NLUEngine,
)


# =========================================================
# MIMI DIALOGUE MANAGER V3
# =========================================================
#
# Architecture:
#
# Child speech
#     ↓
# ConversationContext
#     +
# InteractionMemory
#     ↓
# Pending follow-up?
#     ↓
# NLU V3
#     ↓
# Intent + Slots
#     ↓
# Ask / Execute
#
#
# Example:
#
# Child:
#   بدي قرآن
#
# Mimi:
#   بدك نقرأ ولا نحفظ؟
#
# Child:
#   نحفظ
#
# Mimi:
#   أي سورة؟
#
# Child:
#   الملك
#
# Result:
#   intent = quran_memorize
#   surah_number = 67
#
# =========================================================


class DialogueManager:

    def __init__(
        self,
        nlu_engine=None,
        context=None,
        memory=None,
    ):

        # =================================================
        # NLU
        # =================================================

        self.nlu = (
            nlu_engine
            if nlu_engine is not None
            else NLUEngine()
        )

        self.owns_nlu = (
            nlu_engine is None
        )

        # =================================================
        # CONVERSATION CONTEXT
        # =================================================
        #
        # مهم:
        # mimi_bot.py يستخدم self.context
        # لذلك لا نحذفه.
        # =================================================

        self.context = (
            context
            if context is not None
            else ConversationContext(
                timeout_seconds=120
            )
        )

        # =================================================
        # INTERACTION MEMORY
        # =================================================
        #
        # ذاكرة إضافية للحوار الطبيعي:
        #
        # "نحفظ"
        # "الملك"
        # "الألوان"
        # "كملي"
        # "غيري"
        # "استني"
        #
        # =================================================

        self.memory = (
            memory
            if memory is not None
            else InteractionMemory(
                timeout_seconds=120
            )
        )

        self.started = False

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:

            return

        print()
        print("=" * 70)
        print("💬 STARTING MIMI DIALOGUE MANAGER V3")
        print("=" * 70)

        if self.owns_nlu:

            self.nlu.start()

        self.started = True

        print(
            "✅ Conversation context ready."
        )

        print(
            "✅ Interaction memory ready."
        )

        print(
            "✅ Multi-turn dialogue ready."
        )

        print("=" * 70)

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.context.reset()

        self.memory.reset()

        print()
        print(
            "💬 Dialogue + memory reset."
        )

    # =====================================================
    # NORMALIZED TEXT
    # =====================================================

    def normalize(
        self,
        text,
    ):

        try:

            result = (
                self.nlu.normalizer.normalize(
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
    # QURAN MODE FROM CHILD ANSWER
    # =====================================================

    def detect_quran_mode_answer(
        self,
        text,
    ):

        # InteractionMemory has a more flexible
        # detector, so try it first.

        try:

            mode = (
                self.memory
                .extract_quran_mode(
                    text
                )
            )

            if mode:

                return mode

        except Exception:

            pass

        normalized = (
            self.normalize(
                text
            )
        )

        tokens = set(
            normalized.split()
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

        if (
            tokens
            &
            memorize_words
        ):

            return "memorize"

        read_words = {
            "اقري",
            "اسمع",
            "اسمعيني",
            "قراءه",
            "شغلي",
            "نقرا",
            "اقرا",
        }

        if (
            tokens
            &
            read_words
        ):

            return "read"

        return None

    # =====================================================
    # LEARNING TOPIC ANSWER
    # =====================================================

    def detect_learning_topic_answer(
        self,
        text,
    ):

        try:

            topic = (
                self.memory
                .extract_learning_topic(
                    text
                )
            )

            if topic:

                return topic

        except Exception:

            pass

        try:

            slots = (
                self.nlu
                .slot_extractor
                .extract(
                    text
                )
            )

            return (
                slots.get(
                    "learning_topic"
                )
            )

        except Exception:

            return None

    # =====================================================
    # SURAH ANSWER
    # =====================================================

    def detect_surah_answer(
        self,
        text,
    ):

        # =================================================
        # Interaction Memory
        # =================================================

        try:

            surah = (
                self.memory
                .extract_surah(
                    text
                )
            )

            if surah:

                return surah

        except Exception:

            pass

        # =================================================
        # SlotExtractor fallback
        # =================================================

        try:

            slots = (
                self.nlu
                .slot_extractor
                .extract(
                    text
                )
            )

        except Exception:

            return None

        number = (
            slots.get(
                "surah_number"
            )
        )

        if number is None:

            return None

        return {
            "surah_number":
                number,

            "surah_name":
                slots.get(
                    "surah_name"
                ),

            "surah_confidence":
                slots.get(
                    "surah_confidence"
                ),
        }

    # =====================================================
    # MEMORY WAITING NAME
    # =====================================================

    def memory_waiting_name(
        self,
        waiting_for,
    ):

        mapping = {
            "quran_mode":
                "quran_mode",

            "surah_number":
                "surah",

            "learning_topic":
                "learning_topic",

            "clarification":
                "clarification",
        }

        return mapping.get(
            waiting_for,
            waiting_for,
        )

    # =====================================================
    # UNIVERSAL RESPONSE
    # =====================================================

    def build_universal_result(
        self,
        command,
        nlu_result=None,
    ):

        return {
            "handled":
                True,

            "action":
                "universal",

            "ready_to_execute":
                True,

            "intent":
                "universal_command",

            "slots": {
                "command":
                    command
            },

            "response":
                None,

            "question":
                None,

            "waiting_for":
                None,

            "nlu":
                nlu_result,

            "context":
                self.context.get_state(),

            "memory":
                self.memory.get_state(),
        }

    # =====================================================
    # CONTROL RESPONSE
    # =====================================================

    def build_control_result(
        self,
        command,
    ):

        # Stop / Back are global actions.

        if command in {
            "stop",
            "back",
        }:

            self.context.reset()

            self.memory.reset()

            return (
                self.build_universal_result(
                    command=
                        command,
                    nlu_result=
                        None,
                )
            )

        # Repeat / Continue / Wait / Change
        # already have handlers inside MimiBot.

        return {
            "handled":
                True,

            "action":
                "execute",

            "ready_to_execute":
                True,

            "intent":
                command,

            "slots":
                {},

            "response":
                None,

            "question":
                None,

            "waiting_for":
                None,

            "nlu":
                None,

            "context":
                self.context.get_state(),

            "memory":
                self.memory.get_state(),
        }

    # =====================================================
    # ASK QUESTION
    # =====================================================

    def ask(
        self,
        waiting_for,
        question,
        intent=None,
        slots=None,
        nlu_result=None,
    ):

        # =================================================
        # ConversationContext
        # =================================================

        if intent is not None:

            self.context.set_intent(
                intent
            )

        if slots:

            self.context.update_slots(
                slots
            )

        self.context.wait_for(
            waiting_for,
            question,
        )

        # =================================================
        # InteractionMemory
        # =================================================

        memory_waiting = (
            self.memory_waiting_name(
                waiting_for
            )
        )

        # Preserve existing memory context when possible.

        if not self.memory.active:

            self.memory.start_context(
                intent=
                    intent
                    or
                    self.context.intent,

                slots=
                    dict(
                        self.context.slots
                    ),
            )

        else:

            if intent is not None:

                self.memory.active_intent = (
                    intent
                )

            if slots:

                for (
                    key,
                    value,
                ) in slots.items():

                    if value is not None:

                        self.memory.set_slot(
                            key,
                            value,
                        )

        if (
            memory_waiting
            !=
            "clarification"
        ):

            self.memory.ask_for(
                waiting_for=
                    memory_waiting,

                intent=
                    intent
                    or
                    self.context.intent,

                slots=
                    dict(
                        self.context.slots
                    ),
            )

        else:

            self.memory.waiting_for = (
                "clarification"
            )

            self.memory.active = True

            self.memory.touch()

        self.memory.record_mimi(
            question
        )

        return {
            "handled":
                True,

            "action":
                "ask",

            "ready_to_execute":
                False,

            "intent":
                self.context.intent,

            "slots":
                dict(
                    self.context.slots
                ),

            "response":
                question,

            "question":
                question,

            "waiting_for":
                waiting_for,

            "nlu":
                nlu_result,

            "context":
                self.context.get_state(),

            "memory":
                self.memory.get_state(),
        }

    # =====================================================
    # EXECUTE RESULT
    # =====================================================

    def execute(
        self,
        intent,
        slots=None,
        nlu_result=None,
    ):

        final_slots = {}

        # =================================================
        # Existing ConversationContext slots
        # =================================================

        final_slots.update(
            self.context.slots
        )

        # =================================================
        # Existing Memory slots
        # =================================================

        try:

            final_slots.update(
                self.memory.pending_slots
            )

        except Exception:

            pass

        # =================================================
        # New slots
        # =================================================

        if slots:

            for (
                key,
                value,
            ) in slots.items():

                if value is not None:

                    final_slots[
                        key
                    ] = value

        # =================================================
        # Snapshot before clearing
        # =================================================

        context_snapshot = (
            self.context.get_state()
        )

        # =================================================
        # Keep short-term activity memory
        # =================================================
        #
        # Important:
        #
        # We complete ConversationContext because all
        # required information was gathered.
        #
        # But InteractionMemory stays aware of the
        # last executed activity so:
        #
        #   كملي
        #   استني
        #   غيري
        #
        # still have conversational meaning.
        # =================================================

        self.memory.start_context(
            intent=
                intent,

            slots=
                final_slots,

            topic=
                "activity",
        )

        self.memory.set_activity(
            intent
        )

        self.memory.clear_waiting()

        # =================================================
        # Result
        # =================================================

        result = {
            "handled":
                True,

            "action":
                "execute",

            "ready_to_execute":
                True,

            "intent":
                intent,

            "slots":
                final_slots,

            "response":
                None,

            "question":
                None,

            "waiting_for":
                None,

            "nlu":
                nlu_result,

            "context":
                context_snapshot,

            "memory":
                self.memory.get_state(),
        }

        self.context.complete()

        return result

    # =====================================================
    # UNKNOWN RESULT
    # =====================================================

    def unknown(
        self,
        nlu_result,
        question=None,
    ):

        question = (
            question
            or
            "ما فهمتك منيح. "
            "ممكن تحكيلي بطريقة ثانية؟"
        )

        self.context.set_intent(
            "unknown"
        )

        self.context.wait_for(
            "clarification",
            question,
        )

        self.memory.start_context(
            intent=
                "unknown"
        )

        self.memory.waiting_for = (
            "clarification"
        )

        self.memory.record_mimi(
            question
        )

        return {
            "handled":
                True,

            "action":
                "ask",

            "ready_to_execute":
                False,

            "intent":
                "unknown",

            "slots":
                {},

            "response":
                question,

            "question":
                question,

            "waiting_for":
                "clarification",

            "nlu":
                nlu_result,

            "context":
                self.context.get_state(),

            "memory":
                self.memory.get_state(),
        }

    # =====================================================
    # MEMORY CONTROL
    # =====================================================

    def detect_memory_control(
        self,
        text,
    ):

        try:

            control = (
                self.memory
                .detect_control(
                    text
                )
            )

        except Exception:

            control = None

        if control is None:

            return None

        print()
        print(
            f"🧠 Memory control: "
            f"{control}"
        )

        return control

    # =====================================================
    # HANDLE PENDING QUESTION
    # =====================================================

    def handle_pending(
        self,
        text,
    ):

        self.context.check_timeout()

        self.memory.cleanup_if_expired()

        waiting_for = (
            self.context.waiting_for
        )

        if not waiting_for:

            return None

        print()
        print(
            f"💬 Dialogue answer for: "
            f"{waiting_for}"
        )

        # =================================================
        # CONTROL WHILE MIMI IS ASKING
        # =================================================
        #
        # Example:
        #
        # Mimi: أي سورة؟
        # Child: استني
        #
        # Do not interpret "استني" as a Surah.
        # =================================================

        control = (
            self.detect_memory_control(
                text
            )
        )

        if control:

            # Keep current pending question for wait/repeat.

            if control in {
                "wait",
                "repeat",
            }:

                return (
                    self.build_control_result(
                        control
                    )
                )

            # Change / stop / back end the current
            # pending conversation.

            if control in {
                "change",
                "stop",
                "back",
            }:

                self.context.reset()

                self.memory.reset()

                return (
                    self.build_control_result(
                        control
                    )
                )

            if control == "continue":

                # "كملي" while waiting for information
                # isn't an answer; repeat the question.

                question = (
                    self.context.question
                    if hasattr(
                        self.context,
                        "question",
                    )
                    else None
                )

                if not question:

                    question = (
                        self.memory.last_response
                    )

                if not question:

                    question = (
                        "احكيلي جوابك."
                    )

                return self.ask(
                    waiting_for=
                        waiting_for,

                    question=
                        question,

                    intent=
                        self.context.intent,
                )

        # =================================================
        # WAITING FOR QURAN MODE
        # =================================================

        if waiting_for == "quran_mode":

            mode = (
                self.detect_quran_mode_answer(
                    text
                )
            )

            if mode is None:

                return self.ask(
                    waiting_for=
                        "quran_mode",

                    question=
                        "بدك نقرأ القرآن "
                        "ولا نحفظ؟",

                    intent=
                        self.context.intent,
                )

            self.context.set_slot(
                "quran_mode",
                mode,
            )

            self.memory.set_slot(
                "quran_mode",
                mode,
            )

            self.context.clear_waiting()

            self.memory.clear_waiting()

            # =================================================
            # Do we already know the Surah?
            # =================================================

            surah_number = (
                self.context.get_slot(
                    "surah_number"
                )
            )

            if surah_number is None:

                return self.ask(
                    waiting_for=
                        "surah_number",

                    question=
                        "تمام. أي سورة؟",

                    intent=
                        "quran",
                )

            # =================================================
            # Ready
            # =================================================

            if mode == "memorize":

                intent = (
                    "quran_memorize"
                )

            else:

                intent = (
                    "quran_read"
                )

            return self.execute(
                intent=
                    intent,

                slots=
                    self.context.slots,
            )

        # =================================================
        # WAITING FOR SURAH
        # =================================================

        if waiting_for == "surah_number":

            surah = (
                self.detect_surah_answer(
                    text
                )
            )

            if surah is None:

                return self.ask(
                    waiting_for=
                        "surah_number",

                    question=
                        "ما عرفت اسم السورة. "
                        "احكيلي اسم السورة مرة ثانية.",

                    intent=
                        self.context.intent,
                )

            self.context.update_slots(
                surah
            )

            for (
                key,
                value,
            ) in surah.items():

                if value is not None:

                    self.memory.set_slot(
                        key,
                        value,
                    )

            self.context.clear_waiting()

            self.memory.clear_waiting()

            quran_mode = (
                self.context.get_slot(
                    "quran_mode"
                )
            )

            # =================================================
            # Mode still unknown
            # =================================================

            if quran_mode is None:

                return self.ask(
                    waiting_for=
                        "quran_mode",

                    question=
                        "بدك نقرأ السورة "
                        "ولا نحفظها؟",

                    intent=
                        "quran",
                )

            # =================================================
            # Ready
            # =================================================

            if quran_mode == "memorize":

                intent = (
                    "quran_memorize"
                )

            else:

                intent = (
                    "quran_read"
                )

            return self.execute(
                intent=
                    intent,

                slots=
                    self.context.slots,
            )

        # =================================================
        # WAITING FOR LEARNING TOPIC
        # =================================================

        if waiting_for == "learning_topic":

            topic = (
                self.detect_learning_topic_answer(
                    text
                )
            )

            if topic is None:

                return self.ask(
                    waiting_for=
                        "learning_topic",

                    question=
                        "شو بتحب نتعلم؟ "
                        "الألوان، الأرقام، "
                        "الحروف، ولا الجمع؟",

                    intent=
                        "learning",
                )

            self.context.set_slot(
                "learning_topic",
                topic,
            )

            self.memory.set_slot(
                "learning_topic",
                topic,
            )

            self.context.clear_waiting()

            self.memory.clear_waiting()

            return self.execute(
                intent=
                    "learning",

                slots=
                    self.context.slots,
            )

        # =================================================
        # GENERIC CLARIFICATION
        # =================================================

        if waiting_for == "clarification":

            # Clear the old uncertainty and give the new
            # sentence to NLU normally.

            self.context.clear_waiting()

            self.memory.clear_waiting()

            return None

        return None

    # =====================================================
    # HANDLE QURAN INTENT
    # =====================================================

    def handle_quran(
        self,
        nlu_result,
    ):

        slots = (
            nlu_result.get(
                "slots",
                {}
            )
        )

        quran_mode = (
            slots.get(
                "quran_mode"
            )
        )

        surah_number = (
            slots.get(
                "surah_number"
            )
        )

        # =================================================
        # Save useful slots
        # =================================================

        self.context.set_intent(
            "quran"
        )

        self.context.update_slots(
            slots
        )

        if not self.memory.active:

            self.memory.start_context(
                intent=
                    "quran",

                slots=
                    slots,
            )

        else:

            self.memory.active_intent = (
                "quran"
            )

            for (
                key,
                value,
            ) in slots.items():

                if value is not None:

                    self.memory.set_slot(
                        key,
                        value,
                    )

        # =================================================
        # Missing Mode
        # =================================================

        if quran_mode is None:

            return self.ask(
                waiting_for=
                    "quran_mode",

                question=
                    "بدك نقرأ القرآن "
                    "ولا نحفظ؟",

                intent=
                    "quran",

                slots=
                    slots,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # Missing Surah
        # =================================================

        if surah_number is None:

            return self.ask(
                waiting_for=
                    "surah_number",

                question=
                    "أي سورة؟",

                intent=
                    "quran",

                slots=
                    slots,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # Everything known
        # =================================================

        if quran_mode == "memorize":

            final_intent = (
                "quran_memorize"
            )

        else:

            final_intent = (
                "quran_read"
            )

        return self.execute(
            intent=
                final_intent,

            slots=
                slots,

            nlu_result=
                nlu_result,
        )

    # =====================================================
    # HANDLE LEARNING
    # =====================================================

    def handle_learning(
        self,
        nlu_result,
    ):

        slots = (
            nlu_result.get(
                "slots",
                {}
            )
        )

        topic = (
            slots.get(
                "learning_topic"
            )
        )

        self.context.set_intent(
            "learning"
        )

        self.context.update_slots(
            slots
        )

        if not self.memory.active:

            self.memory.start_context(
                intent=
                    "learning",

                slots=
                    slots,
            )

        else:

            self.memory.active_intent = (
                "learning"
            )

            for (
                key,
                value,
            ) in slots.items():

                if value is not None:

                    self.memory.set_slot(
                        key,
                        value,
                    )

        # =================================================
        # Need Topic
        # =================================================

        if topic is None:

            return self.ask(
                waiting_for=
                    "learning_topic",

                question=
                    "شو بتحب نتعلم؟ "
                    "الألوان، الأرقام، "
                    "الحروف، ولا الجمع؟",

                intent=
                    "learning",

                slots=
                    slots,

                nlu_result=
                    nlu_result,
            )

        return self.execute(
            intent=
                "learning",

            slots=
                slots,

            nlu_result=
                nlu_result,
        )

    # =====================================================
    # MEMORY CONTROL OUTSIDE PENDING QUESTION
    # =====================================================

    def handle_free_memory_control(
        self,
        text,
    ):

        if not self.memory.active:

            return None

        control = (
            self.detect_memory_control(
                text
            )
        )

        if control is None:

            return None

        return (
            self.build_control_result(
                control
            )
        )

    # =====================================================
    # MAIN PROCESS
    # =====================================================

    def process(
        self,
        text,
    ):

        if not self.started:

            self.start()

        text = str(
            text
        ).strip()

        print()
        print("=" * 70)
        print("💬 MIMI DIALOGUE INPUT V3")
        print("=" * 70)

        print(
            f"👧 Child: {text}"
        )

        # =================================================
        # EMPTY INPUT
        # =================================================

        if not text:

            return self.unknown(
                {
                    "intent":
                        "unknown",

                    "confidence":
                        0.0,

                    "slots":
                        {},
                },

                question=
                    "ممكن تحكيلي مرة ثانية؟",
            )

        # =================================================
        # 1. CONTEXT TIMEOUT
        # =================================================

        self.context.check_timeout()

        self.memory.cleanup_if_expired()

        # =================================================
        # 2. RECORD CHILD TURN
        # =================================================
        #
        # This stays local memory only.
        # We do not save raw child speech to MongoDB here.
        # =================================================

        self.memory.record_child(
            text
        )

        # =================================================
        # 3. PENDING CONVERSATION QUESTION
        # =================================================

        if self.context.is_waiting():

            pending_result = (
                self.handle_pending(
                    text
                )
            )

            if pending_result is not None:

                return pending_result

        # =================================================
        # 4. SHORT CONTROL BASED ON MEMORY
        # =================================================
        #
        # Important:
        #
        # "كملي" / "استني" / "غيري"
        #
        # get conversational meaning even when there is
        # no pending slot question.
        # =================================================

        memory_control_result = (
            self.handle_free_memory_control(
                text
            )
        )

        if memory_control_result is not None:

            return memory_control_result

        # =================================================
        # 5. NORMAL NLU
        # =================================================

        nlu_result = (
            self.nlu.understand(
                text
            )
        )

        intent = (
            nlu_result.get(
                "intent",
                "unknown",
            )
        )

        slots = (
            nlu_result.get(
                "slots",
                {}
            )
        )

        # Store interpreted child turn.

        self.memory.last_intent = (
            intent
        )

        self.memory.last_slots = dict(
            slots
        )

        # =================================================
        # 6. UNIVERSAL COMMAND
        # =================================================

        universal_command = (
            slots.get(
                "universal_command"
            )
        )

        if (
            intent
            ==
            "universal_command"
            or
            universal_command
        ):

            command = (
                universal_command
            )

            # If NLU returned universal intent but slot
            # isn't populated, try normalized control.

            if command is None:

                command = (
                    self.detect_memory_control(
                        text
                    )
                )

            self.context.reset()

            self.memory.reset()

            return (
                self.build_universal_result(
                    command=
                        command,

                    nlu_result=
                        nlu_result,
                )
            )

        # =================================================
        # 7. QURAN
        # =================================================

        if intent in {
            "quran",
            "quran_read",
            "quran_memorize",
        }:

            # Force mode from final intent.

            if (
                intent
                ==
                "quran_read"
                and
                slots.get(
                    "quran_mode"
                )
                is None
            ):

                slots[
                    "quran_mode"
                ] = "read"

            elif (
                intent
                ==
                "quran_memorize"
                and
                slots.get(
                    "quran_mode"
                )
                is None
            ):

                slots[
                    "quran_mode"
                ] = "memorize"

            return (
                self.handle_quran(
                    nlu_result
                )
            )

        # =================================================
        # 8. LEARNING
        # =================================================

        if intent == "learning":

            return (
                self.handle_learning(
                    nlu_result
                )
            )

        # =================================================
        # 9. NLU REQUESTED CLARIFICATION
        # =================================================

        if nlu_result.get(
            "needs_clarification",
            False,
        ):

            question = (
                nlu_result.get(
                    "question"
                )
                or
                "ممكن تحكيلي بطريقة ثانية؟"
            )

            return self.ask(
                waiting_for=
                    "clarification",

                question=
                    question,

                intent=
                    intent,

                slots=
                    slots,

                nlu_result=
                    nlu_result,
            )

        # =================================================
        # 10. UNKNOWN
        # =================================================

        if intent == "unknown":

            return (
                self.unknown(
                    nlu_result
                )
            )

        # =================================================
        # 11. SIMPLE READY INTENT
        # =================================================
        #
        # Includes:
        #
        # story
        # riddle
        # tasks
        # adhkar
        # greeting
        # social intents
        # emotions
        # dialogue signals
        # goodbye
        #
        # =================================================

        return self.execute(
            intent=
                intent,

            slots=
                slots,

            nlu_result=
                nlu_result,
        )

    # =====================================================
    # PRINT RESULT
    # =====================================================

    def print_result(
        self,
        result,
    ):

        print()
        print("=" * 70)
        print("💬 DIALOGUE RESULT V3")
        print("=" * 70)

        print(
            f"Action     : "
            f"{result.get('action')}"
        )

        print(
            f"Intent     : "
            f"{result.get('intent')}"
        )

        print(
            f"Ready      : "
            f"{result.get('ready_to_execute')}"
        )

        print(
            f"Waiting For: "
            f"{result.get('waiting_for')}"
        )

        print()
        print(
            "Slots:"
        )

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

        if result.get(
            "response"
        ):

            print()
            print(
                f"🤖 Mimi: "
                f"{result.get('response')}"
            )

        print()
        print(
            "Memory:"
        )

        memory = (
            result.get(
                "memory",
                {}
            )
        )

        print(
            f"  active_intent: "
            f"{memory.get('active_intent')}"
        )

        print(
            f"  waiting_for: "
            f"{memory.get('waiting_for')}"
        )

        print(
            f"  last_activity: "
            f"{memory.get('last_activity')}"
        )

        print("=" * 70)

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.context.reset()

        self.memory.reset()

        if self.owns_nlu:

            try:

                self.nlu.close()

            except Exception:

                pass

        self.started = False

        print(
            "✅ Dialogue Manager V3 closed."
        )


# =========================================================
# TEST HELPER
# =========================================================

def print_turn(
    dialogue,
    text,
):

    print()
    print()
    print("#" * 70)
    print(
        f"👧 CHILD: {text}"
    )
    print("#" * 70)

    result = (
        dialogue.process(
            text
        )
    )

    dialogue.print_result(
        result
    )

    return result


# =========================================================
# TEST CONVERSATIONS
# =========================================================

def test_dialogue():

    dialogue = (
        DialogueManager()
    )

    try:

        dialogue.start()

        # =================================================
        # TEST 1 - QURAN MULTI TURN
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 1 - QURAN MULTI-TURN")
        print("#" * 70)

        dialogue.reset()

        print_turn(
            dialogue,
            "ميمي بدي قرآن",
        )

        print_turn(
            dialogue,
            "نحفظ",
        )

        print_turn(
            dialogue,
            "الملك",
        )

        # =================================================
        # TEST 2 - DIRECT QURAN
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 2 - DIRECT QURAN")
        print("#" * 70)

        dialogue.reset()

        print_turn(
            dialogue,
            "ميمي بدي أحفظ سورة الناس",
        )

        # =================================================
        # TEST 3 - QURAN SURAH FIRST
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 3 - SURAH THEN MODE")
        print("#" * 70)

        dialogue.reset()

        print_turn(
            dialogue,
            "سورة الفلق",
        )

        print_turn(
            dialogue,
            "نقرا",
        )

        # =================================================
        # TEST 4 - LEARNING MULTI TURN
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 4 - LEARNING MULTI-TURN")
        print("#" * 70)

        dialogue.reset()

        print_turn(
            dialogue,
            "ميمي بدي نتعلم",
        )

        print_turn(
            dialogue,
            "الألوان",
        )

        # =================================================
        # TEST 5 - SOCIAL
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 5 - SOCIAL")
        print("#" * 70)

        social_tests = [
            "كيفك",
            "شو اسمك",
            "شو بتقدري تعملي",
            "شكرا ميمي",
            "بحبك ميمي",
            "انتي شطوره",
        ]

        for text in social_tests:

            dialogue.reset()

            print_turn(
                dialogue,
                text,
            )

        # =================================================
        # TEST 6 - EMOTIONS
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 6 - EMOTIONS")
        print("#" * 70)

        emotion_tests = [
            "انا مبسوط",
            "انا زعلان",
            "انا خايف",
            "انا تعبان",
            "انا زهقان",
        ]

        for text in emotion_tests:

            dialogue.reset()

            print_turn(
                dialogue,
                text,
            )

        # =================================================
        # TEST 7 - ACTIVITY MEMORY CONTROL
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 7 - MEMORY CONTROLS")
        print("#" * 70)

        dialogue.reset()

        print_turn(
            dialogue,
            "بدي قصة",
        )

        print_turn(
            dialogue,
            "استني",
        )

        print_turn(
            dialogue,
            "كملي",
        )

        print_turn(
            dialogue,
            "غيري",
        )

        # =================================================
        # TEST 8 - CHILD SPEECH
        # =================================================

        print()
        print()
        print("#" * 70)
        print("TEST 8 - CHILD SPEECH")
        print("#" * 70)

        child_speech = [
            "مييييمي بدييي قصصصه",
            "ممكن تعطيني فزوره",
            "شو واجباتي اليوم",
            "ميمي شغلي الناص",
        ]

        for text in child_speech:

            dialogue.reset()

            print_turn(
                dialogue,
                text,
            )

    finally:

        dialogue.close()


if __name__ == "__main__":

    test_dialogue()