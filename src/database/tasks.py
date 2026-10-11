from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.database.mongodb import close_connection, get_database


VALID_STATUSES = {"pending", "completed", "cancelled"}


def create_task(
    child_id: str,
    title: str,
    description: str = "",
    category: str = "study",
    due_at: datetime | None = None,
) -> dict[str, Any]:
    """إنشاء مهمة جديدة لطفل مسجل."""

    child_id = child_id.strip()
    title = title.strip()
    description = description.strip()
    category = category.strip()

    if not child_id:
        raise ValueError("child_id cannot be empty")

    if not title:
        raise ValueError("title cannot be empty")

    database = get_database()

    child_exists = database.children.find_one(
        {"child_id": child_id},
        {"_id": 1},
    )

    if child_exists is None:
        raise ValueError(f"Child does not exist: {child_id}")

    now = datetime.now(timezone.utc)
    task_id = f"task_{uuid4().hex[:12]}"

    task = {
        "task_id": task_id,
        "child_id": child_id,
        "title": title,
        "description": description,
        "category": category,
        "status": "pending",
        "due_at": due_at,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    database.tasks.insert_one(task)

    task.pop("_id", None)
    return task


def get_task(task_id: str) -> dict[str, Any] | None:
    """البحث عن مهمة باستخدام رقمها."""

    database = get_database()

    return database.tasks.find_one(
        {"task_id": task_id.strip()},
        {"_id": 0},
    )


def list_child_tasks(
    child_id: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """إرجاع مهام طفل محدد."""

    query: dict[str, Any] = {
        "child_id": child_id.strip(),
    }

    if status is not None:
        status = status.strip().lower()

        if status not in VALID_STATUSES:
            raise ValueError(
                f"status must be one of: {sorted(VALID_STATUSES)}"
            )

        query["status"] = status

    database = get_database()

    return list(
        database.tasks.find(
            query,
            {"_id": 0},
        ).sort("created_at", -1)
    )


def complete_task(task_id: str) -> dict[str, Any] | None:
    """تغيير حالة المهمة إلى مكتملة."""

    database = get_database()
    now = datetime.now(timezone.utc)

    result = database.tasks.update_one(
        {"task_id": task_id.strip()},
        {
            "$set": {
                "status": "completed",
                "completed_at": now,
                "updated_at": now,
            }
        },
    )

    if result.matched_count == 0:
        return None

    return get_task(task_id)


if __name__ == "__main__":
    try:
        test_task = create_task(
            child_id="test_child_001",
            title="مراجعة سورة الفلق",
            description="الاستماع إلى السورة وتكرار أول آيتين",
            category="quran",
        )

        print("✅ Task created successfully:")
        print(test_task)

    finally:
        close_connection()
