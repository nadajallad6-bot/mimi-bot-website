import os
import re
import time
from collections import deque
from pathlib import Path

from dotenv import load_dotenv


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_PATH = (
    PROJECT_ROOT
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH
)


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_MODEL = os.getenv(
    "MIMI_GEMINI_MODEL",
    "gemini-3.6-flash",
)

MAX_HISTORY_TURNS = 5

MAX_CHILD_TEXT_LENGTH = 400

MAX_RESPONSE_CHARS = 500


# =========================================================
# GEMINI OPEN DOMAIN AI
# =========================================================
#
# هذا العقل ليس مسؤولًا عن أوامر الروبوت.
#
# LOCAL MIMI:
#
# Quran
# Story
# Riddle
# Learning
# Tasks
# Adhkar
# Safety
# Robot Commands
#
#
# GEMINI:
#
# General knowledge
# Simple conversation
# Questions outside Mimi local domain
#
# =========================================================


class GeminiOpenDomainAI:

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

        # -------------------------------------------------
        # الاسم LOCAL فقط.
        #
        # لا نرسله للـAI.
        # نستخدمه لحذفه من النص إن ظهر.
        # -------------------------------------------------

        self.child_name = (
            child_name
        )

        # -------------------------------------------------
        # ذاكرة قصيرة LOCAL RAM.
        # -------------------------------------------------

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

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.started:

            return self.available

        self.started = True

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            self.available = False

            self.last_error = (
                "GEMINI_API_KEY is missing"
            )

            print()
            print(
                "⚠️ Gemini AI disabled:"
            )

            print(
                "GEMINI_API_KEY is missing."
            )

            return False

        # =================================================
        # IMPORT GOOGLE GENAI SDK
        # =================================================

        try:

            from google import genai

        except ImportError:

            self.available = False

            self.last_error = (
                "google-genai package "
                "is not installed"
            )

            print()
            print(
                "⚠️ Gemini AI disabled:"
            )

            print(
                "google-genai is not installed."
            )

            return False

        # =================================================
        # CLIENT
        # =================================================

        try:

            self.client = (
                genai.Client(
                    api_key=api_key
                )
            )

            self.available = True
            self.last_error = None

            print()
            print("=" * 70)

            print(
                "🌐 MIMI GEMINI OPEN-DOMAIN AI READY"
            )

            print("=" * 70)

            print(
                f"Model : {self.model}"
            )

            print(
                "API   : Interactions"
            )

            print(
                "Store : False"
            )

            print(
                "Role  : general questions only"
            )

            print("=" * 70)

            return True

        except Exception as error:

            self.available = False

            self.last_error = str(
                error
            )

            print()
            print(
                "❌ Gemini startup error:"
            )

            print(
                error
            )

            return False

    # =====================================================
    # AVAILABILITY
    # =====================================================

    def is_available(self):

        if not self.started:

            self.start()

        return bool(
            self.available
        )

    # =====================================================
    # SET CHILD
    # =====================================================

    def set_child(
        self,
        child_name=None,
    ):

        self.child_name = (
            child_name
        )

        self.clear_history()

        return True

    # =====================================================
    # CLEAR CHILD
    # =====================================================

    def clear_child(self):

        self.child_name = None

        self.clear_history()

        return True

    # =====================================================
    # CLEAR HISTORY
    # =====================================================

    def clear_history(self):

        self.history.clear()

        return True

    # =====================================================
    # PRIVACY SANITIZER
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
            (
                r"\b"
                r"[A-Za-z0-9._%+-]+"
                r"@"
                r"[A-Za-z0-9.-]+"
                r"\.[A-Za-z]{2,}"
                r"\b"
            ),
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
        # LONG NUMBER
        # =================================================

        text = re.sub(
            r"(?<!\d)\d{6,}(?!\d)",
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

        # =================================================
        # SPACES
        # =================================================

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =====================================================
    # SYSTEM INSTRUCTION
    # =====================================================

    def build_system_instruction(self):

        return """
أنت العقل الحواري العام لروبوت أطفال اسمه ميمي بوت.

يتم استدعاؤك فقط عندما يكون كلام الطفل خارج الوظائف
المحلية التي يستطيع Mimi Bot تنفيذها بنفسه.

تحدث بالعربية البسيطة والواضحة.
استخدم أسلوبًا طبيعيًا قريبًا من اللهجة الفلسطينية
عندما يكون ذلك مناسبًا.

قواعد إلزامية:

1. اجعل الإجابة قصيرة عادة من جملة إلى ثلاث جمل.

2. استخدم كلمات سهلة ومناسبة لطفل.

3. كن ودودًا ومرحًا ومشجعًا.

4. إذا كان السؤال غير واضح،
اسأل سؤال توضيح قصيرًا.

5. إذا لم تكن متأكدًا من معلومة،
لا تخترع الإجابة.

6. لا تطلب معلومات شخصية من الطفل مثل:
الاسم الكامل،
العنوان،
رقم الهاتف،
البريد الإلكتروني،
اسم المدرسة،
كلمات المرور،
أرقام الهوية،
أو الحسابات.

7. لا تقدم تعليمات خطرة أو مؤذية.

8. لا تقدم محتوى جنسيًا أو عنيفًا
أو مخيفًا غير مناسب للأطفال.

9. لا تدعِ أنك شغلت أو تحكمت في:
الموتورات،
الحساسات،
الكاميرا،
الشاشة،
السماعة،
أو أي قطعة Hardware.

10. لا تدعِ أنك نفذت أمرًا داخل Mimi Bot.

11. لا تبدأ قراءة القرآن من هنا.

12. لا تنشئ ولا تؤلف ولا تكمل آيات قرآنية.

13. QuranModule المحلي الموثوق مسؤول عن القرآن.

14. لا تشغل StoryModule أو RiddleModule
أو LearningModule أو TaskModule.

15. لا تتحكم في SafetyModule.

16. أوامر الخطر والطوارئ مسؤول عنها
النظام المحلي في Mimi Bot.

17. لا تقل إنك Gemini أو API أو نموذج لغوي.

18. تحدث دائمًا كشخصية Mimi Bot.

19. لا تستخدم تنسيق Markdown معقدًا،
لأن الرد سيقرأ بصوت.

20. لا تعطِ إجابات طويلة إلا إذا طلب الطفل ذلك.

شخصية ميمي:
لطيفة،
فضولية،
مرحة،
هادئة،
مشجعة،
وقصيرة الكلام.
""".strip()

    # =====================================================
    # BUILD LOCAL CONTEXT
    # =====================================================
    #
    # نحن نستخدم store=False.
    #
    # لذلك كل سؤال Gemini Interaction مستقل.
    #
    # نحافظ فقط على كمية صغيرة جدًا من الحوار
    # محليًا ونضعها كنص داخل السؤال.
    #
    # =====================================================

    def build_input(
        self,
        child_text,
    ):

        lines = []

        if self.history:

            lines.append(
                "سياق محادثة قصير:"
            )

            for item in self.history:

                role = (
                    item.get(
                        "role"
                    )
                )

                content = str(
                    item.get(
                        "content"
                    )
                    or ""
                ).strip()

                if not content:

                    continue

                if role == "user":

                    lines.append(
                        f"الطفل: {content}"
                    )

                elif role == "assistant":

                    lines.append(
                        f"ميمي: {content}"
                    )

            lines.append(
                ""
            )

        lines.append(
            "الكلام الحالي للطفل:"
        )

        lines.append(
            child_text
        )

        lines.append(
            ""
        )

        lines.append(
            "جاوب فقط على الكلام الحالي "
            "مع الاستفادة من السياق إذا احتجته."
        )

        return "\n".join(
            lines
        )

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
        # MARKDOWN CLEAN
        # =================================================

        text = (
            text
            .replace(
                "**",
                ""
            )
            .replace(
                "__",
                ""
            )
            .replace(
                "###",
                ""
            )
        )

        # =================================================
        # WHITESPACE
        # =================================================

        text = re.sub(
            r"\n{2,}",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # =================================================
        # LENGTH LIMIT
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

        return text.strip()

    # =====================================================
    # FALLBACK TEXT
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
                    "gemini_open_domain_ai",

                "provider":
                    "gemini",

                "error":
                    "empty_input",
            }

        # =================================================
        # SANITIZE
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
                    "gemini_open_domain_ai",

                "provider":
                    "gemini",

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
                    "gemini_open_domain_ai",

                "provider":
                    "gemini",

                "error":
                    self.last_error
                    or
                    "gemini_unavailable",
            }

        # =================================================
        # COUNT REQUEST
        # =================================================

        self.total_requests += 1

        started_at = (
            time.monotonic()
        )

        # =================================================
        # INPUT
        # =================================================

        request_input = (
            self.build_input(
                safe_text
            )
        )

        # =================================================
        # INTERACTIONS API
        # =================================================

        try:

            interaction = (
                self.client
                .interactions
                .create(

                    model=
                        self.model,

                    input=
                        request_input,

                    system_instruction=
                        self.build_system_instruction(),

                    # -------------------------------------
                    # We intentionally do not use
                    # previous_interaction_id.
                    #
                    # Mimi manages short context locally.
                    # -------------------------------------

                    store=
                        False,

                    generation_config={
                        "thinking_level":
                            "low",
                    },
                )
            )

            elapsed = (
                time.monotonic()
                -
                started_at
            )

            # =================================================
            # OUTPUT
            # =================================================

            raw_text = str(
                getattr(
                    interaction,
                    "output_text",
                    "",
                )
                or ""
            )

            text = (
                self.clean_response(
                    raw_text
                )
            )

            # =================================================
            # EMPTY
            # =================================================

            if not text:

                self.failed_requests += 1

                return {
                    "success":
                        False,

                    "text":
                        self.fallback_text(),

                    "source":
                        "gemini_open_domain_ai",

                    "provider":
                        "gemini",

                    "model":
                        self.model,

                    "latency":
                        elapsed,

                    "error":
                        "empty_response",
                }

            # =================================================
            # LOCAL SANITIZED HISTORY
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

            self.successful_requests += 1

            self.last_error = None

            print()
            print(
                f"🌐 Gemini answer "
                f"in {elapsed:.2f}s"
            )

            return {
                "success":
                    True,

                "text":
                    text,

                "source":
                    "gemini_open_domain_ai",

                "provider":
                    "gemini",

                "model":
                    self.model,

                "latency":
                    elapsed,

                "error":
                    None,
            }

        # =================================================
        # ERROR
        # =================================================

        except Exception as error:

            elapsed = (
                time.monotonic()
                -
                started_at
            )

            self.failed_requests += 1

            self.last_error = str(
                error
            )

            print()
            print(
                "⚠️ Gemini Open-Domain AI error:"
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
                    "gemini_open_domain_ai",

                "provider":
                    "gemini",

                "model":
                    self.model,

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

            "provider":
                "gemini",

            "model":
                self.model,

            "child_set":
                bool(
                    self.child_name
                ),

            "history_items":
                len(
                    self.history
                ),

            "total_requests":
                self.total_requests,

            "successful_requests":
                self.successful_requests,

            "failed_requests":
                self.failed_requests,

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

        return True


# =========================================================
# REAL TEST
# =========================================================


def run_test():

    ai = (
        GeminiOpenDomainAI(
            child_name="سارة"
        )
    )

    try:

        print()
        print("=" * 70)
        print(
            "🧪 MIMI GEMINI TEST"
        )
        print("=" * 70)

        started = (
            ai.start()
        )

        print(
            "START:",
            started,
        )

        if not started:

            print(
                "ERROR:",
                ai.last_error,
            )

            return

        tests = [
            "ليش السما زرقا؟",
            "شو هو كوكب المريخ؟",
        ]

        for question in tests:

            print()
            print(
                "👧 CHILD:",
                question,
            )

            result = (
                ai.answer(
                    question
                )
            )

            print(
                "SUCCESS:",
                result.get(
                    "success"
                )
            )

            print(
                "MIMI:",
                result.get(
                    "text"
                )
            )

            print(
                "LATENCY:",
                result.get(
                    "latency"
                )
            )

            print(
                "ERROR:",
                result.get(
                    "error"
                )
            )

        print()
        print(
            "STATE:"
        )

        print(
            ai.get_state()
        )

    finally:

        ai.close()


if __name__ == "__main__":

    run_test()