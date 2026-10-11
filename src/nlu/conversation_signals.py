from difflib import SequenceMatcher

from src.nlu.child_language_normalizer import (
    ChildLanguageNormalizer,
)


# =========================================================
# MIMI CONVERSATION SIGNALS
# =========================================================
#
# هذه الطبقة مسؤولة عن الكلام القصير والطبيعي:
#
# كيفك؟
# شو اسمك؟
# شكرا
# بحبك
# أنا زعلان
# آه
# لا
# كملي
# غيري
# استني
# مش فاهم
#
# لماذا Rules هنا؟
#
# لأن جمل مثل:
#
#   آه
#   لا
#   كملي
#
# قصيرة جدًا وقد لا تكون مناسبة لوحدها
# لتصنيف Machine Learning.
#
# =========================================================


class ConversationSignals:

    def __init__(
        self,
        fuzzy_threshold=0.84,
    ):

        self.normalizer = (
            ChildLanguageNormalizer()
        )

        self.fuzzy_threshold = (
            fuzzy_threshold
        )

        # =================================================
        # SOCIAL
        # =================================================

        self.social_phrases = {

            # -------------------------------------------------
            # How are you?
            # -------------------------------------------------

            "how_are_you": {
                "كيفك",
                "كيف حالك",
                "شو اخبارك",
                "شو اخبارك ميمي",
                "كيفك اليوم",
                "انتي منيحه",
                "انتي بخير",
            },

            # -------------------------------------------------
            # Mimi name
            # -------------------------------------------------

            "robot_name": {
                "شو اسمك",
                "ايش اسمك",
                "ايش اسمك انتي",
                "انتي مين",
                "مين انتي",
                "شو بناديكي",
                "اسمك ايش",
                "اسمك شو",
            },

            # -------------------------------------------------
            # Capabilities
            # -------------------------------------------------

            "capabilities": {
                "شو بتعملي",
                "شو بتقدري تعملي",
                "شو بتعرفي تعملي",
                "شو في عندك",
                "شو ممكن نعمل",
                "شو نعمل",
                "بشو بتساعديني",
                "شو بتعرفي",
                "ايش بتقدري تعملي",
            },

            # -------------------------------------------------
            # Thanks
            # -------------------------------------------------

            "thanks": {
                "شكرا",
                "شكرا ميمي",
                "يسلمو",
                "ثانك يو",
                "مشكوره",
                "يعطيكي العافيه",
            },

            # -------------------------------------------------
            # Compliment
            # -------------------------------------------------

            "compliment": {
                "انتي شطوره",
                "انتي حلوه",
                "صوتك حلو",
                "انتي لطيفه",
                "انتي رائعه",
                "ميمي شطوره",
                "بحب صوتك",
            },

            # -------------------------------------------------
            # Affection
            # -------------------------------------------------

            "affection": {
                "بحبك",
                "انا بحبك",
                "بحبك ميمي",
                "انتي صاحبتي",
                "انتي صديقتي",
                "انا بحب ميمي",
            },
        }

        # =================================================
        # CHILD EMOTIONS
        # =================================================

        self.emotion_phrases = {

            "child_happy": {
                "انا مبسوط",
                "انا مبسوطه",
                "مبسوط",
                "مبسوطه",
                "انا فرحان",
                "انا فرحانه",
                "فرحان",
                "فرحانه",
                "انا سعيد",
                "انا سعيده",
                "اليوم مبسوط",
            },

            "child_sad": {
                "انا زعلان",
                "انا زعلانه",
                "زعلان",
                "زعلانه",
                "انا حزين",
                "انا حزينه",
                "متضايق",
                "متضايقه",
                "انا متضايق",
                "انا متضايقه",
            },

            "child_scared": {
                "انا خايف",
                "انا خايفه",
                "خايف",
                "خايفه",
                "انا خائف",
                "انا خائفه",
                "بخاف",
                "انا بخاف",
            },

            "child_tired": {
                "انا تعبان",
                "انا تعبانه",
                "تعبان",
                "تعبانه",
                "انا نعسان",
                "انا نعسانه",
                "نعسان",
                "نعسانه",
            },

            "child_bored": {
                "انا زهقان",
                "انا زهقانه",
                "زهقان",
                "زهقانه",
                "طفشان",
                "طفشانه",
                "انا طفشان",
                "انا طفشانه",
                "ملان",
                "مليت",
            },
        }

        # =================================================
        # DIALOGUE CONTROL
        # =================================================

        self.dialogue_phrases = {

            # -------------------------------------------------
            # Yes
            # -------------------------------------------------

            "yes": {
                "اه",
                "ايوه",
                "ايوا",
                "نعم",
                "اوك",
                "تمام",
                "ماشي",
                "يلا",
            },

            # -------------------------------------------------
            # No
            # -------------------------------------------------

            "no": {
                "لا",
                "لأ",
                "لا لا",
                "مش بدي",
                "ما بدي",
                "مش هيك",
            },

            # -------------------------------------------------
            # Continue
            # -------------------------------------------------

            "continue": {
                "كملي",
                "كمل",
                "واصلي",
                "يلا كملي",
                "كملي ميمي",
                "بعدها",
                "وبعدين",
                "شو صار بعدين",
            },

            # -------------------------------------------------
            # Change
            # -------------------------------------------------

            "change": {
                "غيري",
                "غير",
                "بدي غيرها",
                "واحده ثانيه",
                "وحده ثانيه",
                "اشي ثاني",
                "شي ثاني",
                "مش هاي",
            },

            # -------------------------------------------------
            # Wait
            # -------------------------------------------------

            "wait": {
                "استني",
                "استنا",
                "لحظه",
                "اصبري",
                "شوي",
                "دقيقه",
            },

            # -------------------------------------------------
            # Repeat
            # -------------------------------------------------

            "repeat": {
                "عيدي",
                "عيد",
                "كرري",
                "كرر",
                "مره ثانيه",
                "كمان مره",
                "عيديها",
            },

            # -------------------------------------------------
            # Child didn't understand Mimi
            # -------------------------------------------------

            "did_not_understand": {
                "مش فاهم",
                "مش فاهمه",
                "ما فهمت",
                "مش فاهم شو قلتي",
                "شو قلتي",
                "احكيها مره ثانيه",
                "مفهمتش",
            },
        }

        # =================================================
        # FLAT INDEX
        # =================================================

        self.phrase_index = []

        self._build_index()

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

        return (
            result.get(
                "canonical",
                ""
            )
            or
            result.get(
                "normalized",
                ""
            )
            or
            ""
        )

    # =====================================================
    # BUILD INDEX
    # =====================================================

    def _build_index(self):

        self.phrase_index.clear()

        groups = [
            (
                "social",
                self.social_phrases,
            ),

            (
                "emotion",
                self.emotion_phrases,
            ),

            (
                "dialogue",
                self.dialogue_phrases,
            ),
        ]

        for (
            category,
            mapping,
        ) in groups:

            for (
                intent,
                phrases,
            ) in mapping.items():

                for phrase in phrases:

                    normalized = (
                        self.normalize(
                            phrase
                        )
                    )

                    if not normalized:

                        continue

                    self.phrase_index.append(
                        {
                            "category":
                                category,

                            "intent":
                                intent,

                            "phrase":
                                normalized,
                        }
                    )

    # =====================================================
    # SIMILARITY
    # =====================================================

    def similarity(
        self,
        first,
        second,
    ):

        return (
            SequenceMatcher(
                None,
                first,
                second,
            ).ratio()
        )

    # =====================================================
    # EXACT MATCH
    # =====================================================

    def exact_match(
        self,
        normalized_text,
    ):

        for item in self.phrase_index:

            if (
                normalized_text
                ==
                item[
                    "phrase"
                ]
            ):

                return {
                    "matched":
                        True,

                    "intent":
                        item[
                            "intent"
                        ],

                    "category":
                        item[
                            "category"
                        ],

                    "confidence":
                        1.0,

                    "source":
                        "conversation_exact",

                    "matched_phrase":
                        item[
                            "phrase"
                        ],
                }

        return None

    # =====================================================
    # SAFE TOKEN MATCH
    # =====================================================
    #
    # نستخدمه لبعض المشاعر:
    #
    # "انا اليوم كتير زعلان"
    #
    # لو phrase:
    #
    # "زعلان"
    #
    # نقدر نلتقطها.
    #
    # لكن لا نستخدم substring حرفي.
    # =====================================================

    def token_match(
        self,
        normalized_text,
    ):

        text_tokens = set(
            normalized_text.split()
        )

        if not text_tokens:

            return None

        # =================================================
        # EMOTION KEYWORDS
        # =================================================

        emotion_keywords = {

            "child_happy": {
                "مبسوط",
                "مبسوطه",
                "فرحان",
                "فرحانه",
                "سعيد",
                "سعيده",
            },

            "child_sad": {
                "زعلان",
                "زعلانه",
                "حزين",
                "حزينه",
                "متضايق",
                "متضايقه",
            },

            "child_scared": {
                "خايف",
                "خايفه",
                "خائف",
                "خائفه",
            },

            "child_tired": {
                "تعبان",
                "تعبانه",
                "نعسان",
                "نعسانه",
            },

            "child_bored": {
                "زهقان",
                "زهقانه",
                "طفشان",
                "طفشانه",
                "مليت",
            },
        }

        for (
            intent,
            words,
        ) in emotion_keywords.items():

            overlap = (
                text_tokens
                &
                words
            )

            if overlap:

                return {
                    "matched":
                        True,

                    "intent":
                        intent,

                    "category":
                        "emotion",

                    "confidence":
                        0.96,

                    "source":
                        "conversation_tokens",

                    "matched_phrase":
                        next(
                            iter(
                                overlap
                            )
                        ),
                }

        return None

    # =====================================================
    # FUZZY MATCH
    # =====================================================

    def fuzzy_match(
        self,
        normalized_text,
    ):

        # -------------------------------------------------
        # Important safety:
        #
        # لا نعمل fuzzy قوي على كلمة من حرفين فقط.
        # -------------------------------------------------

        if len(
            normalized_text.replace(
                " ",
                "",
            )
        ) < 4:

            return None

        best = None

        for item in self.phrase_index:

            phrase = (
                item[
                    "phrase"
                ]
            )

            # Avoid fuzzy matching tiny phrases
            if len(
                phrase.replace(
                    " ",
                    "",
                )
            ) < 4:

                continue

            score = (
                self.similarity(
                    normalized_text,
                    phrase,
                )
            )

            if (
                best is None
                or
                score
                >
                best[
                    "confidence"
                ]
            ):

                best = {
                    "matched":
                        True,

                    "intent":
                        item[
                            "intent"
                        ],

                    "category":
                        item[
                            "category"
                        ],

                    "confidence":
                        score,

                    "source":
                        "conversation_fuzzy",

                    "matched_phrase":
                        phrase,
                }

        if (
            best is not None
            and
            best[
                "confidence"
            ]
            >=
            self.fuzzy_threshold
        ):

            return best

        return None

    # =====================================================
    # DETECT
    # =====================================================

    def detect(
        self,
        text,
    ):

        normalized = (
            self.normalize(
                text
            )
        )

        result = {
            "matched":
                False,

            "intent":
                None,

            "category":
                None,

            "confidence":
                0.0,

            "source":
                None,

            "matched_phrase":
                None,

            "normalized_text":
                normalized,
        }

        if not normalized:

            return result

        # =================================================
        # 1. EXACT
        # =================================================

        match = (
            self.exact_match(
                normalized
            )
        )

        if match:

            result.update(
                match
            )

            return result

        # =================================================
        # 2. SAFE TOKEN
        # =================================================

        match = (
            self.token_match(
                normalized
            )
        )

        if match:

            result.update(
                match
            )

            return result

        # =================================================
        # 3. FUZZY
        # =================================================

        match = (
            self.fuzzy_match(
                normalized
            )
        )

        if match:

            result.update(
                match
            )

            return result

        return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    engine = (
        ConversationSignals()
    )

    tests = [

        # =================================================
        # SOCIAL
        # =================================================

        "كيفك",
        "ميمي كيفك اليوم",
        "شو اسمك",
        "مين انتي",
        "شو بتقدري تعملي",
        "شو ممكن نعمل",
        "شكرا ميمي",
        "انتي شطوره",
        "بحبك ميمي",

        # =================================================
        # EMOTIONS
        # =================================================

        "انا مبسوط اليوم",
        "انا زعلان",
        "اليوم انا كتير زعلان",
        "انا خايفه",
        "انا تعبانه",
        "زهقت",
        "انا طفشان",

        # =================================================
        # DIALOGUE
        # =================================================

        "اه",
        "لا",
        "كملي",
        "وبعدين",
        "غيري",
        "بدي غيرها",
        "استني",
        "عيدي",
        "ما فهمت",
        "شو قلتي",

        # =================================================
        # SHOULD NOT RANDOMLY MATCH
        # =================================================

        "بدي قصة",
        "بدي قرآن",
        "شو واجباتي",
        "الوان",
        "الفلق",
    ]

    print()
    print("=" * 72)
    print("🧠 MIMI CONVERSATION SIGNALS TEST")
    print("=" * 72)

    for text in tests:

        result = (
            engine.detect(
                text
            )
        )

        print()
        print(
            f"👧 {text}"
        )

        print(
            f"   normalized : "
            f"{result.get('normalized_text')}"
        )

        print(
            f"   matched    : "
            f"{result.get('matched')}"
        )

        print(
            f"   intent     : "
            f"{result.get('intent')}"
        )

        print(
            f"   category   : "
            f"{result.get('category')}"
        )

        print(
            f"   confidence : "
            f"{result.get('confidence'):.2f}"
        )

        print(
            f"   source     : "
            f"{result.get('source')}"
        )

    print()
    print("=" * 72)
