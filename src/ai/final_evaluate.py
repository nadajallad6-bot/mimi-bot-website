import json
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from src.modules.ai_module import AIModule


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "ai"
    / "final_evaluation.json"
)


# =========================================================
# FINAL UNSEEN TEST
# لا نضيف هذه الجمل إلى training dataset
# =========================================================

TEST_CASES = [

    # -----------------------------------------------------
    # greeting
    # -----------------------------------------------------

    ("صباح الورد يا ميمي", "greeting"),
    ("هلا والله ميمي", "greeting"),
    ("ميمي شو أخبارك اليوم", "greeting"),
    ("يسعد صباحك ميمي", "greeting"),
    ("مرحبتين كيف حالك", "greeting"),

    # -----------------------------------------------------
    # story
    # -----------------------------------------------------

    ("بدنا نسمع حكاية عن قطة", "story"),
    ("احكيلي حكاية قبل النوم", "story"),
    ("شو رأيك تحكيلنا قصة جديدة", "story"),
    ("ميمي اختاري حكاية واحكيلي ياها", "story"),
    ("نفسي اسمع قصة ممتعة", "story"),

    # -----------------------------------------------------
    # riddle
    # -----------------------------------------------------

    ("بدنا نلعب لعبة حزازير", "riddle"),
    ("ورجيني لغز أشوف إذا بعرفه", "riddle"),
    ("اعطيني حزورة أفكر فيها", "riddle"),
    ("اسأليني سؤال يحتاج تفكير", "riddle"),
    ("يلا نلعب لغز جديد", "riddle"),

    # -----------------------------------------------------
    # quran_read
    # -----------------------------------------------------

    ("ممكن تسمعيني سورة الناس", "quran_read"),
    ("نفسي اسمع شوية قرآن", "quran_read"),
    ("اقرأيلي سورة من القرآن", "quran_read"),
    ("شغلي تلاوة سورة الفلق", "quran_read"),
    ("ميمي بدي أسمع آيات", "quran_read"),

    # -----------------------------------------------------
    # quran_memorize
    # -----------------------------------------------------

    ("ساعديني أحفظ أول آية", "quran_memorize"),
    ("خلينا نراجع اللي حفظته", "quran_memorize"),
    ("بدي أقرأ وإنت تصححيلي", "quran_memorize"),
    ("خليني أردد الآية وراك", "quran_memorize"),
    ("اختبريني بالسورة اللي حفظتها", "quran_memorize"),

    # -----------------------------------------------------
    # tasks
    # -----------------------------------------------------

    ("شو مطلوب مني أعمل هسا", "tasks"),
    ("عندي واجبات مسجلة عندك", "tasks"),
    ("ميمي ذكّريني شو علي", "tasks"),
    ("شو المهام اللي لسا ما خلصتها", "tasks"),
    ("احكيلي شو عندي لليوم", "tasks"),

    # -----------------------------------------------------
    # morning_adhkar
    # -----------------------------------------------------

    ("يلا نبدأ يومنا بذكر الله", "morning_adhkar"),
    ("شو بنقرأ من أذكار الصبح", "morning_adhkar"),
    ("ميمي احكي معي أذكار الصباح", "morning_adhkar"),
    ("بدي أسمع ذكر الصبح", "morning_adhkar"),
    ("نقرأ الأذكار قبل ما أبدأ يومي", "morning_adhkar"),

    # -----------------------------------------------------
    # evening_adhkar
    # -----------------------------------------------------

    ("خلينا نختم اليوم بأذكار المساء", "evening_adhkar"),
    ("ميمي شو أذكار الليل", "evening_adhkar"),
    ("بدي أقرأ ذكر المساء", "evening_adhkar"),
    ("احكيلي أذكار قبل ما أنام", "evening_adhkar"),
    ("نقرأ أذكارنا بالليل", "evening_adhkar"),

    # -----------------------------------------------------
    # learning
    # -----------------------------------------------------

    ("علّميني أعد من واحد لعشرة", "learning"),
    ("بدنا نتعلم الألوان اليوم", "learning"),
    ("ميمي اشرحيلي الجمع", "learning"),
    ("خلينا نتعلم حرف جديد", "learning"),
    ("بدي أعمل نشاط تعليمي", "learning"),

    # -----------------------------------------------------
    # help
    # -----------------------------------------------------

    ("ميمي ممكن توقفي معي شوي", "help"),
    ("مش فاهم هاد الاشي ساعديني", "help"),
    ("محتاج مساعدتك يا ميمي", "help"),
    ("ساعديني أعرف شو أعمل", "help"),
    ("ميمي بدي منك تساعديني", "help"),

    # -----------------------------------------------------
    # goodbye
    # -----------------------------------------------------

    ("يلا أنا ماشي بشوفك بعدين", "goodbye"),
    ("شكرا ميمي نشوفك بكرا", "goodbye"),
    ("خلص بكفي لليوم سلام", "goodbye"),
    ("أنا رايحة هسا باي", "goodbye"),
    ("تصبحي على خير يا ميمي", "goodbye"),

    # -----------------------------------------------------
    # unknown
    # -----------------------------------------------------

    ("اليوم أكلت رز ودجاج", "unknown"),
    ("عندي كرة لونها أحمر", "unknown"),
    ("أختي راحت تزور ستي", "unknown"),
    ("أنا بحب فصل الشتاء", "unknown"),
    ("اليوم المدرسة كانت حلوة", "unknown"),
]


# =========================================================
# Main
# =========================================================

def main():

    ai = AIModule()

    ai.start()

    expected_labels = []
    predicted_labels = []

    mistakes = []

    detailed_results = []

    print()
    print("=" * 70)
    print("🧠 MIMI AI FINAL UNSEEN TEST")
    print("=" * 70)

    for index, (
        sentence,
        expected,
    ) in enumerate(
        TEST_CASES,
        start=1,
    ):

        result = ai.predict(
            sentence
        )

        predicted = result[
            "intent"
        ]

        raw_intent = result[
            "raw_intent"
        ]

        confidence = float(
            result[
                "confidence"
            ]
        )

        expected_labels.append(
            expected
        )

        predicted_labels.append(
            predicted
        )

        correct = (
            predicted == expected
        )

        item = {
            "number": index,
            "text": sentence,
            "expected": expected,
            "predicted": predicted,
            "raw_intent": raw_intent,
            "confidence": confidence,
            "correct": correct,
        }

        detailed_results.append(
            item
        )

        if not correct:

            mistakes.append(
                item
            )

        status = (
            "✅"
            if correct
            else "❌"
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
            f"Raw        : {raw_intent}"
        )

        print(
            f"Predicted  : {predicted}"
        )

        print(
            f"Confidence : {confidence:.3f}"
        )

    # =====================================================
    # Accuracy
    # =====================================================

    accuracy = accuracy_score(
        expected_labels,
        predicted_labels,
    )

    total = len(
        TEST_CASES
    )

    correct_count = sum(
        1
        for item in detailed_results
        if item["correct"]
    )

    print()
    print("=" * 70)
    print("📊 FINAL RESULT")
    print("=" * 70)

    print(
        f"Correct  : "
        f"{correct_count}/{total}"
    )

    print(
        f"Accuracy : "
        f"{accuracy * 100:.2f}%"
    )

    # =====================================================
    # Classification Report
    # =====================================================

    report = classification_report(
        expected_labels,
        predicted_labels,
        digits=3,
        zero_division=0,
        output_dict=True,
    )

    print()
    print("=" * 70)
    print("📋 CLASSIFICATION REPORT")
    print("=" * 70)

    print(
        classification_report(
            expected_labels,
            predicted_labels,
            digits=3,
            zero_division=0,
        )
    )

    # =====================================================
    # Confusion Matrix
    # =====================================================

    labels = sorted(
        set(
            expected_labels
        )
    )

    matrix = confusion_matrix(
        expected_labels,
        predicted_labels,
        labels=labels,
    )

    print()
    print("=" * 70)
    print("🔀 CONFUSION MATRIX")
    print("=" * 70)

    print()

    for index, label in enumerate(
        labels
    ):

        print(
            f"{index:2} = {label}"
        )

    print()
    print(
        matrix
    )

    # =====================================================
    # Mistakes
    # =====================================================

    print()
    print("=" * 70)
    print("❌ FINAL TEST MISTAKES")
    print("=" * 70)

    if not mistakes:

        print()
        print(
            "🔥 No mistakes!"
        )

    else:

        for item in mistakes:

            print()
            print(
                f"Text       : "
                f"{item['text']}"
            )

            print(
                f"Expected   : "
                f"{item['expected']}"
            )

            print(
                f"Raw        : "
                f"{item['raw_intent']}"
            )

            print(
                f"Predicted  : "
                f"{item['predicted']}"
            )

            print(
                f"Confidence : "
                f"{item['confidence']:.3f}"
            )

    # =====================================================
    # Save Report
    # =====================================================

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_report = {
        "total_tests": total,
        "correct": correct_count,
        "accuracy": float(
            accuracy
        ),
        "confidence_threshold":
            ai.confidence_threshold,
        "classification_report":
            report,
        "mistakes":
            mistakes,
        "all_results":
            detailed_results,
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            final_report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)

    print(
        "✅ Evaluation saved:"
    )

    print(
        REPORT_FILE
    )

    print("=" * 70)

    ai.close()


if __name__ == "__main__":

    main()
