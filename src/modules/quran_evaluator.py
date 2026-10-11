import json
import re
import unicodedata
from pathlib import Path


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

QURAN_TEXT_FILE = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "quran_text.json"
)


# =========================================================
# Arabic Normalization
# =========================================================

def normalize_arabic(text):
    """
    تطبيع النص حتى نقارن كلام الطفل
    مع نص الآية بدون ما تؤثر:

    - الحركات
    - أشكال الألف
    - علامات الترقيم
    - المد
    """

    if text is None:
        return ""

    text = str(text).strip().lower()

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    # Remove combining marks / tashkeel
    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    # Quranic marks
    text = re.sub(
        r"[\u0610-\u061A"
        r"\u064B-\u065F"
        r"\u0670"
        r"\u06D6-\u06ED]",
        "",
        text,
    )

    # Tatweel
    text = text.replace(
        "ـ",
        "",
    )

    # Normalize Alef
    for char in (
        "أ",
        "إ",
        "آ",
        "ٱ",
    ):
        text = text.replace(
            char,
            "ا",
        )

    # Normalize Ya
    text = text.replace(
        "ى",
        "ي",
    )

    # Common STT normalization
    text = text.replace(
        "ؤ",
        "و",
    )

    text = text.replace(
        "ئ",
        "ي",
    )

    # Remove punctuation
    text = re.sub(
        r"[^\u0600-\u06FFa-zA-Z0-9\s]",
        " ",
        text,
    )

    # Extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# Character Distance
# =========================================================

def char_distance(
    first,
    second,
):
    """
    Levenshtein distance between two normalized Arabic words.
    Used only to make child/STT evaluation tolerant to a very
    small one-character difference.
    """

    first = str(first or "")
    second = str(second or "")

    n = len(first)
    m = len(second)

    if n == 0:
        return m

    if m == 0:
        return n

    previous = list(
        range(m + 1)
    )

    for i in range(
        1,
        n + 1,
    ):

        current = [i] + [0] * m

        for j in range(
            1,
            m + 1,
        ):

            cost = (
                0
                if first[i - 1] == second[j - 1]
                else 1
            )

            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + cost,
            )

        previous = current

    return previous[m]


# =========================================================
# Word Substitution Cost
# =========================================================

NEAR_WORD_PENALTY = 0.25


def word_substitution_cost(
    expected_word,
    heard_word,
):
    """
    Exact word:
        cost 0.0

    Very small child/STT difference:
        cost 0.25

    Clearly different word:
        cost 1.0

    This does NOT change the Quran text. It only makes the
    speech-recognition comparison less frustrating for a
    child when one letter is misheard.
    """

    if expected_word == heard_word:
        return 0.0

    if not expected_word or not heard_word:
        return 1.0

    distance = char_distance(
        expected_word,
        heard_word,
    )

    # One-character difference is accepted as a near match
    # only for words long enough to avoid over-tolerance on
    # very short Quran words.
    minimum_length = min(
        len(expected_word),
        len(heard_word),
    )

    if (
        minimum_length >= 3
        and distance == 1
    ):
        return NEAR_WORD_PENALTY

    return 1.0


# =========================================================
# Optional Basmala Handling
# =========================================================

NORMALIZED_BASMALA_WORDS = [
    "بسم",
    "الله",
    "الرحمن",
    "الرحيم",
]


def remove_leading_basmala_words(
    words,
):
    """
    Returns (clean_words, removed).

    On the first ayah of most surahs the reciter/audio or STT
    may include the basmala while the verse text file may not,
    or vice versa.

    We ignore ONLY an exact leading normalized basmala during
    evaluation. The original Quran text in quran_text.json is
    never changed.
    """

    words = list(
        words
        or []
    )

    count = len(
        NORMALIZED_BASMALA_WORDS
    )

    if (
        len(words) >= count
        and
        words[:count]
        ==
        NORMALIZED_BASMALA_WORDS
    ):

        return (
            words[count:],
            True,
        )

    return (
        words,
        False,
    )


# =========================================================
# Word Edit Distance + Errors
# =========================================================

def compare_words(
    expected_words,
    child_words,
):
    """
    Tolerant word-level Levenshtein distance.

    Returns:
    - distance (float)
    - missing words
    - extra words
    - substitutions
    - near_matches
    """

    n = len(
        expected_words
    )

    m = len(
        child_words
    )

    dp = [
        [0.0] * (m + 1)
        for _ in range(n + 1)
    ]

    operation = [
        [None] * (m + 1)
        for _ in range(n + 1)
    ]

    for i in range(
        1,
        n + 1,
    ):

        dp[i][0] = float(i)
        operation[i][0] = "missing"

    for j in range(
        1,
        m + 1,
    ):

        dp[0][j] = float(j)
        operation[0][j] = "extra"

    for i in range(
        1,
        n + 1,
    ):

        for j in range(
            1,
            m + 1,
        ):

            expected_word = (
                expected_words[i - 1]
            )

            heard_word = (
                child_words[j - 1]
            )

            substitution_cost = (
                word_substitution_cost(
                    expected_word,
                    heard_word,
                )
            )

            candidates = [
                (
                    dp[i - 1][j] + 1.0,
                    "missing",
                ),
                (
                    dp[i][j - 1] + 1.0,
                    "extra",
                ),
                (
                    dp[i - 1][j - 1]
                    + substitution_cost,
                    (
                        "match"
                        if substitution_cost == 0.0
                        else
                        (
                            "near"
                            if substitution_cost
                            == NEAR_WORD_PENALTY
                            else
                            "substitution"
                        )
                    ),
                ),
            ]

            best_cost, best_op = min(
                candidates,
                key=lambda item: item[0],
            )

            dp[i][j] = best_cost
            operation[i][j] = best_op

    missing = []
    extra = []
    substitutions = []
    near_matches = []

    i = n
    j = m

    while (
        i > 0
        or j > 0
    ):

        op = operation[i][j]

        if (
            i > 0
            and
            j > 0
            and
            op == "match"
        ):

            i -= 1
            j -= 1
            continue

        if (
            i > 0
            and
            j > 0
            and
            op == "near"
        ):

            near_matches.append(
                {
                    "expected":
                        expected_words[i - 1],

                    "heard":
                        child_words[j - 1],
                }
            )

            i -= 1
            j -= 1
            continue

        if (
            i > 0
            and
            j > 0
            and
            op == "substitution"
        ):

            substitutions.append(
                {
                    "expected":
                        expected_words[i - 1],

                    "heard":
                        child_words[j - 1],
                }
            )

            i -= 1
            j -= 1
            continue

        if (
            i > 0
            and
            op == "missing"
        ):

            missing.append(
                expected_words[i - 1]
            )

            i -= 1
            continue

        if (
            j > 0
            and
            op == "extra"
        ):

            extra.append(
                child_words[j - 1]
            )

            j -= 1
            continue

        # Safety fallback
        if i > 0 and j > 0:
            substitutions.append(
                {
                    "expected":
                        expected_words[i - 1],
                    "heard":
                        child_words[j - 1],
                }
            )
            i -= 1
            j -= 1
        elif i > 0:
            missing.append(
                expected_words[i - 1]
            )
            i -= 1
        elif j > 0:
            extra.append(
                child_words[j - 1]
            )
            j -= 1

    missing.reverse()
    extra.reverse()
    substitutions.reverse()
    near_matches.reverse()

    return {
        "distance":
            float(dp[n][m]),

        "missing":
            missing,

        "extra":
            extra,

        "substitutions":
            substitutions,

        "near_matches":
            near_matches,
    }


# =========================================================
# Quran Evaluator
# =========================================================

class QuranEvaluator:

    def __init__(
        self,
        pass_threshold=85.0,
    ):

        self.pass_threshold = float(
            pass_threshold
        )

        self.quran_data = {}

        self.started = False

    # =====================================================
    # Start
    # =====================================================

    def start(self):

        if self.started:
            return

        print()
        print("=" * 60)
        print("📖 STARTING QURAN EVALUATOR")
        print("=" * 60)

        if not QURAN_TEXT_FILE.exists():

            raise FileNotFoundError(
                f"Quran text file not found: "
                f"{QURAN_TEXT_FILE}"
            )

        with open(
            QURAN_TEXT_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            self.quran_data = (
                json.load(file)
            )

        if not isinstance(
            self.quran_data,
            dict,
        ):

            raise ValueError(
                "quran_text.json must contain "
                "a dictionary of surahs."
            )

        total_surahs = len(
            self.quran_data
        )

        total_ayahs = 0

        for surah in (
            self.quran_data.values()
        ):

            if not isinstance(
                surah,
                dict,
            ):

                continue

            # Supports old structure:
            # {"113": {"ayahs": {"1": "..."}}}
            if (
                "ayahs" in surah
                and
                isinstance(
                    surah.get("ayahs"),
                    dict,
                )
            ):

                total_ayahs += len(
                    surah["ayahs"]
                )

            # Supports new full-Quran structure:
            # {"113": {"1": "...", "2": "..."}}
            else:

                total_ayahs += len(
                    surah
                )

        self.started = True

        print(
            f"📚 Surahs loaded: "
            f"{total_surahs}"
        )

        print(
            f"📖 Ayahs loaded: "
            f"{total_ayahs}"
        )

        print(
            f"🎯 Pass threshold: "
            f"{self.pass_threshold:.0f}%"
        )

        print(
            "✅ Quran Evaluator ready."
        )

        print("=" * 60)

    # =====================================================
    # Get Ayah
    # =====================================================

    def get_ayah_text(
        self,
        surah_number,
        ayah_number,
    ):

        if not self.started:

            self.start()

        try:

            surah_key = str(
                int(surah_number)
            )

            ayah_key = str(
                int(ayah_number)
            )

        except Exception:

            return None

        surah = (
            self.quran_data.get(
                surah_key
            )
        )

        if not isinstance(
            surah,
            dict,
        ):

            return None

        # -------------------------------------------------
        # OLD FORMAT
        # -------------------------------------------------
        #
        # {
        #   "113": {
        #       "ayahs": {
        #           "1": "...",
        #           ...
        #       }
        #   }
        # }
        #
        # -------------------------------------------------

        if (
            "ayahs" in surah
            and
            isinstance(
                surah.get("ayahs"),
                dict,
            )
        ):

            return (
                surah["ayahs"].get(
                    ayah_key
                )
            )

        # -------------------------------------------------
        # NEW FULL-QURAN FORMAT
        # -------------------------------------------------
        #
        # {
        #   "113": {
        #       "1": "...",
        #       "2": "...",
        #       ...
        #   }
        # }
        #
        # -------------------------------------------------

        return (
            surah.get(
                ayah_key
            )
        )

    # =====================================================
    # Evaluate
    # =====================================================

    def evaluate(
        self,
        surah_number,
        ayah_number,
        child_text,
    ):

        if not self.started:

            self.start()

        expected_text = (
            self.get_ayah_text(
                surah_number,
                ayah_number,
            )
        )

        if expected_text is None:

            return {
                "handled": False,
                "error":
                    "ayah_not_found",
            }

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------

        expected_normalized = (
            normalize_arabic(
                expected_text
            )
        )

        child_normalized = (
            normalize_arabic(
                child_text
            )
        )

        expected_words = (
            expected_normalized.split()
        )

        child_words = (
            child_normalized.split()
        )

        # -------------------------------------------------
        # Optional leading Basmala on first ayah
        # -------------------------------------------------
        #
        # Fatiha keeps its own first ayah as normal.
        # Surah 9 (At-Tawbah) does not begin with Basmala.
        #
        # For other surahs, if either audio/STT or the text
        # representation includes a leading Basmala while
        # the other side does not, ignore that leading
        # Basmala for the recitation score only.
        # -------------------------------------------------

        basmala_removed_expected = False
        basmala_removed_child = False

        try:
            surah_number_int = int(
                surah_number
            )
            ayah_number_int = int(
                ayah_number
            )
        except Exception:
            surah_number_int = 0
            ayah_number_int = 0

        if (
            ayah_number_int == 1
            and
            surah_number_int not in {
                1,
                9,
            }
        ):

            (
                expected_words,
                basmala_removed_expected,
            ) = (
                remove_leading_basmala_words(
                    expected_words
                )
            )

            (
                child_words,
                basmala_removed_child,
            ) = (
                remove_leading_basmala_words(
                    child_words
                )
            )

        # -------------------------------------------------
        # Empty input
        # -------------------------------------------------

        if not child_words:

            return {
                "handled": True,

                "passed": False,

                "score": 0.0,

                "expected":
                    expected_text,

                "heard":
                    child_text,

                "missing":
                    expected_words,

                "extra": [],

                "substitutions": [],

                "near_matches": [],

                "basmala_ignored":
                    (
                        basmala_removed_expected
                        or
                        basmala_removed_child
                    ),
            }

        # -------------------------------------------------
        # Compare
        # -------------------------------------------------

        comparison = (
            compare_words(
                expected_words,
                child_words,
            )
        )

        distance = (
            comparison[
                "distance"
            ]
        )

        reference_length = max(
            len(expected_words),
            1,
        )

        score = (
            1.0
            -
            (
                distance
                /
                reference_length
            )
        )

        score = max(
            0.0,
            score,
        )

        score = min(
            1.0,
            score,
        )

        score_percent = (
            score * 100
        )

        passed = (
            score_percent
            >=
            self.pass_threshold
        )

        return {
            "handled": True,

            "passed":
                passed,

            "score":
                round(
                    score_percent,
                    2,
                ),

            "threshold":
                self.pass_threshold,

            "surah_number":
                surah_number,

            "ayah_number":
                ayah_number,

            "expected":
                expected_text,

            "expected_normalized":
                expected_normalized,

            "heard":
                child_text,

            "heard_normalized":
                child_normalized,

            "missing":
                comparison[
                    "missing"
                ],

            "extra":
                comparison[
                    "extra"
                ],

            "substitutions":
                comparison[
                    "substitutions"
                ],

            "near_matches":
                comparison[
                    "near_matches"
                ],

            "basmala_ignored":
                (
                    basmala_removed_expected
                    or
                    basmala_removed_child
                ),
        }

    # =====================================================
    # Print Evaluation
    # =====================================================

    def show_result(
        self,
        result,
    ):

        print()
        print("=" * 60)
        print("📖 QURAN EVALUATION")
        print("=" * 60)

        if not result.get(
            "handled"
        ):

            print(
                "❌ Evaluation failed."
            )

            print(
                result
            )

            return

        print(
            f"Expected : "
            f"{result['expected']}"
        )

        print(
            f"Heard    : "
            f"{result['heard']}"
        )

        print()
        print(
            f"🎯 Score : "
            f"{result['score']:.2f}%"
        )

        if result[
            "passed"
        ]:

            print(
                "✅ PASS"
            )

        else:

            print(
                "❌ TRY AGAIN"
            )

        if result[
            "missing"
        ]:

            print()
            print(
                "Missing words:"
            )

            for word in result[
                "missing"
            ]:

                print(
                    f"  - {word}"
                )

        if result[
            "extra"
        ]:

            print()
            print(
                "Extra words:"
            )

            for word in result[
                "extra"
            ]:

                print(
                    f"  + {word}"
                )

        if result[
            "substitutions"
        ]:

            print()
            print(
                "Different words:"
            )

            for item in result[
                "substitutions"
            ]:

                print(
                    f"  "
                    f"{item['heard']} "
                    f"→ "
                    f"{item['expected']}"
                )

        if result.get(
            "near_matches"
        ):

            print()
            print(
                "Near word matches "
                "(small child/STT difference):"
            )

            for item in result[
                "near_matches"
            ]:

                print(
                    f"  ~ "
                    f"{item['heard']} "
                    f"≈ "
                    f"{item['expected']}"
                )

        if result.get(
            "basmala_ignored"
        ):

            print()
            print(
                "ℹ️ Leading Basmala ignored "
                "for first-ayah scoring."
            )

        print("=" * 60)


# =========================================================
# Standalone Test
# =========================================================

def test_evaluator():

    evaluator = (
        QuranEvaluator(
            pass_threshold=85
        )
    )

    evaluator.start()

    print()
    print("=" * 70)
    print("🧪 FINAL QURAN EVALUATOR TEST")
    print("=" * 70)

    # -----------------------------------------------------
    # 1) Verify access to different parts of the Quran
    # -----------------------------------------------------

    references = [
        (1, 1),
        (2, 1),
        (67, 1),
        (112, 1),
        (113, 1),
        (114, 1),
    ]

    for (
        surah,
        ayah,
    ) in references:

        expected = (
            evaluator.get_ayah_text(
                surah,
                ayah,
            )
        )

        print()
        print(
            f"TEXT {surah}:{ayah}:",
            "OK"
            if expected
            else
            "MISSING",
        )

        if not expected:
            continue

        result = evaluator.evaluate(
            surah,
            ayah,
            expected,
        )

        print(
            f"SELF SCORE: "
            f"{result.get('score')}%"
        )

    # -----------------------------------------------------
    # 2) Optional Basmala test
    # -----------------------------------------------------
    #
    # Do not hardcode any Quran verse here.
    # Get the real verse from the local trusted Quran file.
    # -----------------------------------------------------

    expected_112_1 = (
        evaluator.get_ayah_text(
            112,
            1,
        )
    )

    if expected_112_1:

        child_with_basmala = (
            "بسم الله الرحمن الرحيم "
            + expected_112_1
        )

        result = evaluator.evaluate(
            112,
            1,
            child_with_basmala,
        )

        print()
        print(
            "BASMALA OPTIONAL TEST:"
        )
        print(
            "Score:",
            result.get("score"),
        )
        print(
            "Passed:",
            result.get("passed"),
        )
        print(
            "Basmala ignored:",
            result.get(
                "basmala_ignored"
            ),
        )

    print()
    print("=" * 70)


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    test_evaluator()