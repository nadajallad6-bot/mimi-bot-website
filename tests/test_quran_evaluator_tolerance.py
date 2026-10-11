"""
Mimi Bot - Quran Evaluator Tolerance Test

Tests:
1) Exact recitation
2) Small one-letter STT/pronunciation difference
3) Missing word
4) Clearly wrong word

Run:
    cd ~/Projects/mimi-bot
    source .venv/bin/activate
    PYTHONPATH=. python tests/test_quran_evaluator_tolerance.py
"""

from src.modules.quran_evaluator import QuranEvaluator


def show_case(title, evaluator, surah, ayah, child_text):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    result = evaluator.evaluate(
        surah_number=surah,
        ayah_number=ayah,
        child_text=child_text,
    )

    evaluator.show_result(result)

    print()
    print("RAW RESULT:")
    print(result)

    return result


def main():
    evaluator = QuranEvaluator(
        pass_threshold=85.0
    )

    evaluator.start()

    # سورة الإخلاص - آية 1
    # Expected text is read from quran_text.json,
    # so we don't hardcode Quran text except test inputs.

    expected = evaluator.get_ayah_text(
        112,
        1,
    )

    print()
    print("Expected from Quran JSON:")
    print(expected)

    # -------------------------------------------------
    # 1) Exact
    # -------------------------------------------------
    show_case(
        "CASE 1 - EXACT",
        evaluator,
        112,
        1,
        expected,
    )

    # -------------------------------------------------
    # 2) Small one-letter difference
    # Example STT may hear "احد" as "اهد".
    # -------------------------------------------------
    show_case(
        "CASE 2 - ONE LETTER DIFFERENCE",
        evaluator,
        112,
        1,
        "قل هو الله اهد",
    )

    # -------------------------------------------------
    # 3) Missing whole word
    # -------------------------------------------------
    show_case(
        "CASE 3 - MISSING WORD",
        evaluator,
        112,
        1,
        "قل هو الله",
    )

    # -------------------------------------------------
    # 4) Clearly different word
    # -------------------------------------------------
    show_case(
        "CASE 4 - WRONG WORD",
        evaluator,
        112,
        1,
        "قل هو الرحمن احد",
    )

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()