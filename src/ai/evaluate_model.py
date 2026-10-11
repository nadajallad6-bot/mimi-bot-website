from src.modules.ai_module import AIModule


TEST_CASES = [
    # greeting
    ("ميمي صباحو", "greeting"),
    ("اهلين كيفك اليوم", "greeting"),

    # story
    ("نفسي اسمع منك حكاية", "story"),
    ("احكيلنا حكاية عن حيوان", "story"),

    # riddle
    ("بدنا نحزر حزورة", "riddle"),
    ("جربي تعطيني سؤال ذكاء", "riddle"),

    # quran_read
    ("شغليلي سورة الناس", "quran_read"),
    ("نفسي اسمع تلاوة قرآن", "quran_read"),

    # quran_memorize
    ("خلينا نحفظ اول آيتين", "quran_memorize"),
    ("اسمعيني وانا براجع السورة", "quran_memorize"),

    # tasks
    ("شو الأشياء اللي لازم اعملها اليوم", "tasks"),
    ("عندي واجب اليوم ولا لا", "tasks"),

    # morning adhkar
    ("نبدأ الصبح بالأذكار", "morning_adhkar"),

    # evening adhkar
    ("اقرأيلي أذكار قبل الليل", "evening_adhkar"),

    # learning
    ("بدنا نتعلم العد اليوم", "learning"),
    ("علّميني كيف اجمع", "learning"),

    # help
    ("ميمي مش فاهمة ساعديني", "help"),

    # goodbye
    ("خلص نشوفك بعدين", "goodbye"),

    # unknown
    ("اليوم لعبت مع صحابي بالمدرسة", "unknown"),
    ("انا بحب عصير البرتقال", "unknown"),
]


def main():

    ai = AIModule()

    ai.start()

    correct = 0
    wrong = []

    print()
    print("=" * 70)
    print("🧠 MIMI AI REAL TEST")
    print("=" * 70)

    for index, (sentence, expected) in enumerate(
        TEST_CASES,
        start=1,
    ):

        result = ai.predict(
            sentence
        )

        predicted = result[
            "intent"
        ]

        confidence = result[
            "confidence"
        ]

        is_correct = (
            predicted == expected
        )

        if is_correct:

            correct += 1

            status = "✅"

        else:

            status = "❌"

            wrong.append(
                {
                    "sentence": sentence,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": confidence,
                    "raw_intent": result["raw_intent"],
                }
            )

        print()
        print(
            f"{status} Test {index}"
        )

        print(
            f"Text       : {sentence}"
        )

        print(
            f"Expected   : {expected}"
        )

        print(
            f"Predicted  : {predicted}"
        )

        print(
            f"Confidence : {confidence:.3f}"
        )

    total = len(
        TEST_CASES
    )

    accuracy = (
        correct / total
    )

    print()
    print("=" * 70)
    print("📊 REAL TEST RESULT")
    print("=" * 70)

    print(
        f"Correct : {correct}/{total}"
    )

    print(
        f"Accuracy: {accuracy * 100:.2f}%"
    )

    # =====================================================
    # Wrong Predictions
    # =====================================================

    if wrong:

        print()
        print("=" * 70)
        print("❌ WRONG PREDICTIONS")
        print("=" * 70)

        for item in wrong:

            print()
            print(
                f"Text      : {item['sentence']}"
            )

            print(
                f"Expected  : {item['expected']}"
            )

            print(
                f"Predicted : {item['predicted']}"
            )

            print(
                f"Raw       : {item['raw_intent']}"
            )

            print(
                f"Confidence: {item['confidence']:.3f}"
            )

    else:

        print()
        print(
            "🔥 All real test sentences were correct!"
        )

    ai.close()


if __name__ == "__main__":
    main()
