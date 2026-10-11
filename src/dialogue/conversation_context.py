import time


# =========================================================
# MIMI CONVERSATION CONTEXT
# =========================================================


class ConversationContext:

    def __init__(
        self,
        timeout_seconds=120,
    ):

        self.timeout_seconds = float(
            timeout_seconds
        )

        self.reset()

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        # -------------------------------------------------
        # Conversation
        # -------------------------------------------------

        self.active = False

        self.started_at = None

        self.updated_at = None

        # -------------------------------------------------
        # Intent
        # -------------------------------------------------

        self.intent = None

        # -------------------------------------------------
        # Slots
        # -------------------------------------------------

        self.slots = {}

        # -------------------------------------------------
        # Waiting state
        # -------------------------------------------------

        self.waiting_for = None

        self.last_question = None

        # -------------------------------------------------
        # Previous interaction
        # -------------------------------------------------

        self.previous_intent = None

        self.previous_slots = {}

    # =====================================================
    # CURRENT TIME
    # =====================================================

    def now(self):

        return time.monotonic()

    # =====================================================
    # EXPIRED?
    # =====================================================

    def is_expired(self):

        if not self.active:

            return False

        if self.updated_at is None:

            return False

        return (
            self.now()
            -
            self.updated_at
            >
            self.timeout_seconds
        )

    # =====================================================
    # TOUCH
    # =====================================================

    def touch(self):

        now = self.now()

        if not self.active:

            self.started_at = (
                now
            )

        self.updated_at = (
            now
        )

        self.active = True

    # =====================================================
    # CHECK TIMEOUT
    # =====================================================

    def check_timeout(self):

        if self.is_expired():

            print()
            print(
                "🕒 Conversation context expired."
            )

            self.reset()

            return True

        return False

    # =====================================================
    # SET INTENT
    # =====================================================

    def set_intent(
        self,
        intent,
    ):

        self.check_timeout()

        self.touch()

        if (
            self.intent
            and
            self.intent != intent
        ):

            self.previous_intent = (
                self.intent
            )

        self.intent = intent

    # =====================================================
    # SET SLOT
    # =====================================================

    def set_slot(
        self,
        name,
        value,
    ):

        if value is None:

            return

        self.check_timeout()

        self.touch()

        self.slots[
            name
        ] = value

    # =====================================================
    # SET MULTIPLE SLOTS
    # =====================================================

    def update_slots(
        self,
        slots,
    ):

        if not slots:

            return

        for (
            name,
            value,
        ) in slots.items():

            if value is not None:

                self.set_slot(
                    name,
                    value,
                )

    # =====================================================
    # GET SLOT
    # =====================================================

    def get_slot(
        self,
        name,
        default=None,
    ):

        self.check_timeout()

        return self.slots.get(
            name,
            default,
        )

    # =====================================================
    # WAIT FOR
    # =====================================================

    def wait_for(
        self,
        slot_name,
        question,
    ):

        self.touch()

        self.waiting_for = (
            slot_name
        )

        self.last_question = (
            question
        )

        print()
        print(
            f"💬 Waiting for: "
            f"{slot_name}"
        )

    # =====================================================
    # CLEAR WAITING
    # =====================================================

    def clear_waiting(self):

        self.waiting_for = None

        self.last_question = None

        self.touch()

    # =====================================================
    # IS WAITING
    # =====================================================

    def is_waiting(self):

        self.check_timeout()

        return (
            self.waiting_for
            is not None
        )

    # =====================================================
    # COMPLETE TURN
    # =====================================================

    def complete_turn(self):

        self.previous_intent = (
            self.intent
        )

        self.previous_slots = dict(
            self.slots
        )

        self.waiting_for = None

        self.last_question = None

        self.touch()

    # =====================================================
    # COMPLETE CONVERSATION
    # =====================================================

    def complete(self):

        self.previous_intent = (
            self.intent
        )

        self.previous_slots = dict(
            self.slots
        )

        self.active = False

        self.intent = None

        self.slots = {}

        self.waiting_for = None

        self.last_question = None

        self.started_at = None

        self.updated_at = None

    # =====================================================
    # STATE
    # =====================================================

    def get_state(self):

        self.check_timeout()

        return {
            "active":
                self.active,

            "intent":
                self.intent,

            "slots":
                dict(
                    self.slots
                ),

            "waiting_for":
                self.waiting_for,

            "last_question":
                self.last_question,

            "previous_intent":
                self.previous_intent,

            "previous_slots":
                dict(
                    self.previous_slots
                ),
        }


# =========================================================
# TEST
# =========================================================

def test_context():

    context = (
        ConversationContext()
    )

    print()
    print("=" * 60)
    print("💬 CONVERSATION CONTEXT TEST")
    print("=" * 60)

    # Child:
    # "بدي قرآن"

    context.set_intent(
        "quran"
    )

    context.wait_for(
        "quran_mode",
        "بدك نقرأ ولا نحفظ؟",
    )

    print()
    print(
        context.get_state()
    )

    # Child:
    # "نحفظ"

    context.set_slot(
        "quran_mode",
        "memorize",
    )

    context.clear_waiting()

    context.wait_for(
        "surah_number",
        "أي سورة؟",
    )

    print()
    print(
        context.get_state()
    )

    # Child:
    # "الفلق"

    context.set_slot(
        "surah_number",
        113,
    )

    context.set_slot(
        "surah_name",
        "الفلق",
    )

    context.clear_waiting()

    print()
    print(
        context.get_state()
    )

    # Conversation finished

    context.complete()

    print()
    print(
        context.get_state()
    )


if __name__ == "__main__":

    test_context()
