from difflib import SequenceMatcher

from src.nlu.child_language_normalizer import (
    ChildLanguageNormalizer,
)


# =========================================================
# SURAH DATABASE
# =========================================================

SURAH_NAMES = {
    1: "الفاتحه",
    2: "البقره",
    3: "ال عمران",
    4: "النساء",
    5: "المائده",
    6: "الانعام",
    7: "الاعراف",
    8: "الانفال",
    9: "التوبه",
    10: "يونس",
    11: "هود",
    12: "يوسف",
    13: "الرعد",
    14: "ابراهيم",
    15: "الحجر",
    16: "النحل",
    17: "الاسراء",
    18: "الكهف",
    19: "مريم",
    20: "طه",
    21: "الانبياء",
    22: "الحج",
    23: "المومنون",
    24: "النور",
    25: "الفرقان",
    26: "الشعراء",
    27: "النمل",
    28: "القصص",
    29: "العنكبوت",
    30: "الروم",
    31: "لقمان",
    32: "السجده",
    33: "الاحزاب",
    34: "سبا",
    35: "فاطر",
    36: "يس",
    37: "الصافات",
    38: "ص",
    39: "الزمر",
    40: "غافر",
    41: "فصلت",
    42: "الشوري",
    43: "الزخرف",
    44: "الدخان",
    45: "الجاثيه",
    46: "الاحقاف",
    47: "محمد",
    48: "الفتح",
    49: "الحجرات",
    50: "ق",
    51: "الذاريات",
    52: "الطور",
    53: "النجم",
    54: "القمر",
    55: "الرحمن",
    56: "الواقعه",
    57: "الحديد",
    58: "المجادله",
    59: "الحشر",
    60: "الممتحنه",
    61: "الصف",
    62: "الجمعه",
    63: "المنافقون",
    64: "التغابن",
    65: "الطلاق",
    66: "التحريم",
    67: "الملك",
    68: "القلم",
    69: "الحاقه",
    70: "المعارج",
    71: "نوح",
    72: "الجن",
    73: "المزمل",
    74: "المدثر",
    75: "القيامه",
    76: "الانسان",
    77: "المرسلات",
    78: "النبا",
    79: "النازعات",
    80: "عبس",
    81: "التكوير",
    82: "الانفطار",
    83: "المطففين",
    84: "الانشقاق",
    85: "البروج",
    86: "الطارق",
    87: "الاعلي",
    88: "الغاشيه",
    89: "الفجر",
    90: "البلد",
    91: "الشمس",
    92: "الليل",
    93: "الضحي",
    94: "الشرح",
    95: "التين",
    96: "العلق",
    97: "القدر",
    98: "البينه",
    99: "الزلزله",
    100: "العاديات",
    101: "القارعه",
    102: "التكاثر",
    103: "العصر",
    104: "الهمزه",
    105: "الفيل",
    106: "قريش",
    107: "الماعون",
    108: "الكوثر",
    109: "الكافرون",
    110: "النصر",
    111: "المسد",
    112: "الاخلاص",
    113: "الفلق",
    114: "الناس",
}


# =========================================================
# CURRENT QURAN CONTENT AVAILABLE IN MIMI
# =========================================================

SUPPORTED_SURAHS = {
    113,
    114,
}


# =========================================================
# COMMON SPEECH-TO-TEXT VARIATIONS
# =========================================================
#
# خاصة بالسور الموجودة حاليًا عند Mimi.
#
# Google STT أحيانًا يسمع:
#
# الناس -> الناص
# الفلق -> فلق
#
# =========================================================

SURAH_ALIASES = {
    113: {
        "الفلق",
        "فلق",
    },

    114: {
        "الناس",
        "ناس",
        "الناص",
    },
}


# =========================================================
# FUZZY SETTINGS
# =========================================================

SURAH_FUZZY_THRESHOLD = 0.80


# =========================================================
# SLOT EXTRACTOR
# =========================================================


class SlotExtractor:

    def __init__(self):

        self.normalizer = (
            ChildLanguageNormalizer()
        )

        # =================================================
        # LEARNING TOPICS
        # =================================================

        self.learning_topics = {

            "colors": {
                "لون",
                "اللون",
                "الوان",
                "الالوان",
            },

            "numbers": {
                "رقم",
                "الرقم",
                "ارقام",
                "الارقام",
                "عد",
                "اعداد",
                "الاعداد",
            },

            "letters": {
                "حرف",
                "حروف",
                "ابجديه",
                "ابجديه",
            },

            "addition": {
                "جمع",
                "الجمع",
                "زائد",
                "حساب",
                "الحساب",
                "رياضيات",
                "الرياضيات",
            },
        }

        # =================================================
        # STORY TYPES
        # =================================================

        self.story_types = {

            "animals": {
                "حيوانات",
                "حيوان",
                "ارنب",
                "اسد",
                "قطه",
            },

            "funny": {
                "مضحكه",
                "تضحك",
                "ضحك",
            },

            "educational": {
                "تعليميه",
                "تعليمي",
                "مفيده",
                "مفيد",
            },
        }

    # =====================================================
    # NORMALIZE
    # =====================================================

    def normalize(
        self,
        text,
    ):

        return (
            self.normalizer
            .basic_normalize(
                str(text)
            )
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
    # EXACT PHRASE MATCH
    # =====================================================
    #
    # IMPORTANT:
    #
    # بدل:
    #
    #     if name in text
    #
    # نعمل مقارنة tokens كاملة.
    #
    # مثال:
    #
    # text:
    #   بدي قصة
    #
    # tokens:
    #   ["بدي", "قصه"]
    #
    # سورة ق:
    #   ["ق"]
    #
    # لا يوجد token اسمه "ق"
    # إذًا لا يوجد تطابق.
    #
    # =====================================================

    def contains_phrase(
        self,
        text_tokens,
        phrase_tokens,
    ):

        if not phrase_tokens:

            return False

        phrase_length = len(
            phrase_tokens
        )

        if (
            phrase_length
            >
            len(text_tokens)
        ):

            return False

        for index in range(
            len(text_tokens)
            -
            phrase_length
            +
            1
        ):

            candidate = (
                text_tokens[
                    index:
                    index
                    +
                    phrase_length
                ]
            )

            if candidate == phrase_tokens:

                return True

        return False

    # =====================================================
    # EXTRACT QURAN MODE
    # =====================================================

    def extract_quran_mode(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        tokens = set(
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
            "اقري",
            "اقرا",
            "نقرا",
            "اسمع",
            "شغلي",
            "قراءه",
        }

        if (
            tokens
            &
            memorize_words
        ):

            return "memorize"

        if (
            tokens
            &
            read_words
        ):

            return "read"

        return None

    # =====================================================
    # HAS QURAN CONTEXT
    # =====================================================

    def has_quran_context(
        self,
        text,
    ):

        tokens = set(
            text.split()
        )

        quran_words = {
            "قران",
            "القران",
            "سوره",
            "سور",
            "ايه",
            "ايات",
            "اقري",
            "اقرا",
            "نقرا",
            "احفظ",
            "نحفظ",
            "حفظ",
            "تسميع",
            "سمعلي",
        }

        return bool(
            tokens
            &
            quran_words
        )

    # =====================================================
    # EXACT SURAH MATCH
    # =====================================================

    def find_exact_surah(
        self,
        text,
    ):

        text_tokens = (
            text.split()
        )

        candidates = []

        # -------------------------------------------------
        # Main names
        # -------------------------------------------------

        for number, name in (
            SURAH_NAMES.items()
        ):

            normalized_name = (
                self.normalize(
                    name
                )
            )

            candidates.append(
                (
                    number,
                    normalized_name,
                    "exact",
                )
            )

        # -------------------------------------------------
        # Aliases
        # -------------------------------------------------

        for number, aliases in (
            SURAH_ALIASES.items()
        ):

            for alias in aliases:

                normalized_alias = (
                    self.normalize(
                        alias
                    )
                )

                candidates.append(
                    (
                        number,
                        normalized_alias,
                        "alias",
                    )
                )

        # -------------------------------------------------
        # Longer names first
        # -------------------------------------------------
        #
        # مثال:
        # "ال عمران" قبل أسماء أقصر.
        # -------------------------------------------------

        candidates.sort(
            key=lambda item: (
                len(
                    item[1].split()
                ),
                len(
                    item[1]
                ),
            ),
            reverse=True,
        )

        for (
            number,
            candidate_name,
            match_type,
        ) in candidates:

            phrase_tokens = (
                candidate_name.split()
            )

            if self.contains_phrase(
                text_tokens,
                phrase_tokens,
            ):

                return {
                    "number":
                        number,

                    "name":
                        SURAH_NAMES[
                            number
                        ],

                    "confidence":
                        1.0,

                    "match_type":
                        match_type,

                    "supported":
                        number
                        in
                        SUPPORTED_SURAHS,
                }

        return None

    # =====================================================
    # FUZZY SURAH MATCH
    # =====================================================

    def find_fuzzy_surah(
        self,
        text,
    ):

        ignored = {
            "سوره",
            "سور",
            "قران",
            "القران",
            "اقري",
            "اقرا",
            "نقرا",
            "اسمع",
            "احفظ",
            "نحفظ",
            "حفظ",
            "شغلي",
            "بدي",
            "ممكن",
            "لو",
            "سمحتي",
            "ميمي",
        }

        words = [
            word
            for word in text.split()
            if (
                word
                and
                word
                not in ignored
            )
        ]

        if not words:

            return None

        # =================================================
        # SAFETY AGAINST RANDOM SURAH MATCHES
        # =================================================
        #
        # Fuzzy matching is only allowed when:
        #
        # 1. The sentence clearly looks Quran-related
        #
        # OR
        #
        # 2. The child said only one word.
        #
        # The second case is important for follow-up:
        #
        # Mimi: أي سورة؟
        # Child: الناص
        #
        # =================================================

        quran_context = (
            self.has_quran_context(
                text
            )
        )

        if (
            not quran_context
            and
            len(words) != 1
        ):

            return None

        best = None

        # =================================================
        # BUILD CANDIDATES
        # =================================================

        candidates = []

        for number, name in (
            SURAH_NAMES.items()
        ):

            normalized_name = (
                self.normalize(
                    name
                )
            )

            # ---------------------------------------------
            # VERY SHORT NAMES
            # ---------------------------------------------
            #
            # ق
            # ص
            # يس
            # طه
            #
            # Exact match only.
            # Fuzzy on these is too dangerous.
            # ---------------------------------------------

            compact_name = (
                normalized_name
                .replace(
                    " ",
                    "",
                )
            )

            if len(compact_name) <= 2:

                continue

            candidates.append(
                (
                    number,
                    normalized_name,
                )
            )

        # =================================================
        # COMPARE WINDOWS
        # =================================================

        for (
            number,
            surah_name,
        ) in candidates:

            surah_tokens = (
                surah_name.split()
            )

            token_count = len(
                surah_tokens
            )

            # ---------------------------------------------
            # One-word Surah
            # ---------------------------------------------

            if token_count == 1:

                for word in words:

                    # Avoid silly comparisons
                    if len(word) < 3:

                        continue

                    score = (
                        self.similarity(
                            word,
                            surah_name,
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
                            "number":
                                number,

                            "name":
                                SURAH_NAMES[
                                    number
                                ],

                            "confidence":
                                score,

                            "match_type":
                                "fuzzy",

                            "supported":
                                number
                                in
                                SUPPORTED_SURAHS,
                        }

            # ---------------------------------------------
            # Multi-word Surah
            # ---------------------------------------------

            else:

                if (
                    len(words)
                    <
                    token_count
                ):

                    continue

                for index in range(
                    len(words)
                    -
                    token_count
                    +
                    1
                ):

                    candidate_phrase = (
                        " ".join(
                            words[
                                index:
                                index
                                +
                                token_count
                            ]
                        )
                    )

                    score = (
                        self.similarity(
                            candidate_phrase,
                            surah_name,
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
                            "number":
                                number,

                            "name":
                                SURAH_NAMES[
                                    number
                                ],

                            "confidence":
                                score,

                            "match_type":
                                "fuzzy",

                            "supported":
                                number
                                in
                                SUPPORTED_SURAHS,
                        }

        if (
            best is not None
            and
            best[
                "confidence"
            ]
            >=
            SURAH_FUZZY_THRESHOLD
        ):

            return best

        return None

    # =====================================================
    # EXTRACT SURAH
    # =====================================================

    def extract_surah(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        # -------------------------------------------------
        # Exact full-token matching first
        # -------------------------------------------------

        exact = (
            self.find_exact_surah(
                text
            )
        )

        if exact is not None:

            return exact

        # -------------------------------------------------
        # Controlled fuzzy matching
        # -------------------------------------------------

        return (
            self.find_fuzzy_surah(
                text
            )
        )

    # =====================================================
    # EXTRACT LEARNING TOPIC
    # =====================================================

    def extract_learning_topic(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        tokens = set(
            text.split()
        )

        for (
            topic,
            keywords,
        ) in (
            self.learning_topics.items()
        ):

            if (
                tokens
                &
                keywords
            ):

                return topic

        return None

    # =====================================================
    # EXTRACT STORY TYPE
    # =====================================================

    def extract_story_type(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        tokens = set(
            text.split()
        )

        for (
            story_type,
            keywords,
        ) in (
            self.story_types.items()
        ):

            if (
                tokens
                &
                keywords
            ):

                return story_type

        return None

    # =====================================================
    # EXTRACT TASK ACTION
    # =====================================================

    def extract_task_action(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        tokens = set(
            text.split()
        )

        complete_words = {
            "خلصت",
            "خلص",
            "انجزت",
            "انهيت",
            "تم",
        }

        view_words = {
            "مهامي",
            "مهماتي",
            "واجباتي",
            "واجب",
            "مهام",
        }

        if (
            tokens
            &
            complete_words
        ):

            return "complete"

        if (
            tokens
            &
            view_words
        ):

            return "view"

        return None

    # =====================================================
    # EXTRACT UNIVERSAL COMMAND
    # =====================================================

    def extract_universal_command(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        tokens = set(
            text.split()
        )

        stop_words = {
            "وقف",
            "توقف",
            "وقفي",
            "خلص",
        }

        repeat_words = {
            "عيدي",
            "كرر",
            "كرري",
            "كمان",
        }

        back_words = {
            "ارجع",
            "ارجعي",
            "رجع",
        }

        if (
            tokens
            &
            stop_words
        ):

            return "stop"

        if (
            tokens
            &
            repeat_words
        ):

            return "repeat"

        if (
            tokens
            &
            back_words
        ):

            return "back"

        return None

    # =====================================================
    # EXTRACT ALL SLOTS
    # =====================================================

    def extract(
        self,
        text,
    ):

        normalized = self.normalize(
            text
        )

        quran_mode = (
            self.extract_quran_mode(
                normalized
            )
        )

        surah = (
            self.extract_surah(
                normalized
            )
        )

        learning_topic = (
            self.extract_learning_topic(
                normalized
            )
        )

        story_type = (
            self.extract_story_type(
                normalized
            )
        )

        task_action = (
            self.extract_task_action(
                normalized
            )
        )

        universal_command = (
            self.extract_universal_command(
                normalized
            )
        )

        result = {
            "quran_mode":
                quran_mode,

            "surah_number":
                None,

            "surah_name":
                None,

            "surah_confidence":
                None,

            "surah_match_type":
                None,

            "surah_supported":
                None,

            "learning_topic":
                learning_topic,

            "story_type":
                story_type,

            "task_action":
                task_action,

            "universal_command":
                universal_command,
        }

        if surah is not None:

            result[
                "surah_number"
            ] = surah.get(
                "number"
            )

            result[
                "surah_name"
            ] = surah.get(
                "name"
            )

            result[
                "surah_confidence"
            ] = surah.get(
                "confidence"
            )

            result[
                "surah_match_type"
            ] = surah.get(
                "match_type"
            )

            result[
                "surah_supported"
            ] = surah.get(
                "supported"
            )

        return result


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    extractor = (
        SlotExtractor()
    )

    tests = [
        # ---------------------------------------------
        # These MUST NOT become Quran
        # ---------------------------------------------
        "بدي قصة",
        "احكيلي قصة",
        "بدي لغز",
        "شو واجباتي",
        "بدي اتعلم الالوان",
        "مرحبا ميمي",
        "كيفك اليوم",
        "احكيلي قصة عن قطة",

        # ---------------------------------------------
        # Quran
        # ---------------------------------------------
        "بدي قران",
        "اقري سورة الفلق",
        "بدي احفظ سورة الناس",
        "شغلي الناص",
        "الفلق",
        "الناس",

        # ---------------------------------------------
        # Single-letter Surahs
        # ---------------------------------------------
        "ق",
        "ص",
        "بدي سورة ق",
    ]

    print()
    print("=" * 70)
    print("🧠 MIMI SLOT EXTRACTOR TEST")
    print("=" * 70)

    for text in tests:

        result = (
            extractor.extract(
                text
            )
        )

        print()
        print(
            f"TEXT: {text}"
        )

        print(
            f"Quran mode: "
            f"{result.get('quran_mode')}"
        )

        print(
            f"Surah: "
            f"{result.get('surah_name')}"
        )

        print(
            f"Surah number: "
            f"{result.get('surah_number')}"
        )

        print(
            f"Match: "
            f"{result.get('surah_match_type')}"
        )

        print(
            f"Supported: "
            f"{result.get('surah_supported')}"
        )

        print(
            f"Learning: "
            f"{result.get('learning_topic')}"
        )

        print(
            f"Story type: "
            f"{result.get('story_type')}"
        )

        print(
            f"Task action: "
            f"{result.get('task_action')}"
        )

        print(
            f"Universal: "
            f"{result.get('universal_command')}"
        )

    print()
    print("=" * 70)