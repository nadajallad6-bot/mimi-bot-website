from datetime import datetime, timezone
from typing import Any

from src.database.mongodb import close_connection, get_database


def save_ayah_attempt(
    child_id: str,
    surah_number: int,
    surah_name: str,
    ayah_number: int,
    score: float,
    target_repetitions: int = 3,
    mastery_threshold: float = 85.0,
) -> dict[str, Any]:
    """حفظ نتيجة محاولة الطفل في تكرار آية."""

    child_id = child_id.strip()
    surah_name = surah_name.strip()

    if not child_id:
        raise ValueError("child_id cannot be empty")

    if not 1 <= surah_number <= 114:
        raise ValueError("surah_number must be between 1 and 114")

    if ayah_number < 1:
        raise ValueError("ayah_number must be greater than zero")

    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")

    if target_repetitions < 1:
        raise ValueError("target_repetitions must be at least 1")

    database = get_database()

    child_exists = database.children.find_one(
        {"child_id": child_id},
        {"_id": 1},
    )

    if child_exists is None:
        raise ValueError(f"Child does not exist: {child_id}")

    query = {
        "child_id": child_id,
        "surah_number": surah_number,
        "ayah_number": ayah_number,
    }

    old_progress = database.quran_progress.find_one(query)

    attempts = 1
    repetitions_completed = 0
    best_score = score
    created_at = datetime.now(timezone.utc)

    if old_progress is not None:
        attempts = old_progress.get("attempts", 0) + 1
        repetitions_completed = old_progress.get(
            "repetitions_completed",
            0,
        )
        best_score = max(
            float(old_progress.get("best_score", 0)),
            score,
        )
        created_at = old_progress.get("created_at", created_at)

    if score >= mastery_threshold:
        repetitions_completed += 1

    repetitions_completed = min(
        repetitions_completed,
        target_repetitions,
    )

    mastered = repetitions_completed >= target_repetitions
    now = datetime.now(timezone.utc)

    progress = {
        "child_id": child_id,
        "surah_number": surah_number,
        "surah_name": surah_name,
        "ayah_number": ayah_number,
        "attempts": attempts,
        "last_score": score,
        "best_score": best_score,
        "mastery_threshold": mastery_threshold,
        "repetitions_completed": repetitions_completed,
        "target_repetitions": target_repetitions,
        "mastered": mastered,
        "created_at": created_at,
        "updated_at": now,
    }

    database.quran_progress.update_one(
        query,
        {"$set": progress},
        upsert=True,
    )

    return progress


def get_ayah_progress(
    child_id: str,
    surah_number: int,
    ayah_number: int,
) -> dict[str, Any] | None:
    """إرجاع تقدّم طفل في آية محددة."""

    database = get_database()

    return database.quran_progress.find_one(
        {
            "child_id": child_id.strip(),
            "surah_number": surah_number,
            "ayah_number": ayah_number,
        },
        {"_id": 0},
    )


def list_surah_progress(
    child_id: str,
    surah_number: int,
) -> list[dict[str, Any]]:
    """إرجاع تقدّم الطفل في جميع آيات سورة محددة."""

    database = get_database()

    return list(
        database.quran_progress.find(
            {
                "child_id": child_id.strip(),
                "surah_number": surah_number,
            },
            {"_id": 0},
        ).sort("ayah_number", 1)
    )


if __name__ == "__main__":
    try:
        test_progress = save_ayah_attempt(
            child_id="test_child_001",
            surah_number=113,
            surah_name="سورة الفلق",
            ayah_number=1,
            score=88.5,
            target_repetitions=3,
            mastery_threshold=85.0,
        )

        print("✅ Quran progress saved successfully:")
        print(test_progress)

    finally:
        close_connection()
