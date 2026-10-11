import random
import threading
from collections import defaultdict, deque


# =========================================================
# MIMI RESPONSE MANAGER
# =========================================================
#
# الهدف:
#
# - Mimi لا تعيد نفس الرد كل مرة
# - ردود قصيرة وسريعة للصوت
# - لغة مناسبة للأطفال
# - تشجيع طبيعي
# - ردود مختلفة حسب الحالة
# - بدون LLM
#
# =========================================================


class ResponseManager:

    def __init__(
        self,
        seed=None,
        history_size=3,
    ):

        self.random = random.Random(
            seed
        )

        self.history_size = (
            history_size
        )

        self.history = defaultdict(
            lambda: deque(
                maxlen=
                    self.history_size
            )
        )

        self.lock = threading.Lock()

        # =================================================
        # RESPONSE LIBRARY
        # =================================================

        self.responses = {

            # =============================================
            # GREETING
            # =============================================

            "greeting": [
                "أهلًا! كيفك اليوم؟",
                "مرحبا! شو بتحب نعمل؟",
                "أهلين! أنا جاهزة.",
                "مرحبا! شو بدك نعمل سوا؟",
            ],

            "greeting_name": [
                "أهلًا {name}! كيفك اليوم؟",
                "مرحبا {name}! شو بتحب نعمل؟",
                "أهلين {name}! أنا جاهزة.",
                "يا أهلًا {name}! شو نعمل سوا؟",
            ],

            # =============================================
            # ACKNOWLEDGEMENT
            # =============================================

            "okay": [
                "تمام.",
                "أوكي.",
                "أكيد.",
                "يلا.",
                "حلو.",
            ],

            "yes": [
                "آه، تمام.",
                "أكيد.",
                "طبعًا.",
                "يلا.",
            ],

            # =============================================
            # PRAISE
            # =============================================

            "praise": [
                "ممتاز!",
                "شطور!",
                "رائع!",
                "أحسنت!",
                "كتير منيح!",
                "برافو!",
            ],

            "strong_praise": [
                "رائع جدًا!",
                "شطور كتير!",
                "ممتاز! كمل هيك.",
                "برافو! عملتها صح.",
            ],

            # =============================================
            # TRY AGAIN
            # =============================================

            "retry": [
                "قريب! جرب مرة ثانية.",
                "منيح، جرب كمان مرة.",
                "قريب جدًا.",
                "يلا نجرب مرة ثانية.",
                "مش مشكلة، حاول كمان مرة.",
            ],

            "gentle_retry": [
                "خد راحتك وجرب مرة ثانية.",
                "ولا يهمك، نجرب سوا.",
                "قريب، اسمع مني وجرب.",
            ],

            # =============================================
            # UNKNOWN
            # =============================================

            "unknown": [
                "ما فهمتك منيح. احكيلي مرة ثانية.",
                "ممكن تعيدها بطريقة ثانية؟",
                "مش متأكدة شو قصدك. احكيلي كمان مرة.",
                "احكيلي شوي أوضح.",
            ],

            "unknown_short": [
                "ممكن تعيد؟",
                "شو قصدك؟",
                "احكيلي كمان مرة.",
            ],

            # =============================================
            # QURAN
            # =============================================

            "quran_mode": [
                "بدك نقرأ ولا نحفظ؟",
                "نقرأ السورة ولا نحفظها؟",
                "بدك تسمع ولا نحفظ سوا؟",
            ],

            "quran_surah": [
                "أي سورة؟",
                "شو اسم السورة؟",
                "أي سورة بتحب؟",
            ],

            "quran_ready": [
                "تمام، يلا نبدأ.",
                "يلا نبدأ سوا.",
                "تمام، جاهزين.",
            ],

            "quran_repeat": [
                "اسمعها مرة ثانية.",
                "خلينا نعيد الآية.",
                "ركز معي ونجرب كمان مرة.",
            ],

            # =============================================
            # LEARNING
            # =============================================

            "learning_topic": [
                "شو بدك نتعلم؟ ألوان، أرقام، حروف، ولا جمع؟",
                "اختار: ألوان، أرقام، حروف، أو جمع.",
                "شو بتحب ندرس سوا؟",
            ],

            "learning_correct": [
                "ممتاز! الجواب صح.",
                "شطور! صح.",
                "رائع! إجابة صحيحة.",
                "برافو!",
            ],

            "learning_wrong": [
                "قريب. جرب كمان مرة.",
                "مش هي، حاول مرة ثانية.",
                "يلا نفكر فيها كمان مرة.",
            ],

            # =============================================
            # STORY
            # =============================================

            "story_start": [
                "أكيد! اسمع القصة.",
                "يلا، نبدأ القصة.",
                "تمام! عندي قصة حلوة.",
            ],

            "story_continue": [
                "يلا نكمل.",
                "اسمع شو صار بعدين.",
                "طيب، وبعدها...",
            ],

            # =============================================
            # RIDDLE
            # =============================================

            "riddle_start": [
                "جاهز للغز؟",
                "يلا نشوف إذا بتحله.",
                "عندي لغز إلك.",
            ],

            "riddle_correct": [
                "صح! شطور.",
                "ممتاز! حليته.",
                "برافو! جوابك صح.",
            ],

            "riddle_wrong": [
                "قريب، جرب كمان.",
                "مش هي. فكر شوي.",
                "يلا حاول مرة ثانية.",
            ],

            # =============================================
            # TASKS
            # =============================================

            "tasks_none": [
                "ما عندك مهام هسا.",
                "خلصت مهامك. ممتاز!",
                "ما في مهام جديدة.",
            ],

            "tasks_have": [
                "عندك {count} مهام.",
                "في عندك {count} مهام.",
            ],

            # =============================================
            # SOCIAL
            # =============================================

            "how_are_you": [
                "أنا منيحة ومبسوطة إني معك.",
                "أنا تمام! وإنت كيفك؟",
                "مبسوطة اليوم. وإنت؟",
            ],

            "thanks": [
                "العفو!",
                "ولو!",
                "أكيد!",
                "على راسي.",
            ],

            "compliment": [
                "شكرا! إنت لطيف.",
                "يسلمو!",
                "شكرا كتير!",
            ],

            "name": [
                "أنا ميمي بوت.",
                "اسمي ميمي.",
                "أنا ميمي، صاحبتك الروبوت.",
            ],

            "capabilities": [
                "بقدر أحكيلك قصص، نحل ألغاز، نقرأ قرآن، نحفظ، ونتعلم سوا.",
                "بقدر أساعدك بالقرآن، القصص، الألغاز، والتعلم.",
            ],

            # =============================================
            # GOODBYE
            # =============================================

            "goodbye": [
                "مع السلامة! بشوفك المرة الجاية.",
                "باي! انبسطت معك.",
                "مع السلامة! يوم سعيد.",
            ],

            # =============================================
            # GLOBAL COMMANDS
            # =============================================

            "stop": [
                "تمام، وقفت.",
                "أوكي، وقفنا.",
                "تمام.",
            ],

            "back": [
                "تمام، رجعنا.",
                "أوكي، نرجع.",
                "رجعنا للقائمة.",
            ],

            "repeat": [
                "أكيد.",
                "تمام، بعيدها.",
                "يلا نعيد.",
            ],

            # =============================================
            # THINKING
            # =============================================
            #
            # ما نستخدمها إلا إذا المعالجة أخذت وقت.
            # حتى ما نبطئ Mimi بدون داعي.
            # =============================================

            "thinking": [
                "ثانية.",
                "تمام، خليني أشوف.",
                "لحظة صغيرة.",
            ],

            # =============================================
            # ERRORS
            # =============================================

            "network_error": [
                "النت بطيء شوي. جرب معي مرة ثانية.",
                "في مشكلة صغيرة بالاتصال.",
            ],

            "system_error": [
                "صار عندي مشكلة صغيرة. جرب مرة ثانية.",
                "لحظة، صار خطأ صغير.",
            ],
        }

    # =====================================================
    # CHOOSE RESPONSE
    # =====================================================

    def choose(
        self,
        key,
        **values,
    ):

        options = self.responses.get(
            key
        )

        if not options:

            return ""

        with self.lock:

            recent = set(
                self.history[
                    key
                ]
            )

            available = [
                response
                for response in options
                if response not in recent
            ]

            # لو استخدمنا كل الردود مؤخرًا
            # نسمح بإعادة الاختيار.
            if not available:

                available = list(
                    options
                )

            response = (
                self.random.choice(
                    available
                )
            )

            self.history[
                key
            ].append(
                response
            )

        try:

            response = (
                response.format(
                    **values
                )
            )

        except Exception:

            pass

        return response

    # =====================================================
    # GREETING
    # =====================================================

    def greeting(
        self,
        name=None,
    ):

        if name:

            return self.choose(
                "greeting_name",
                name=
                    name,
            )

        return self.choose(
            "greeting"
        )

    # =====================================================
    # QURAN
    # =====================================================

    def ask_quran_mode(self):

        return self.choose(
            "quran_mode"
        )

    def ask_surah(self):

        return self.choose(
            "quran_surah"
        )

    def quran_ready(self):

        return self.choose(
            "quran_ready"
        )

    def quran_repeat(self):

        return self.choose(
            "quran_repeat"
        )

    # =====================================================
    # LEARNING
    # =====================================================

    def ask_learning_topic(self):

        return self.choose(
            "learning_topic"
        )

    def learning_correct(self):

        return self.choose(
            "learning_correct"
        )

    def learning_wrong(self):

        return self.choose(
            "learning_wrong"
        )

    # =====================================================
    # UNKNOWN
    # =====================================================

    def unknown(
        self,
        short=False,
    ):

        if short:

            return self.choose(
                "unknown_short"
            )

        return self.choose(
            "unknown"
        )

    # =====================================================
    # PRAISE
    # =====================================================

    def praise(
        self,
        strong=False,
    ):

        if strong:

            return self.choose(
                "strong_praise"
            )

        return self.choose(
            "praise"
        )

    # =====================================================
    # RETRY
    # =====================================================

    def retry(
        self,
        gentle=False,
    ):

        if gentle:

            return self.choose(
                "gentle_retry"
            )

        return self.choose(
            "retry"
        )

    # =====================================================
    # TASK COUNT
    # =====================================================

    def tasks(
        self,
        count,
    ):

        try:

            count = int(
                count
            )

        except Exception:

            count = 0

        if count <= 0:

            return self.choose(
                "tasks_none"
            )

        return self.choose(
            "tasks_have",
            count=
                count,
        )

    # =====================================================
    # SOCIAL
    # =====================================================

    def how_are_you(self):

        return self.choose(
            "how_are_you"
        )

    def thanks(self):

        return self.choose(
            "thanks"
        )

    def compliment(self):

        return self.choose(
            "compliment"
        )

    def name_response(self):

        return self.choose(
            "name"
        )

    def capabilities(self):

        return self.choose(
            "capabilities"
        )

    # =====================================================
    # GLOBAL
    # =====================================================

    def stop(self):

        return self.choose(
            "stop"
        )

    def back(self):

        return self.choose(
            "back"
        )

    def repeat(self):

        return self.choose(
            "repeat"
        )

    def goodbye(self):

        return self.choose(
            "goodbye"
        )

    # =====================================================
    # THINKING
    # =====================================================

    def should_use_thinking(
        self,
        processing_seconds,
        threshold=1.4,
    ):

        try:

            processing_seconds = float(
                processing_seconds
            )

        except Exception:

            return False

        return (
            processing_seconds
            >=
            threshold
        )

    def thinking(self):

        return self.choose(
            "thinking"
        )

    # =====================================================
    # ERROR
    # =====================================================

    def system_error(self):

        return self.choose(
            "system_error"
        )

    def network_error(self):

        return self.choose(
            "network_error"
        )

    # =====================================================
    # RESET HISTORY
    # =====================================================

    def reset_history(self):

        with self.lock:

            self.history.clear()


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    mimi = (
        ResponseManager(
            seed=10
        )
    )

    print()
    print("=" * 70)
    print("🤖 MIMI RESPONSE MANAGER TEST")
    print("=" * 70)

    print()
    print("GREETING:")

    for _ in range(5):

        print(
            mimi.greeting(
                "سارة"
            )
        )

    print()
    print("PRAISE:")

    for _ in range(6):

        print(
            mimi.praise()
        )

    print()
    print("UNKNOWN:")

    for _ in range(4):

        print(
            mimi.unknown()
        )

    print()
    print("QURAN:")

    for _ in range(4):

        print(
            mimi.ask_quran_mode()
        )

    print()
    print("LEARNING:")

    print(
        mimi.ask_learning_topic()
    )

    print()
    print("TASKS:")

    print(
        mimi.tasks(
            0
        )
    )

    print(
        mimi.tasks(
            3
        )
    )

    print()
    print("SOCIAL:")

    print(
        mimi.how_are_you()
    )

    print(
        mimi.name_response()
    )

    print(
        mimi.capabilities()
    )

    print()
    print("=" * 70)
