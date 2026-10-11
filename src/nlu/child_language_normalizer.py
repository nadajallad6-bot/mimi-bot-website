import re
import unicodedata


# =========================================================
# CHILD LANGUAGE NORMALIZER
# =========================================================
#
# This module prepares CHILD COMMANDS for Mimi's NLU.
#
# Examples:
#
#   "مييييمي بدييي قصة"
#       -> "قصة"
#
#   "ممكن لو سمحتي تقرأيلي سورة الفلق"
#       -> "اقري سورة الفلق"
#
#   "بدنا نحفظ سوره الناس"
#       -> "نحفظ سوره الناس"
#
# IMPORTANT:
# This is NOT used for Quran recitation evaluation.
# =========================================================


class ChildLanguageNormalizer:

    def __init__(self):

        # =================================================
        # WAKE WORD VARIATIONS
        # =================================================

        self.wake_words = {
            "ميمي",
            "ميمى",
            "ميمي بوت",
            "ميمي بوتي",
            "مِيمي",
            "ميميي",
            "مييمي",
        }

        # =================================================
        # FILLER PHRASES
        # =================================================
        #
        # Child may use these without changing the intent.
        # =================================================

        self.filler_phrases = [
            "لو سمحتي",
            "لو سمحت",
            "من فضلك",
            "ممكن",
            "طيب",
            "طب",
            "يعني",
            "هسا",
            "هلأ",
            "هلا",
            "بليز",
            "please",
        ]

        # =================================================
        # CHILD / DIALECT WORD NORMALIZATION
        # =================================================
        #
        # Left = possible child/STT form
        # Right = canonical Mimi form
        # =================================================

        self.word_aliases = {

            # -------------------------------------------------
            # Quran
            # -------------------------------------------------

            "قران":
                "قران",

            "قرآن":
                "قران",

            "القران":
                "قران",

            "القرآن":
                "قران",

            "سورة":
                "سوره",

            "سوره":
                "سوره",

            "سورا":
                "سوره",

            "سورت":
                "سوره",

            # -------------------------------------------------
            # Read
            # -------------------------------------------------

            "اقرالي":
                "اقري",

            "اقرأيلي":
                "اقري",

            "اقرئيلي":
                "اقري",

            "اقرألي":
                "اقري",

            "اقريلي":
                "اقري",

            "اقرأي":
                "اقري",

            "اقرئي":
                "اقري",

            "شغليلي":
                "شغلي",

            "شغللي":
                "شغلي",

            "سمعيني":
                "اسمع",

            "اسمعيني":
                "اسمع",

            # -------------------------------------------------
            # Memorize
            # -------------------------------------------------

            "احفظ":
                "احفظ",

            "احفظني":
                "احفظ",

            "حفظيني":
                "احفظ",

            "حفّظيني":
                "احفظ",

            "نحفظ":
                "احفظ",

            "حفظ":
                "احفظ",

            # -------------------------------------------------
            # Story
            # -------------------------------------------------

            "حكايه":
                "قصه",

            "حكاية":
                "قصه",

            "حكايهً":
                "قصه",

            "قصة":
                "قصه",

            "قصه":
                "قصه",

            "احكيلي":
                "احكي",

            "احكيليلي":
                "احكي",

            # -------------------------------------------------
            # Riddle
            # -------------------------------------------------

            "لغز":
                "لغز",

            "لغزلي":
                "لغز",

            "فزوره":
                "لغز",

            "فزورة":
                "لغز",

            "حزوره":
                "لغز",

            "حزورة":
                "لغز",

            # -------------------------------------------------
            # Learning
            # -------------------------------------------------

            "علّميني":
                "علميني",

            "علميني":
                "علميني",

            "تعلميني":
                "علميني",

            "نتعلم":
                "تعلم",

            "اتعلم":
                "تعلم",

            "ندرس":
                "تعلم",

            "ادرس":
                "تعلم",

            # -------------------------------------------------
            # Colors
            # -------------------------------------------------

            "الوان":
                "الوان",

            "ألوان":
                "الوان",

            "الالوان":
                "الوان",

            "الألوان":
                "الوان",

            # -------------------------------------------------
            # Numbers
            # -------------------------------------------------

            "ارقام":
                "ارقام",

            "أرقام":
                "ارقام",

            "الارقام":
                "ارقام",

            "الأرقام":
                "ارقام",

            # -------------------------------------------------
            # Letters
            # -------------------------------------------------

            "حروف":
                "حروف",

            "الحروف":
                "حروف",

            # -------------------------------------------------
            # Addition
            # -------------------------------------------------

            "جمع":
                "جمع",

            "الجمع":
                "جمع",

            "زائد":
                "جمع",

            # -------------------------------------------------
            # Tasks
            # -------------------------------------------------

            "وظايفي":
                "مهامي",

            "وظائفي":
                "مهامي",

            "واجباتي":
                "مهامي",

            "واجباتي":
                "مهامي",

            "المهام":
                "مهام",

            # -------------------------------------------------
            # Adhkar
            # -------------------------------------------------

            "اذكار":
                "اذكار",

            "أذكار":
                "اذكار",

            "الاذكار":
                "اذكار",

            "الأذكار":
                "اذكار",

            "الصبح":
                "الصباح",

            "الصباحي":
                "الصباح",

            "المسا":
                "المساء",

            "المساي":
                "المساء",

            # -------------------------------------------------
            # Basic conversational
            # -------------------------------------------------

            "بدي":
                "بدي",

            "بديش":
                "لا",

            "بدنا":
                "بدي",

            "نفسي":
                "بدي",

            "حاب":
                "بدي",

            "حابه":
                "بدي",

            "حابة":
                "بدي",

            "اريد":
                "بدي",

            "أريد":
                "بدي",

            # -------------------------------------------------
            # Repeat / stop
            # -------------------------------------------------

            "عيديها":
                "عيدي",

            "اعيدي":
                "عيدي",

            "أعيدي":
                "عيدي",

            "مرةكمان":
                "عيدي",

            "مرهكمان":
                "عيدي",

            "خلص":
                "وقف",

            "وقفي":
                "وقف",

            "بس":
                "وقف",
        }

        # =================================================
        # COMMON PHRASE REWRITES
        # =================================================
        #
        # Longer phrases are handled before individual words.
        # =================================================

        self.phrase_aliases = {

            "بدي اسمع قران":
                "اسمع قران",

            "بدي اسمع القران":
                "اسمع قران",

            "بدي اسمع سوره":
                "اسمع سوره",

            "شغلي سوره":
                "اسمع سوره",

            "شغليلي سوره":
                "اسمع سوره",

            "اقريلي سوره":
                "اقري سوره",

            "اقرالي سوره":
                "اقري سوره",

            "بدي اقرا سوره":
                "اقري سوره",

            "بدي احفظ سوره":
                "احفظ سوره",

            "خلينا نحفظ سوره":
                "احفظ سوره",

            "بدنا نحفظ سوره":
                "احفظ سوره",

            "علميني سوره":
                "احفظ سوره",

            "بدي قصه":
                "قصه",

            "احكيلي قصه":
                "قصه",

            "احكي قصه":
                "قصه",

            "بدي حكايه":
                "قصه",

            "احكيلي حكايه":
                "قصه",

            "بدي لغز":
                "لغز",

            "اعطيني لغز":
                "لغز",

            "قوليلي لغز":
                "لغز",

            "بدي فزوره":
                "لغز",

            "بدي اتعلم":
                "تعلم",

            "بدي نتعلم":
                "تعلم",

            "خلينا نتعلم":
                "تعلم",

            "علميني الوان":
                "تعلم الوان",

            "علميني ارقام":
                "تعلم ارقام",

            "علميني حروف":
                "تعلم حروف",

            "علميني جمع":
                "تعلم جمع",

            "شو مهامي":
                "مهام",

            "شو واجباتي":
                "مهام",

            "شو علي مهام":
                "مهام",

            "عندي مهام":
                "مهام",

            "اذكار الصبح":
                "اذكار الصباح",

            "اذكار المسا":
                "اذكار المساء",
        }

    # =====================================================
    # REMOVE DIACRITICS
    # =====================================================

    def remove_diacritics(
        self,
        text,
    ):

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        return "".join(
            char
            for char in text
            if not unicodedata.combining(
                char
            )
        )

    # =====================================================
    # NORMALIZE ARABIC LETTERS
    # =====================================================

    def normalize_letters(
        self,
        text,
    ):

        replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ى": "ي",
            "ؤ": "و",
            "ئ": "ي",
            "ة": "ه",
            "ـ": "",
        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new,
            )

        return text

    # =====================================================
    # NORMALIZE ARABIC DIGITS
    # =====================================================

    def normalize_digits(
        self,
        text,
    ):

        arabic_digits = (
            "٠١٢٣٤٥٦٧٨٩"
        )

        western_digits = (
            "0123456789"
        )

        table = str.maketrans(
            arabic_digits,
            western_digits,
        )

        return text.translate(
            table
        )

    # =====================================================
    # REMOVE PUNCTUATION
    # =====================================================

    def remove_punctuation(
        self,
        text,
    ):

        text = re.sub(
            r"[^\u0600-\u06FFa-zA-Z0-9\s]",
            " ",
            text,
        )

        return text

    # =====================================================
    # COLLAPSE CHILD LETTER REPETITION
    # =====================================================
    #
    # "مييييييمي"
    # "بدييييي"
    # "قصصصصصة"
    #
    # Become less exaggerated.
    # =====================================================

    def collapse_repeated_letters(
        self,
        text,
    ):

        return re.sub(
            r"(.)\1{2,}",
            r"\1\1",
            text,
        )

    # =====================================================
    # REMOVE WAKE WORD
    # =====================================================

    def remove_wake_word(
        self,
        text,
    ):

        text = text.strip()

        # Specific variations after normalization
        possible = [
            "ميمي بوت",
            "ميمي",
            "ميمى",
            "مييمي",
            "ميميي",
        ]

        for wake_word in possible:

            normalized_wake = (
                self.normalize_letters(
                    wake_word
                )
            )

            if text == normalized_wake:

                return ""

            if text.startswith(
                normalized_wake + " "
            ):

                return text[
                    len(normalized_wake):
                ].strip()

        return text

    # =====================================================
    # REMOVE FILLER PHRASES
    # =====================================================

    def remove_fillers(
        self,
        text,
    ):

        for phrase in sorted(
            self.filler_phrases,
            key=len,
            reverse=True,
        ):

            phrase = (
                self.normalize_letters(
                    self.remove_diacritics(
                        phrase.lower()
                    )
                )
            )

            text = re.sub(
                rf"\b{re.escape(phrase)}\b",
                " ",
                text,
            )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =====================================================
    # APPLY WORD ALIASES
    # =====================================================

    def apply_word_aliases(
        self,
        text,
    ):

        words = text.split()

        output = []

        for word in words:

            replacement = (
                self.word_aliases.get(
                    word,
                    word,
                )
            )

            output.append(
                replacement
            )

        return " ".join(
            output
        )

    # =====================================================
    # APPLY PHRASE ALIASES
    # =====================================================

    def apply_phrase_aliases(
        self,
        text,
    ):

        aliases = sorted(
            self.phrase_aliases.items(),
            key=lambda item:
                len(item[0]),
            reverse=True,
        )

        for source, target in aliases:

            source = self.basic_normalize(
                source
            )

            target = self.basic_normalize(
                target
            )

            if source in text:

                text = text.replace(
                    source,
                    target,
                )

        return text

    # =====================================================
    # BASIC NORMALIZATION
    # =====================================================

    def basic_normalize(
        self,
        text,
    ):

        if text is None:

            return ""

        text = str(
            text
        ).strip().lower()

        text = self.remove_diacritics(
            text
        )

        text = self.normalize_letters(
            text
        )

        text = self.normalize_digits(
            text
        )

        text = self.remove_punctuation(
            text
        )

        text = self.collapse_repeated_letters(
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =====================================================
    # NORMALIZE COMMAND
    # =====================================================

    def normalize(
        self,
        text,
    ):

        original = (
            ""
            if text is None
            else str(text)
        )

        # -------------------------------------------------
        # Stage 1
        # -------------------------------------------------

        normalized = (
            self.basic_normalize(
                original
            )
        )

        # -------------------------------------------------
        # Stage 2 - Wake Word
        # -------------------------------------------------

        normalized = (
            self.remove_wake_word(
                normalized
            )
        )

        # -------------------------------------------------
        # Stage 3 - Fillers
        # -------------------------------------------------

        no_fillers = (
            self.remove_fillers(
                normalized
            )
        )

        # -------------------------------------------------
        # Stage 4 - Child vocabulary
        # -------------------------------------------------

        canonical = (
            self.apply_word_aliases(
                no_fillers
            )
        )

        canonical = (
            self.apply_phrase_aliases(
                canonical
            )
        )

        canonical = re.sub(
            r"\s+",
            " ",
            canonical,
        ).strip()

        return {
            "original":
                original,

            "normalized":
                normalized,

            "no_fillers":
                no_fillers,

            "canonical":
                canonical,

            "tokens":
                canonical.split(),

            "empty":
                len(canonical) == 0,
        }

    # =====================================================
    # GET POSSIBLE VARIANTS
    # =====================================================

    def get_variants(
        self,
        text,
    ):

        result = (
            self.normalize(
                text
            )
        )

        variants = []

        for candidate in (
            result["normalized"],
            result["no_fillers"],
            result["canonical"],
        ):

            candidate = candidate.strip()

            if (
                candidate
                and
                candidate not in variants
            ):

                variants.append(
                    candidate
                )

        return variants


# =========================================================
# TEST
# =========================================================

def test_normalizer():

    normalizer = (
        ChildLanguageNormalizer()
    )

    examples = [
        "مييييمي بدييي قصصصصة",
        "ميمي ممكن لو سمحتي تقرأيلي سورة الفلق",
        "بدنا نحفظ سوره الناس",
        "ميمي شغليلي سورة الفلق",
        "ممكن تعطيني فزورة",
        "ميمي علميني الألوان",
        "شو واجباتي اليوم",
        "ميمي أذكار الصبح",
        "هسا بدي نتعلم الجمع",
        "ميمي",
    ]

    print()
    print("=" * 70)
    print("🧠 CHILD LANGUAGE NORMALIZER TEST")
    print("=" * 70)

    for text in examples:

        result = (
            normalizer.normalize(
                text
            )
        )

        print()
        print(
            f"Original : {text}"
        )

        print(
            f"Normal   : "
            f"{result['normalized']}"
        )

        print(
            f"Canonical: "
            f"{result['canonical']}"
        )

        print("-" * 70)


if __name__ == "__main__":

    test_normalizer()
