import json
import random
import re
from pathlib import Path


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RIDDLES_FILE = (
    PROJECT_ROOT
    / "data"
    / "riddles"
    / "riddles.json"
)


# =========================================================
# Arabic Normalization
# =========================================================

def normalize_arabic(text: str) -> str:

    text = text.strip().lower()

    # Remove tashkeel
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    # Normalize Alef
    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")

    # Normalize Ya
    text = text.replace("ى", "ي")

    # Remove punctuation
    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
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
# Riddle Manager
# =========================================================

class RiddleManager:

    def __init__(self):

        self.riddles = []

        self.current_riddle = None

        self.attempts = 0

        self.total_points = 0

        self.used_riddles = set()

        self.load_riddles()

    # =====================================================
    # Load
    # =====================================================

    def load_riddles(self):

        if not RIDDLES_FILE.exists():

            raise FileNotFoundError(
                f"Riddles file not found: "
                f"{RIDDLES_FILE}"
            )

        with open(
            RIDDLES_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        self.riddles = data.get(
            "riddles",
            [],
        )

        print(
            f"🧩 Loaded {len(self.riddles)} riddles."
        )

    # =====================================================
    # Start Riddle
    # =====================================================

    def start_riddle(self):

        if not self.riddles:

            return None

        # ---------------------------------------------
        # Avoid immediate repetition
        # ---------------------------------------------

        available = [
            riddle
            for riddle in self.riddles
            if riddle["riddle_id"]
            not in self.used_riddles
        ]

        # إذا خلصوا كلهم
        # نعيد الدورة
        if not available:

            self.used_riddles.clear()

            available = list(
                self.riddles
            )

        self.current_riddle = (
            random.choice(
                available
            )
        )

        self.used_riddles.add(
            self.current_riddle[
                "riddle_id"
            ]
        )

        self.attempts = 0

        return {
            "type": "riddle_started",

            "riddle_id":
                self.current_riddle[
                    "riddle_id"
                ],

            "question":
                self.current_riddle[
                    "question"
                ],
        }

    # =====================================================
    # Check Answer
    # =====================================================

    def answer(
        self,
        child_answer,
    ):

        if self.current_riddle is None:

            return {
                "type": "no_riddle",
                "message":
                    "ما في لغز شغال حاليًا.",
            }

        self.attempts += 1

        normalized_answer = (
            normalize_arabic(
                child_answer
            )
        )

        correct = False

        for answer in (
            self.current_riddle[
                "answers"
            ]
        ):

            normalized_expected = (
                normalize_arabic(
                    answer
                )
            )

            if (
                normalized_expected
                in normalized_answer
            ):

                correct = True

                break

        # =================================================
        # Correct
        # =================================================

        if correct:

            points = int(
                self.current_riddle.get(
                    "points",
                    5,
                )
            )

            self.total_points += (
                points
            )

            message = (
                self.current_riddle.get(
                    "success",
                    "شطور!",
                )
            )

            result = {
                "type":
                    "riddle_correct",

                "message":
                    message,

                "points":
                    points,

                "total_points":
                    self.total_points,

                "attempts":
                    self.attempts,
            }

            self.current_riddle = None

            self.attempts = 0

            return result

        # =================================================
        # First wrong attempt
        # =================================================

        if self.attempts == 1:

            return {
                "type":
                    "riddle_hint",

                "message":
                    "مش مشكلة، جرب مرة ثانية.",

                "hint":
                    self.current_riddle.get(
                        "hint",
                        "فكر شوي.",
                    ),
            }

        # =================================================
        # Second wrong attempt
        # =================================================

        correct_answer = (
            self.current_riddle[
                "answers"
            ][0]
        )

        result = {
            "type":
                "riddle_failed",

            "message":
                (
                    "قريبة! "
                    f"الإجابة الصحيحة هي "
                    f"{correct_answer}."
                ),

            "answer":
                correct_answer,

            "points":
                0,

            "total_points":
                self.total_points,
        }

        self.current_riddle = None

        self.attempts = 0

        return result

    # =====================================================
    # State
    # =====================================================

    def is_active(self):

        return (
            self.current_riddle
            is not None
        )

    # =====================================================
    # Reset
    # =====================================================

    def reset_riddle(self):

        self.current_riddle = None

        self.attempts = 0

    # =====================================================
    # Points
    # =====================================================

    def get_points(self):

        return self.total_points


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    manager = RiddleManager()

    print()
    print("=" * 60)
    print("🧩 Mimi Riddle Test")
    print("=" * 60)

    result = (
        manager.start_riddle()
    )

    print()
    print(
        "🤖 Mimi:",
        result["question"],
    )

    while manager.is_active():

        answer = input(
            "\n👧 Child: "
        )

        result = (
            manager.answer(
                answer
            )
        )

        print()
        print(
            "Result:",
            result["type"]
        )

        if (
            result["type"]
            == "riddle_correct"
        ):

            print(
                "🤖 Mimi:",
                result["message"],
            )

            print(
                f"⭐ +{result['points']}"
            )

        elif (
            result["type"]
            == "riddle_hint"
        ):

            print(
                "🤖 Mimi:",
                result["message"],
            )

            print(
                "💡",
                result["hint"],
            )

        elif (
            result["type"]
            == "riddle_failed"
        ):

            print(
                "🤖 Mimi:",
                result["message"],
            )

    print()
    print(
        "⭐ Total points:",
        manager.get_points(),
    )

