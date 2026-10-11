from src.ai.hybrid_ai_router import (
    HybridAIRouter,
)

from src.dialogue.dialogue_manager import (
    DialogueManager,
)


# =========================================================
# MIMI HYBRID DIALOGUE MANAGER
# =========================================================
#
# المسؤولية:
#
# 1. الحفاظ على DialogueManager المحلي كما هو.
#
# 2. إذا Mimi تنتظر جوابًا:
#       نستخدم الحوار المحلي فقط.
#
# 3. إذا الجملة من وظائف Mimi:
#       Local DialogueManager.
#
# 4. إذا السؤال خارج وظائف Mimi:
#       Open-Domain AI.
#
#
# مثال:
#
# "بدي قرآن"
#       ↓
# Local
#
# "الملك"
# بعد سؤال "أي سورة؟"
#       ↓
# Local Context
#
# "ليش القمر منور؟"
#       ↓
# Open-Domain AI
#
# =========================================================


class HybridDialogueManager:

    def __init__(
        self,
        dialogue_manager=None,
        ai_router=None,
    ):

        # =================================================
        # LOCAL DIALOGUE
        # =================================================

        self.local = (
            dialogue_manager
            if dialogue_manager is not None
            else DialogueManager()
        )

        # =================================================
        # HYBRID ROUTER
        # =================================================

        self.router = (
            ai_router
            if ai_router is not None
            else HybridAIRouter()
        )

        self.started = False

        # =================================================
        # LAST STATE
        # =================================================

        self.last_route = None

        self.last_route_reason = None

        self.last_ai_latency = None

    # =====================================================
    # COMPATIBILITY PROPERTIES
    # =====================================================
    #
    # mimi_bot.py الحالي يستخدم:
    #
    # self.dialogue.context
    # self.dialogue.nlu
    # self.dialogue.memory
    #
    # لذلك نكشف نفس الـAPI.
    #
    # =====================================================

    @property
    def context(self):

        return self.local.context

    @property
    def nlu(self):

        return self.local.nlu

    @property
    def memory(self):

        return getattr(
            self.local,
            "memory",
            None,
        )

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:

            return True

        print()
        print("=" * 70)
        print(
            "🧠 STARTING MIMI HYBRID DIALOGUE"
        )
        print("=" * 70)

        self.local.start()

        self.router.start()

        self.started = True

        print()
        print(
            "✅ Local Mimi brain ready."
        )

        print(
            "✅ Hybrid AI router ready."
        )

        print(
            "✅ Open-domain fallback ready."
        )

        print("=" * 70)

        return True

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.local.reset()

        self.last_route = None

        self.last_route_reason = None

        self.last_ai_latency = None

        return True

    # =====================================================
    # SET CHILD
    # =====================================================

    def set_child(
        self,
        child_name=None,
    ):

        # Open-domain component uses child name
        # locally only for sanitization.

        try:

            self.router.set_child(
                child_name
            )

        except Exception:

            pass

        return True

    # =====================================================
    # CLEAR CHILD
    # =====================================================

    def clear_child(self):

        try:

            self.router.clear_child()

        except Exception:

            pass

        return True

    # =====================================================
    # IS WAITING
    # =====================================================

    def is_dialogue_waiting(self):

        try:

            return bool(
                self.context.is_waiting()
            )

        except Exception:

            return False

    # =====================================================
    # BUILD OPEN DOMAIN RESULT
    # =====================================================

    def build_open_domain_result(
        self,
        text,
        nlu_result,
        ai_result,
        reason,
    ):

        ai_result = (
            ai_result
            if isinstance(
                ai_result,
                dict,
            )
            else {}
        )

        success = bool(
            ai_result.get(
                "success",
                False,
            )
        )

        response_text = (
            ai_result.get(
                "text"
            )
        )

        if success and response_text:

            try:

                self.last_ai_latency = float(
                    ai_result.get(
                        "latency",
                        0.0,
                    )
                    or 0.0
                )

            except Exception:

                self.last_ai_latency = None

            return {
                "handled":
                    True,

                # -----------------------------------------
                # mimi_bot.py الحالي يعرف action="ask"
                # ويقرأ response بصوت Mimi.
                #
                # ما في سؤال pending فعلي هنا.
                # -----------------------------------------

                "action":
                    "ask",

                "ready_to_execute":
                    False,

                "intent":
                    "open_domain",

                "slots":
                    {},

                "response":
                    response_text,

                "question":
                    None,

                "waiting_for":
                    None,

                "nlu":
                    nlu_result,

                "route":
                    "open_domain",

                "route_reason":
                    reason,

                "ai":
                    ai_result,

                "context":
                    self.context.get_state(),
            }

        # =================================================
        # AI UNAVAILABLE FALLBACK
        # =================================================

        return {
            "handled":
                True,

            "action":
                "ask",

            "ready_to_execute":
                False,

            "intent":
                "open_domain_unavailable",

            "slots":
                {},

            "response":
                (
                    "هالسؤال بدّه مني أفكر شوي، "
                    "بس مش قادرة أوصل لعقلي العام هسا. "
                    "جرب اسألني بعد شوي."
                ),

            "question":
                None,

            "waiting_for":
                None,

            "nlu":
                nlu_result,

            "route":
                "open_domain",

            "route_reason":
                reason,

            "ai":
                ai_result,

            "context":
                self.context.get_state(),
        }

    # =====================================================
    # PROCESS
    # =====================================================

    def process(
        self,
        text,
    ):

        if not self.started:

            self.start()

        text = str(
            text
            or ""
        ).strip()

        print()
        print("=" * 70)
        print(
            "🧠 HYBRID DIALOGUE INPUT"
        )
        print("=" * 70)

        print(
            f"👧 Child: {text}"
        )

        # =================================================
        # EMPTY
        # =================================================

        if not text:

            return self.local.process(
                text
            )

        # =================================================
        # 1. ACTIVE MULTI-TURN DIALOGUE
        # =================================================
        #
        # أهم قاعدة:
        #
        # Mimi:
        #   أي سورة؟
        #
        # Child:
        #   الملك
        #
        # ممنوع تمر على Open AI.
        #
        # =================================================

        if self.is_dialogue_waiting():

            self.last_route = (
                "local"
            )

            self.last_route_reason = (
                "dialogue_waiting"
            )

            print(
                "🏠 Route: LOCAL "
                "(pending dialogue)"
            )

            return self.local.process(
                text
            )

        # =================================================
        # 2. LOCAL NLU PRE-CHECK
        # =================================================
        #
        # نعم، حاليًا Local DialogueManager قد يعمل
        # NLU مرة ثانية إذا route=local.
        #
        # هذا مقصود في النسخة الأولى للحفاظ على
        # DialogueManager القديم بدون كسره.
        #
        # NLU المحلي سريع جدًا مقارنة بـ STT/TTS.
        #
        # لاحقًا نزيل التكرار عند إعادة التنظيم.
        #
        # =================================================

        try:

            nlu_result = (
                self.nlu.understand(
                    text
                )
            )

        except Exception as error:

            print()
            print(
                "⚠️ Hybrid NLU pre-check error:"
            )

            print(
                error
            )

            self.last_route = (
                "local"
            )

            self.last_route_reason = (
                "nlu_error_local_fallback"
            )

            return self.local.process(
                text
            )

        # =================================================
        # 3. ROUTE DECISION
        # =================================================

        try:

            decision = (
                self.router.decide(
                    text,
                    nlu_result,

                    dialogue_waiting=
                        False,

                    activity_active=
                        False,
                )
            )

        except Exception as error:

            print()
            print(
                "⚠️ AI Router decision error:"
            )

            print(
                error
            )

            self.last_route = (
                "local"
            )

            self.last_route_reason = (
                "router_error_local_fallback"
            )

            return self.local.process(
                text
            )

        self.last_route = (
            decision.route
        )

        self.last_route_reason = (
            decision.reason
        )

        print()
        print(
            f"🚦 Route: "
            f"{decision.route}"
        )

        print(
            f"📌 Reason: "
            f"{decision.reason}"
        )

        # =================================================
        # 4. LOCAL MIMI
        # =================================================

        if (
            decision.route
            ==
            "local"
        ):

            return self.local.process(
                text
            )

        # =================================================
        # 5. OPEN DOMAIN AI
        # =================================================

        if (
            decision.route
            ==
            "open_domain"
        ):

            print()
            print(
                "🌐 Sending general question "
                "to Open-Domain AI..."
            )

            try:

                ai_result = (
                    self.router.ask_open_domain(
                        text
                    )
                )

            except Exception as error:

                ai_result = {
                    "success":
                        False,

                    "text":
                        None,

                    "error":
                        str(
                            error
                        ),
                }

            return (
                self.build_open_domain_result(
                    text=
                        text,

                    nlu_result=
                        nlu_result,

                    ai_result=
                        ai_result,

                    reason=
                        decision.reason,
                )
            )

        # =================================================
        # UNKNOWN ROUTE → LOCAL SAFE FALLBACK
        # =================================================

        self.last_route = (
            "local"
        )

        self.last_route_reason = (
            "unknown_route_local_fallback"
        )

        return self.local.process(
            text
        )

    # =====================================================
    # PRINT RESULT
    # =====================================================

    def print_result(
        self,
        result,
    ):

        if not isinstance(
            result,
            dict,
        ):

            print(
                result
            )

            return

        print()
        print("=" * 70)
        print(
            "🧠 HYBRID DIALOGUE RESULT"
        )
        print("=" * 70)

        print(
            f"Route   : "
            f"{result.get('route', self.last_route)}"
        )

        print(
            f"Reason  : "
            f"{result.get('route_reason', self.last_route_reason)}"
        )

        print(
            f"Action  : "
            f"{result.get('action')}"
        )

        print(
            f"Intent  : "
            f"{result.get('intent')}"
        )

        print(
            f"Waiting : "
            f"{result.get('waiting_for')}"
        )

        print(
            f"Slots   : "
            f"{result.get('slots')}"
        )

        if result.get(
            "response"
        ):

            print()
            print(
                f"🤖 Mimi: "
                f"{result.get('response')}"
            )

        ai = (
            result.get(
                "ai"
            )
        )

        if isinstance(
            ai,
            dict,
        ):

            print()
            print(
                f"AI success: "
                f"{ai.get('success')}"
            )

            print(
                f"AI latency: "
                f"{ai.get('latency')}"
            )

        print("=" * 70)

    # =====================================================
    # STATE
    # =====================================================

    def get_state(self):

        return {
            "started":
                self.started,

            "last_route":
                self.last_route,

            "last_route_reason":
                self.last_route_reason,

            "last_ai_latency":
                self.last_ai_latency,

            "local_context":
                self.context.get_state(),
        }

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        print()
        print(
            "🧹 Closing Hybrid Dialogue..."
        )

        try:

            self.router.close()

        except Exception:

            pass

        try:

            self.local.close()

        except Exception:

            pass

        self.started = False

        print(
            "✅ Hybrid Dialogue closed."
        )


# =========================================================
# FAKE OPEN DOMAIN AI FOR TESTING
# =========================================================
#
# هذا فقط لاختبار الـarchitecture بدون API key.
#
# =========================================================


class _FakeOpenDomainAI:

    def __init__(self):

        self.started = False

    def start(self):

        self.started = True

        return True

    def set_child(
        self,
        child_name=None,
    ):

        return True

    def clear_child(self):

        return True

    def answer(
        self,
        text,
    ):

        return {
            "success":
                True,

            "text":
                (
                    "هذا جواب تجريبي من "
                    "العقل العام لميمي."
                ),

            "source":
                "fake_open_domain_ai",

            "latency":
                0.01,

            "error":
                None,
        }

    def close(self):

        self.started = False


# =========================================================
# STANDALONE TEST
# =========================================================


def run_test():

    fake_ai = (
        _FakeOpenDomainAI()
    )

    router = (
        HybridAIRouter(
            open_domain_ai=
                fake_ai
        )
    )

    dialogue = (
        HybridDialogueManager(
            ai_router=
                router
        )
    )

    dialogue.start()

    tests = [
        "مرحبا ميمي",
        "كيفك",
        "بدي قصة",
        "ليش السما زرقا",
        "مين اخترع الطيارة",
        "بدي قرآن",
        "نحفظ",
        "الملك",
    ]

    try:

        for text in tests:

            print()
            print()
            print(
                "#" * 70
            )

            print(
                f"👧 TEST: {text}"
            )

            result = (
                dialogue.process(
                    text
                )
            )

            dialogue.print_result(
                result
            )

    finally:

        dialogue.close()


if __name__ == "__main__":

    run_test()
