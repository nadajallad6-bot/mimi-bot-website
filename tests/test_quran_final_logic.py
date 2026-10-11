from src.modules.quran_module import QuranModule


# =========================================================
# MIMI QURAN FINAL LOGIC TEST
# =========================================================
#
# This test does NOT play real audio.
#
# It verifies:
#
# 1. Reading mode:
#    every ayah plays ONCE.
#
# 2. Memorization mode:
#    current ayah plays THREE TIMES,
#    then Mimi waits for child.
#
# 3. One correct child recitation:
#    completes current ayah and moves to next,
#    which is again played THREE TIMES.
#
# =========================================================


class FakePlayer:

    def __init__(self):
        self.calls = []

    def detect_speaker(self):
        return "fake-speaker"

    def play_ayah(
        self,
        surah_number,
        ayah_number,
        prefetch=True,
    ):
        self.calls.append(
            (
                int(surah_number),
                int(ayah_number),
            )
        )

        print(
            f"FAKE PLAY: "
            f"{int(surah_number)}:"
            f"{int(ayah_number)}"
        )

        return True


def assert_equal(
    actual,
    expected,
    label,
):

    if actual != expected:

        raise AssertionError(
            f"{label}\n"
            f"Expected: {expected}\n"
            f"Actual  : {actual}"
        )

    print(
        f"✅ {label}"
    )


def main():

    # =====================================================
    # TEST 1 - READING MODE
    # =====================================================

    print()
    print("=" * 70)
    print(
        "TEST 1 - READING MODE PLAYS EACH AYAH ONCE"
    )
    print("=" * 70)

    quran = QuranModule(
        voice_module=None,
        child_id=None,
        reader="alafasy",
        repeat_target=3,
        pass_threshold=85.0,
    )

    fake = FakePlayer()

    quran.player = fake

    quran.start_module()

    # Al-Kawthar = 3 ayahs.
    result = quran.start_reading(
        surah_number=108
    )

    assert_equal(
        result.get("completed"),
        True,
        "Reading completed",
    )

    assert_equal(
        fake.calls,
        [
            (108, 1),
            (108, 2),
            (108, 3),
        ],
        "Reading plays every ayah exactly once",
    )

    quran.close()

    # =====================================================
    # TEST 2 - MEMORIZATION START
    # =====================================================

    print()
    print("=" * 70)
    print(
        "TEST 2 - MEMORIZATION PLAYS AYAH 3 TIMES"
    )
    print("=" * 70)

    quran = QuranModule(
        voice_module=None,
        child_id=None,
        reader="alafasy",
        repeat_target=3,
        pass_threshold=85.0,
    )

    fake = FakePlayer()

    quran.player = fake

    quran.start_module()

    result = quran.start_memorization(
        surah_number=112
    )

    assert_equal(
        result.get("started"),
        True,
        "Memorization started",
    )

    assert_equal(
        fake.calls,
        [
            (112, 1),
            (112, 1),
            (112, 1),
        ],
        "First ayah is taught exactly 3 times",
    )

    assert_equal(
        quran.is_waiting_for_child(),
        True,
        "Mimi waits for child only after 3 reciter plays",
    )

    # =====================================================
    # TEST 3 - CORRECT CHILD RECITATION
    # =====================================================

    print()
    print("=" * 70)
    print(
        "TEST 3 - ONE CORRECT CHILD RECITATION MOVES NEXT"
    )
    print("=" * 70)

    expected = quran.evaluator.get_ayah_text(
        112,
        1,
    )

    if not expected:
        raise AssertionError(
            "Could not load 112:1 from quran_text.json"
        )

    result = quran.register_repeat(
        child_text=expected
    )

    assert_equal(
        result.get("passed"),
        True,
        "Correct child recitation passes",
    )

    assert_equal(
        result.get("ayah_completed"),
        True,
        "Ayah 1 completed after one correct child recitation",
    )

    assert_equal(
        result.get("next_ayah"),
        2,
        "Moved to Ayah 2",
    )

    assert_equal(
        fake.calls,
        [
            (112, 1),
            (112, 1),
            (112, 1),

            (112, 2),
            (112, 2),
            (112, 2),
        ],
        "Next ayah is immediately taught 3 times",
    )

    assert_equal(
        quran.is_waiting_for_child(),
        True,
        "Mimi waits for child after teaching Ayah 2 three times",
    )

    quran.close()

    print()
    print("=" * 70)
    print(
        "✅ ALL FINAL QURAN LOGIC TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":

    main()