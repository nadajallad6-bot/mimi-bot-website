from datetime import datetime, timezone
from uuid import uuid4

from src.database.mongodb import get_database


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(
        timezone.utc
    )


# =========================================================
# COLLECTION
# =========================================================

def get_collection():

    db = get_database()

    return db[
        "parent_notifications"
    ]


# =========================================================
# INDEXES
# =========================================================

def ensure_indexes():

    collection = get_collection()

    collection.create_index(
        "notification_id",
        unique=True,
    )

    collection.create_index(
        [
            ("child_id", 1),
            ("created_at", -1),
        ]
    )

    collection.create_index(
        [
            ("child_id", 1),
            ("read", 1),
        ]
    )


# =========================================================
# CREATE NOTIFICATION
# =========================================================

def create_notification(
    child_id,
    notification_type,
    title,
    message,
    priority="normal",
    details=None,
):

    if not child_id:
        return None

    ensure_indexes()

    notification_id = (
        "notification_"
        + uuid4().hex[:16]
    )

    now = utc_now()

    document = {
        "notification_id":
            notification_id,

        "child_id":
            str(child_id),

        "notification_type":
            str(notification_type),

        "title":
            str(title),

        "message":
            str(message),

        "priority":
            str(priority),

        "details":
            details or {},

        "read":
            False,

        "created_at":
            now,

        "read_at":
            None,

        "updated_at":
            now,
    }

    get_collection().insert_one(
        document
    )

    print()
    print("=" * 60)
    print("🔔 PARENT NOTIFICATION CREATED")
    print("=" * 60)

    print(
        f"ID: {notification_id}"
    )

    print(
        f"Child: {child_id}"
    )

    print(
        f"Type: {notification_type}"
    )

    print(
        f"Priority: {priority}"
    )

    print("=" * 60)

    return notification_id


# =========================================================
# MARK AS READ
# =========================================================

def mark_notification_read(
    notification_id,
):

    if not notification_id:
        return False

    now = utc_now()

    result = (
        get_collection()
        .update_one(
            {
                "notification_id":
                    notification_id
            },
            {
                "$set": {
                    "read":
                        True,

                    "read_at":
                        now,

                    "updated_at":
                        now,
                }
            },
        )
    )

    return (
        result.modified_count > 0
    )


# =========================================================
# GET UNREAD
# =========================================================

def get_unread_notifications(
    child_id,
    limit=20,
):

    if not child_id:
        return []

    cursor = (
        get_collection()
        .find(
            {
                "child_id":
                    str(child_id),

                "read":
                    False,
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .limit(
            int(limit)
        )
    )

    return list(cursor)


# =========================================================
# GET RECENT
# =========================================================

def get_recent_notifications(
    child_id,
    limit=20,
):

    if not child_id:
        return []

    cursor = (
        get_collection()
        .find(
            {
                "child_id":
                    str(child_id)
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .limit(
            int(limit)
        )
    )

    return list(cursor)


# =========================================================
# READ-ONLY TEST
# =========================================================

def test_notifications():

    child_id = (
        "test_child_001"
    )

    print()
    print("=" * 60)
    print("🔔 NOTIFICATION TEST")
    print("=" * 60)

    notifications = (
        get_recent_notifications(
            child_id,
            limit=10,
        )
    )

    print(
        f"Child: {child_id}"
    )

    print(
        f"Notifications found: "
        f"{len(notifications)}"
    )

    for item in notifications:

        print()
        print(
            item
        )

    print()
    print(
        "✅ Read-only test finished."
    )


if __name__ == "__main__":

    test_notifications()
