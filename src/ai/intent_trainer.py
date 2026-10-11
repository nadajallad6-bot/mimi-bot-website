import json
from pathlib import Path

import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score,
)
from sklearn.pipeline import Pipeline


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_FILE = (
    PROJECT_ROOT
    / "data"
    / "ai"
    / "intents.json"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "ai"
)

MODEL_FILE = (
    MODEL_DIR
    / "intent_model.joblib"
)

METADATA_FILE = (
    MODEL_DIR
    / "intent_model_metadata.json"
)


# =========================================================
# Load Dataset
# =========================================================

def load_dataset():

    print()
    print("=" * 60)
    print("📂 LOADING MIMI AI DATASET")
    print("=" * 60)

    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    texts = []
    labels = []

    intents = data.get(
        "intents",
        []
    )

    for intent in intents:

        tag = intent["tag"]

        patterns = intent.get(
            "patterns",
            []
        )

        for sentence in patterns:

            sentence = (
                str(sentence)
                .strip()
            )

            if not sentence:
                continue

            texts.append(
                sentence
            )

            labels.append(
                tag
            )

    print(
        f"✅ Total sentences: "
        f"{len(texts)}"
    )

    print(
        f"✅ Total intents: "
        f"{len(set(labels))}"
    )

    return (
        texts,
        labels,
    )


# =========================================================
# Create Model
# =========================================================

def create_model():

    """
    Character n-grams are useful for Arabic dialect text
    because they tolerate small spelling differences.

    Example:
        بدي قصة
        بدي قصه
        بديلي قصة
    """

    return Pipeline(
        [
            (
                "tfidf",

                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),

            (
                "classifier",

                LogisticRegression(
                    max_iter=3000,
                    random_state=42,
                ),
            ),
        ]
    )


# =========================================================
# Cross Validation
# =========================================================

def run_cross_validation(
    model,
    texts,
    labels,
):

    print()
    print("=" * 60)
    print("🔄 CROSS VALIDATION")
    print("=" * 60)

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    scores = cross_val_score(
        model,
        texts,
        labels,
        cv=cv,
        scoring="f1_macro",
    )

    print()

    for index, score in enumerate(
        scores,
        start=1,
    ):

        print(
            f"Fold {index}: "
            f"{score * 100:.2f}%"
        )

    average_score = (
        scores.mean()
    )

    print()
    print(
        f"📊 Average Macro F1: "
        f"{average_score * 100:.2f}%"
    )

    return float(
        average_score
    )


# =========================================================
# Train Model
# =========================================================

def train_model():

    texts, labels = (
        load_dataset()
    )

    # =====================================================
    # Train / Test Split
    # =====================================================

    (
        x_train,
        x_test,
        y_train,
        y_test,
    ) = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    print()
    print("=" * 60)
    print("📊 DATA SPLIT")
    print("=" * 60)

    print(
        f"Training samples: "
        f"{len(x_train)}"
    )

    print(
        f"Testing samples: "
        f"{len(x_test)}"
    )

    # =====================================================
    # Create Model
    # =====================================================

    model = (
        create_model()
    )

    # =====================================================
    # Cross Validation
    # =====================================================

    cv_score = (
        run_cross_validation(
            create_model(),
            texts,
            labels,
        )
    )

    # =====================================================
    # Train
    # =====================================================

    print()
    print("=" * 60)
    print("🧠 TRAINING MIMI AI")
    print("=" * 60)

    model.fit(
        x_train,
        y_train,
    )

    print()
    print(
        "✅ Training completed."
    )

    # =====================================================
    # Predict Test Set
    # =====================================================

    predictions = (
        model.predict(
            x_test
        )
    )

    accuracy = (
        accuracy_score(
            y_test,
            predictions,
        )
    )

    # =====================================================
    # Accuracy
    # =====================================================

    print()
    print("=" * 60)
    print("🎯 TEST RESULTS")
    print("=" * 60)

    print(
        f"Accuracy: "
        f"{accuracy * 100:.2f}%"
    )

    # =====================================================
    # Classification Report
    # =====================================================

    print()
    print("=" * 60)
    print("📋 CLASSIFICATION REPORT")
    print("=" * 60)

    print(
        classification_report(
            y_test,
            predictions,
            digits=3,
            zero_division=0,
        )
    )

    # =====================================================
    # Confusion Matrix
    # =====================================================

    labels_sorted = sorted(
        set(labels)
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels_sorted,
    )

    print()
    print("=" * 60)
    print("🔀 CONFUSION MATRIX")
    print("=" * 60)

    print()
    print(
        "Labels order:"
    )

    for index, label in enumerate(
        labels_sorted
    ):

        print(
            f"{index:2} = {label}"
        )

    print()
    print(
        matrix
    )

    # =====================================================
    # Wrong Predictions
    # =====================================================

    print()
    print("=" * 60)
    print("❌ MISCLASSIFIED SENTENCES")
    print("=" * 60)

    wrong_count = 0

    probabilities = (
        model.predict_proba(
            x_test
        )
    )

    for (
        sentence,
        expected,
        predicted,
        probs,
    ) in zip(
        x_test,
        y_test,
        predictions,
        probabilities,
    ):

        if expected != predicted:

            wrong_count += 1

            confidence = (
                float(
                    max(probs)
                )
            )

            print()
            print(
                f"Sentence   : "
                f"{sentence}"
            )

            print(
                f"Expected   : "
                f"{expected}"
            )

            print(
                f"Predicted  : "
                f"{predicted}"
            )

            print(
                f"Confidence : "
                f"{confidence:.3f}"
            )

    if wrong_count == 0:

        print()
        print(
            "✅ No misclassified "
            "test sentences."
        )

    else:

        print()
        print(
            f"Total mistakes: "
            f"{wrong_count}"
        )

    # =====================================================
    # Retrain on ALL Data
    # =====================================================

    print()
    print("=" * 60)
    print(
        "🧠 TRAINING FINAL MODEL "
        "ON ALL DATA"
    )
    print("=" * 60)

    final_model = (
        create_model()
    )

    final_model.fit(
        texts,
        labels,
    )

    # =====================================================
    # Save
    # =====================================================

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        final_model,
        MODEL_FILE,
    )

    metadata = {
        "model_type":
            "TF-IDF Character N-Grams + Logistic Regression",

        "total_samples":
            len(texts),

        "number_of_intents":
            len(set(labels)),

        "intents":
            labels_sorted,

        "test_accuracy":
            float(accuracy),

        "cross_validation_macro_f1":
            cv_score,

        "confidence_threshold":
            0.55,
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "✅ Final model saved:"
    )

    print(
        MODEL_FILE
    )

    print()
    print(
        "✅ Metadata saved:"
    )

    print(
        METADATA_FILE
    )

    return (
        final_model,
        accuracy,
    )


# =========================================================
# Quick Real Examples
# =========================================================

def quick_test(
    model,
):

    print()
    print("=" * 60)
    print("🤖 QUICK MIMI AI TEST")
    print("=" * 60)

    examples = [
        "ميمي ممكن تحكيلي حكاية",
        "نفسي احل حزورة",
        "ممكن تسمعيني سورة الفلق",
        "خلينا نحفظ آيتين",
        "شو علي شغل اليوم",
        "بدي اذكار الصبح",
        "اقرأيلي اذكار الليل",
        "علّميني العد",
        "ممكن تساعديني",
        "يلا بشوفك بكرا",
        "انا اليوم لعبت مع صحابي"
    ]

    for sentence in examples:

        predicted = (
            model.predict(
                [sentence]
            )[0]
        )

        probabilities = (
            model.predict_proba(
                [sentence]
            )[0]
        )

        confidence = float(
            max(probabilities)
        )

        final_intent = (
            predicted
            if confidence >= 0.55
            else "unknown"
        )

        print()
        print(
            f"👧 {sentence}"
        )

        print(
            f"🧠 Prediction : "
            f"{predicted}"
        )

        print(
            f"🎯 Confidence : "
            f"{confidence:.3f}"
        )

        print(
            f"✅ Final       : "
            f"{final_intent}"
        )


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    (
        trained_model,
        test_accuracy,
    ) = train_model()

    quick_test(
        trained_model
    )
