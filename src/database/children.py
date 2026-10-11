from datetime import datetime, timezone
from typing import Any

from src.database.mongodb import close_connection, get_database


def save_child(
    child_id: str,
    name: str,
    age: int | None = None,
) -> dict[str, Any]:
    """إضافة طفل جديد أو تحديث بيانات طفل موجود."""

    child_id = child_id.strip()
    name = name.strip()

    if not child_id:
        raise ValueError("child_id cannot be empty")

    if not name:
        raise ValueError("name cannot be empty")

    if age is not None and not 1 <= age <= 18:
        raise ValueError("age must be between 1 and 18")

    database = get_database()
    now = datetime.now(timezone.utc)

    database.children.update_one(
        {"child_id": child_id},
        {
            "$set": {
                "name": name,
                "age": age,
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    child = database.children.find_one(
        {"child_id": child_id},
        {"_id": 0},
    )

    if child is None:
        raise RuntimeError("Child could not be saved")

    return child


def get_child(child_id: str) -> dict[str, Any] | None:
    """البحث عن طفل باستخدام child_id."""

    database = get_database()

    return database.children.find_one(
        {"child_id": child_id.strip()},
        {"_id": 0},
    )


def list_children() -> list[dict[str, Any]]:
    """إرجاع جميع الأطفال المسجلين."""

    database = get_database()

    return list(
        database.children.find(
            {},
            {"_id": 0},
        )
    )


if __name__ == "__main__":
    try:
        test_child = save_child(
            child_id="test_child_001",
            name="طفل تجريبي",
            age=7,
        )

        print("✅ Child saved successfully:")
        print(test_child)

    finally:
        close_connection()
