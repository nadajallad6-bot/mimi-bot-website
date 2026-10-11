import os
import re
import time
from collections import deque

from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_MODEL = os.getenv(
    "MIMI_OPENAI_MODEL",
    "gpt-5.6-sol",
)

MAX_HISTORY_TURNS = 5

MAX_CHILD_TEXT_LENGTH = 400

MAX_RESPONSE_CHARS = 500

AI_TIMEOUT_SECONDS = 15.0


# =========================================================
# MIMI OPEN DOMAIN AI
# =========================================================
#
# هذا الموديول للمحادثة العامة فقط.
#
# أمثلة:
#
# ليش السما زرقا؟
# شو هو المريخ؟
# ليش القطط بتنام كثير؟
#
#
# غير مسؤول عن:
#
# Quran
# Stories
# Learning
# Tasks
# Motors
# Sensors
# Safety actions
#
# =========================================================


class OpenDomainAI:

    def __init__(
        self,
        model=None,
        child_name=None,
        history_size=MAX_HISTORY_TURNS,
    ):

        self.model = (
            model
            or
            DEFAULT_MODEL
        )

        # يبقى محليًا فقط.
        #
        # لا نضيف اسم الطفل للـprompt.
        self.child_name = (
            child_name
        )

        self.history = deque(
            maxlen=max(
                2,
                int(history_size) * 2,
            )
        )

        self.client = None

        self.started = False

        self.available = False

        self.last_error = None

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:

            return self.available

        self.started = True

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:

            print()
            print(
                "⚠️ Open-domain AI disabled."
            )

            print(
                "OPENAI_API_KEY is missing."
            )

            self.available = False

            return False

        try:

            from openai import OpenAI

        except ImportError:

            print()
            print(
                "⚠️ Open-domain AI disabled."
            )

            print(
                "Install package:"
            )

            print(
                "pip install -U openai"
            )

            self.available = False

            return False

        try:

            self.client = OpenAI(
                api_key=api_key,
                timeout=AI_TIMEOUT_SECONDS,
            )

            self.available = True

            print()
            print("=" * 70)

            print(
                "🌐 MIMI OPEN-DOMAIN AI READY"
            )

            print(
                f"Model: {self.model}"
            )

            print(
                "Mode: child-safe fallback only"
            )

            print("=" * 70)

            return True

        except Exception as error:

            self.last_error = str(
                error
            )

            self.available = False

            print()
            print(
                "❌ Open-domain AI startup error:"
            )

            print(
                error
            )

            return False

    # =====================================================
    # CHILD
    # =====================================================

    def set_child(
        self,
        child_name=None,
    ):

        # اسم الطفل يستخدم محليًا فقط
        # لتنظيف النص إذا ظهر داخله.

        self.child_name = (
            child_name
        )

        self.clear_history()

    # =====================================================
    # CLEAR CHILD
    # =====================================================

    def clear_child(self):

        self.child_name = None

        self.clear_history()

    # =====================================================
    # CLEAR HISTORY
    # =====================================================

    def clear_history(self):

        self.history.clear()

    # =====================================================
    # AVAILABLE
    # =====================================================

    def is_available(self):

        if not self.started:

            self.start()

        return self.available

    # =====================================================
    # PRIVACY SANITIZER
    # =====================================================
    #
    # الهدف:
    #
    # لا نرسل:
    #
    # - email
    # - phone
    # - links
    # - أرقام طويلة
    # - اسم الطفل المعروف
    #
    # للـAI الخارجي.
    #
    # =====================================================

    def sanitize_child_text(
        self,
        text,
    ):

        text = str(
            text
            or ""
        ).strip()

        if not text:

            return ""

        # =================================================
        # EMAIL
        # =================================================

        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "[معلومة خاصة]",
            text,
        )

        # =================================================
        # URL
        # =================================================

        text = re.sub(
            r"https?://\S+|www\.\S+",
            "[رابط]",
            text,
            flags=re.IGNORECASE,
        )

        # =================================================
        # LONG NUMBERS
        # =================================================
        #
        # ممكن تكون:
        # phone / ID / account
        #
        # =================================================

        text = re.sub(
            r"\b\d{6,}\b",
            "[رقم خاص]",
            text,
        )

        # =================================================
        # KNOWN CHILD NAME
        # =================================================

        if self.child_name:

            child_name = str(
                self.child_name
            ).strip()

            if child_name:

                text = re.sub(
                    re.escape(
                        child_name
                    ),
                    "الطفل",
                    text,
                    flags=re.IGNORECASE,
                )

        return text.strip()

    # =====================================================
    # INSTRUCTIONS
    # =====================================================

    def build_instructions(self):

        return """
أنت العقل الحواري العام لروبوت أطفال اسمه ميمي بوت.

مهمتك فقط الإجابة عن الأسئلة العامة والمحادثة البسيطة
عندما لا يكون السؤال من وظائف الروبوت المحلية.

تحدث بالعربية البسيطة والواضحة.
يمكنك استخدام أسلوب قريب من اللهجة الفلسطينية.

قواعد Mimi:

1. اجعل الإجابة قصيرة، غالبًا من جملة إلى ثلاث جمل.
2. استخدم كلمات يستطيع الطفل فهمها.
3. كن لطيفًا ومرحًا وهادئًا.
4. إذا كان السؤال غامضًا، اسأل سؤال توضيح قصير.
5. إذا لم تعرف الإجابة، لا تخترع معلومة.
6. لا تطلب الاسم الكامل أو العنوان أو الهاتف أو أي معلومة خاصة.
7. لا تقدم تعليمات خطرة.
8. لا تقدم محتوى جنسيًا أو عنيفًا أو مخيفًا غير مناسب للأطفال.
9. لا تقل إنك نفذت شيئًا في العالم الحقيقي.
10. لا تقل إنك حركت الروبوت أو شغلت حساسًا أو كاميرا.
11. لا تبدأ القرآن أو القصص أو الألغاز أو المهام من هنا.
12. وظائف الروبوت المحلية يديرها Mimi Bot Core.
13. لا تُنشئ أو تؤلف نصوصًا قرآنية.
14. إذا طُلب قرآن، اترك ذلك لقسم القرآن المحلي.
15. إذا كان الطفل في خطر، لا تتولى الحالة؛
    SafetyModule المحلي مسؤول عنها.
16. لا تقل إنك ChatGPT أو API.
17. تحدث كشخصية Mimi Bot.

شخصية ميمي:
ودودة، فضولية، مشجعة، قصيرة الكلام ومناسبة للأطفال.
""".strip()

    # =====================================================
    # BUILD INPUT
    # =====================================================

    def build_input(
        self,
        child_text,
    ):

        messages = []

        # =================================================
        # LOCAL SHORT MEMORY
        # =================================================

        for item in self.history:

            role = (
                item.get(
                    "role"
                )
            )

            content = (
                item.get(
                    "content"
                )
            )

            if (
                role
                and
                content
            ):

                messages.append(
                    {
                        "role":
                            role,

                        "content":
                            content,
                    }
                )

        # =================================================
        # CURRENT QUESTION
        # =================================================

        messages.append(
            {
                "role":
                    "user",

                "content":
                    child_text,
            }
        )

        return messages

    # =====================================================
    # CLEAN RESPONSE
    # =====================================================

    def clean_response(
        self,
        text,
    ):

        text = str(
            text
            or ""
        ).strip()

        if not text:

            return ""

        # =================================================
        # REMOVE EXCESSIVE LINES
        # =================================================

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        # =================================================
        # KEEP VOICE RESPONSE SHORT
        # =================================================

        if (
            len(text)
            >
            MAX_RESPONSE_CHARS
        ):

            shortened = (
                text[
                    :MAX_RESPONSE_CHARS
                ]
            )

            if " " in shortened:

                shortened = (
                    shortened
                    .rsplit(
                        " ",
                        1,
                    )[0]
                )

            text = (
                shortened.strip()
                +
                "."
            )

        return text

    # =====================================================
    # SAFE FALLBACK
    # =====================================================

    def fallback_text(self):

        return (
            "مش قادرة أجاوب على هالسؤال هسا. "
            "جرب اسألني بطريقة ثانية."
        )

    # =====================================================
    # ANSWER
    # =====================================================

    def answer(
        self,
        child_text,
    ):

        child_text = str(
            child_text
            or ""
        ).strip()

        # =================================================
        # EMPTY
        # =================================================

        if not child_text:

            return {
                "success":
                    False,

                "text":
                    None,

                "source":
                    "open_domain_ai",

                "error":
                    "empty_input",
            }

        # =================================================
        # PRIVACY CLEAN
        # =================================================

        safe_text = (
            self.sanitize_child_text(
                child_text
            )
        )

        if not safe_text:

            return {
                "success":
                    False,

                "text":
                    self.fallback_text(),

                "source":
                    "open_domain_ai",

                "error":
                    "empty_after_sanitization",
            }

        # =================================================
        # INPUT LIMIT
        # =================================================

        if (
            len(safe_text)
            >
            MAX_CHILD_TEXT_LENGTH
        ):

            safe_text = (
                safe_text[
                    :MAX_CHILD_TEXT_LENGTH
                ]
            )

        # =================================================
        # START
        # =================================================

        if not self.is_available():

            return {
                "success":
                    False,

                "text":
                    None,

                "source":
                    "open_domain_ai",

                "error":
                    self.last_error
                    or
                    "ai_unavailable",
            }

        started_at = (
            time.monotonic()
        )

        try:

            response = (
                self.client.responses.create(

                    model=
                        self.model,

                    instructions=
                        self.build_instructions(),

                    input=
                        self.build_input(
                            safe_text
                        ),

                    # -------------------------------------
                    # Don't keep Response object state
                    # for our normal Mimi conversation.
                    # -------------------------------------

                    store=
                        False,

                    # -------------------------------------
                    # Child voice responses should remain
                    # short.
                    # -------------------------------------

                    max_output_tokens=
                        180,
                )
            )

            text = (
                self.clean_response(
                    response.output_text
                )
            )

            elapsed = (
                time.monotonic()
                -
                started_at
            )

            if not text:

                return {
                    "success":
                        False,

                    "text":
                        self.fallback_text(),

                    "source":
                        "open_domain_ai",

                    "latency":
                        elapsed,

                    "error":
                        "empty_response",
                }

            # =================================================
            # LOCAL MEMORY ONLY
            # =================================================

            self.history.append(
                {
                    "role":
                        "user",

                    "content":
                        safe_text,
                }
            )

            self.history.append(
                {
                    "role":
                        "assistant",

                    "content":
                        text,
                }
            )

            print()
            print(
                f"🌐 Open-domain response: "
                f"{elapsed:.2f}s"
            )

            return {
                "success":
                    True,

                "text":
                    text,

                "source":
                    "open_domain_ai",

                "model":
                    self.model,

                "latency":
                    elapsed,

                "error":
                    None,
            }

        except Exception as error:

            elapsed = (
                time.monotonic()
                -
                started_at
            )

            self.last_error = (
                str(
                    error
                )
            )

            print()
            print(
                "⚠️ Open-domain AI error:"
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

                "latency":
                    elapsed,

                "error":
                    str(
                        error
                    ),
            }

    # =====================================================
    # STATE
    # =====================================================

    def get_state(self):

        return {
            "started":
                self.started,

            "available":
                self.available,

            "model":
                self.model,

            # Do not expose/send the child name.
            "child_set":
                bool(
                    self.child_name
                ),

            "history_items":
                len(
                    self.history
                ),

            "last_error":
                self.last_error,
        }

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.clear_history()

        self.client = None

        self.available = False

        self.started = False


# =========================================================
# LOCAL TEST - NO API REQUIRED
# =========================================================

def privacy_test():

    ai = (
        OpenDomainAI(
            child_name=
                "سارة"
        )
    )

    tests = [
        "أنا سارة وليش السما زرقا؟",
        "رقمي 0591234567",
        "ايميلي child@example.com",
        "شوف https://example.com",
    ]

    print()
    print("=" * 70)
    print("🔒 MIMI AI PRIVACY TEST")
    print("=" * 70)

    for text in tests:

        print()
        print(
            "Original:"
        )

        print(
            text
        )

        print(
            "Sanitized:"
        )

        print(
            ai.sanitize_child_text(
                text
            )
        )

    print()
    print("=" * 70)


if __name__ == "__main__":

    privacy_test()