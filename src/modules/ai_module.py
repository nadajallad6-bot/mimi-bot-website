import json
from pathlib import Path

import joblib


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "ai"
    / "intent_model.joblib"
)

METADATA_FILE = (
    PROJECT_ROOT
    / "models"
    / "ai"
    / "intent_model_metadata.json"
)


# =========================================================
# AI Module
# =========================================================

class AIModule:
    """
    Mimi Bot AI Intent Classification Module.

    مسؤول عن:
    - تحميل الموديل المدرب
    - فهم نية كلام الطفل
    - إرجاع confidence
    - استخدام unknown إذا الثقة منخفضة
    """

    def __init__(
        self,
        confidence_threshold=None,
    ):

        self.model = None

        self.metadata = {}

        self.loaded = False

        self.confidence_threshold = (
            confidence_threshold
        )

    # =====================================================
    # Start
    # =====================================================

    def start(self):

        if self.loaded:
            return

        print()
        print("=" * 60)
        print("🧠 STARTING MIMI AI MODULE")
        print("=" * 60)

        # -------------------------------------------------
        # Check Model
        # -------------------------------------------------

        if not MODEL_FILE.exists():

            raise FileNotFoundError(
                f"AI model not found: "
                f"{MODEL_FILE}"
            )

        # -------------------------------------------------
        # Load Model
        # -------------------------------------------------

        print()
        print(
            "🧠 Loading trained intent model..."
        )

        self.model = (
            joblib.load(
                MODEL_FILE
            )
        )

        # -------------------------------------------------
        # Load Metadata
        # -------------------------------------------------

        if METADATA_FILE.exists():

            try:

                with open(
                    METADATA_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:

                    self.metadata = (
                        json.load(
                            file
                        )
                    )

            except Exception as error:

                print(
                    "⚠️ Metadata error:",
                    error,
                )

                self.metadata = {}

        # -------------------------------------------------
        # Confidence Threshold
        # -------------------------------------------------

        if (
            self.confidence_threshold
            is None
        ):

            self.confidence_threshold = float(
                self.metadata.get(
                    "confidence_threshold",
                    0.55,
                )
            )

        self.loaded = True

        print(
            "✅ AI model loaded."
        )

        print(
            f"🎯 Confidence threshold: "
            f"{self.confidence_threshold:.2f}"
        )

        if self.metadata:

            print(
                f"📊 Training samples: "
                f"{self.metadata.get('total_samples', '?')}"
            )

            print(
                f"🧠 Intents: "
                f"{self.metadata.get('number_of_intents', '?')}"
            )

            accuracy = (
                self.metadata.get(
                    "test_accuracy"
                )
            )

            if accuracy is not None:

                print(
                    f"🎯 Test Accuracy: "
                    f"{accuracy * 100:.2f}%"
                )

        print()
        print(
            "✅ Mimi AI Module ready."
        )

        print("=" * 60)

    # =====================================================
    # Predict
    # =====================================================

    def predict(
        self,
        text,
    ):
        """
        Returns:

        {
            "text": "...",
            "intent": "story",
            "raw_intent": "story",
            "confidence": 0.91,
            "accepted": True
        }
        """

        if not self.loaded:

            self.start()

        text = str(
            text
        ).strip()

        if not text:

            return {
                "text": "",
                "intent": "unknown",
                "raw_intent": "unknown",
                "confidence": 0.0,
                "accepted": False,
            }

        # -------------------------------------------------
        # Prediction
        # -------------------------------------------------

        raw_intent = (
            self.model.predict(
                [text]
            )[0]
        )

        # -------------------------------------------------
        # Probabilities
        # -------------------------------------------------

        probabilities = (
            self.model.predict_proba(
                [text]
            )[0]
        )

        confidence = float(
            max(
                probabilities
            )
        )

        # -------------------------------------------------
        # Threshold
        # -------------------------------------------------

        if (
            confidence
            >= self.confidence_threshold
        ):

            intent = (
                raw_intent
            )

            accepted = True

        else:

            intent = (
                "unknown"
            )

            accepted = False

        return {
            "text":
                text,

            "intent":
                intent,

            "raw_intent":
                raw_intent,

            "confidence":
                confidence,

            "accepted":
                accepted,
        }

    # =====================================================
    # Predict + Debug
    # =====================================================

    def analyze(
        self,
        text,
    ):

        result = (
            self.predict(
                text
            )
        )

        print()
        print("=" * 50)

        print(
            f"👧 Text: "
            f"{result['text']}"
        )

        print(
            f"🧠 Raw intent: "
            f"{result['raw_intent']}"
        )

        print(
            f"🎯 Confidence: "
            f"{result['confidence']:.3f}"
        )

        print(
            f"✅ Final intent: "
            f"{result['intent']}"
        )

        print("=" * 50)

        return result

    # =====================================================
    # Top Predictions
    # =====================================================

    def top_predictions(
        self,
        text,
        top_n=3,
    ):
        """
        مفيدة أثناء تطوير الموديل.

        مثال:
        story 0.70
        riddle 0.15
        unknown 0.05
        """

        if not self.loaded:

            self.start()

        text = str(
            text
        ).strip()

        if not text:

            return []

        probabilities = (
            self.model.predict_proba(
                [text]
            )[0]
        )

        classes = (
            self.model.classes_
        )

        results = []

        for (
            intent,
            probability,
        ) in zip(
            classes,
            probabilities,
        ):

            results.append(
                {
                    "intent":
                        intent,

                    "confidence":
                        float(
                            probability
                        ),
                }
            )

        results.sort(
            key=lambda item:
                item[
                    "confidence"
                ],
            reverse=True,
        )

        return (
            results[:top_n]
        )

    # =====================================================
    # Close
    # =====================================================

    def close(self):

        self.model = None

        self.loaded = False

        print(
            "✅ AI Module closed."
        )


# =========================================================
# Standalone Test
# =========================================================

def test_ai_module():

    ai = (
        AIModule()
    )

    ai.start()

    examples = [
        "ميمي احكيلي حكاية حلوة",
        "نفسي احل حزورة",
        "شغليلي سورة الفلق",
        "بدي احفظ آيتين",
        "شو لازم اعمل اليوم",
        "خلينا نقرأ اذكار الصبح",
        "بدي اذكار قبل ما انام",
        "علّميني العد",
        "ساعديني ميمي",
        "خلص بشوفك بكرا",
        "انا اليوم رحت عند ستي",
    ]

    print()
    print("=" * 60)
    print("🤖 MIMI AI TEST")
    print("=" * 60)

    for sentence in examples:

        result = (
            ai.analyze(
                sentence
            )
        )

        print(
            "Top predictions:"
        )

        for prediction in (
            ai.top_predictions(
                sentence
            )
        ):

            print(
                f"   "
                f"{prediction['intent']:20}"
                f" "
                f"{prediction['confidence']:.3f}"
            )

    # =====================================================
    # Interactive Test
    # =====================================================

    print()
    print("=" * 60)
    print("🎤 INTERACTIVE AI TEST")
    print("=" * 60)

    print(
        "اكتبي أي جملة لميمي."
    )

    print(
        "اكتبي exit للخروج."
    )

    while True:

        print()

        text = input(
            "👧 You: "
        ).strip()

        if text.lower() in (
            "exit",
            "quit",
            "q",
        ):

            break

        result = (
            ai.analyze(
                text
            )
        )

        print()
        print(
            "Top 3:"
        )

        for prediction in (
            ai.top_predictions(
                text
            )
        ):

            print(
                f"- "
                f"{prediction['intent']}: "
                f"{prediction['confidence']:.3f}"
            )

    ai.close()


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    test_ai_module()
