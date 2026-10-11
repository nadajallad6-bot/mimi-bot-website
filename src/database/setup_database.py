from pymongo import ASCENDING

from src.database.mongodb import close_connection, get_database


COLLECTIONS = [
    "children",
    "tasks",
    "quran_progress",
]


def setup_database() -> None:
    """إنشاء Collections والفهارس الأساسية لمشروع Mimi Bot."""

    database = get_database()
    existing_collections = set(database.list_collection_names())

    for collection_name in COLLECTIONS:
        if collection_name not in existing_collections:
            database.create_collection(collection_name)
            print(f"✅ Created collection: {collection_name}")
        else:
            print(f"ℹ️ Collection already exists: {collection_name}")

    # كل طفل يمتلك child_id مختلفًا
    database.children.create_index(
        [("child_id", ASCENDING)],
        unique=True,
        name="unique_child_id",
    )

    # كل مهمة تمتلك task_id مختلفًا
    database.tasks.create_index(
        [("task_id", ASCENDING)],
        unique=True,
        name="unique_task_id",
    )

    # تسريع البحث عن مهام طفل حسب حالتها
    database.tasks.create_index(
        [
            ("child_id", ASCENDING),
            ("status", ASCENDING),
        ],
        name="child_tasks_by_status",
    )

    # منع تكرار تقدّم نفس الآية لنفس الطفل
    database.quran_progress.create_index(
        [
            ("child_id", ASCENDING),
            ("surah_number", ASCENDING),
            ("ayah_number", ASCENDING),
        ],
        unique=True,
        name="unique_child_ayah_progress",
    )

    print("✅ Mimi Bot database setup completed successfully")


if __name__ == "__main__":
    try:
        setup_database()
    finally:
        close_connection()
