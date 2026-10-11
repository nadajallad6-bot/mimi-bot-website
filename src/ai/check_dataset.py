import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_FILE = (
    PROJECT_ROOT
    / "data"
    / "ai"
    / "intents.json"
)


def main():

    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    intents = data.get(
        "intents",
        []
    )

    all_patterns = []

    print()
    print("=" * 60)
    print("📊 MIMI AI DATASET")
    print("=" * 60)

    for intent in intents:

        tag = intent["tag"]

        patterns = intent.get(
            "patterns",
            []
        )

        print(
            f"{tag:20} : {len(patterns)}"
        )

        all_patterns.extend(
            patterns
        )

    print()
    print("=" * 60)

    print(
        f"Number of intents : {len(intents)}"
    )

    print(
        f"Total sentences   : {len(all_patterns)}"
    )

    normalized = [
        text.strip().lower()
        for text in all_patterns
    ]

    counts = Counter(
        normalized
    )

    duplicates = [
        text
        for text, count
        in counts.items()
        if count > 1
    ]

    print(
        f"Duplicates        : {len(duplicates)}"
    )

    if duplicates:

        print()
        print("⚠️ Duplicate sentences:")

        for text in duplicates:

            print(
                "-",
                text
            )

    else:

        print()
        print(
            "✅ No duplicate sentences."
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
