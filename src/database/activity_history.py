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
        "activity_history"
    ]


# =========================================================
# INDEXES
# =========================================================

def ensure_indexes():

    collection = (
        get_collection()
    )

    collection.create_index(
        "activity_id",
        unique=True,
    )

    collection.create_index(
        [
            ("child_id", 1),
            ("started_at", -1),
        ]
    )

    collection.create_index(
        [
            ("child_id", 1),
            ("activity_type", 1),
        ]
    )


# =========================================================
# START ACTIVITY
# =========================================================

def start_activity(
    child_id,
    activity_type,
    details=None,
):

    if not child_id:
        return None

    ensure_indexes()

    activity_id = (
        "activity_"
        + uuid4().hex[:16]
    )

    now = utc_now()

    document = {

        "activity_id":
            activity_id,

        "child_id":
            str(child_id),

        "activity_type":
            str(activity_type),

        "status":
            "in_progress",

        "score":
            None,

        "details":
            details or {},

        "started_at":
            now,

        "completed_at":
            None,

        "updated_at":
            now,
    }

    get_collection().insert_one(
        document
    )

    print()
    print(
        f"📝 Activity started: "
        f"{activity_type}"
    )

    print(
        f"🆔 Activity ID: "
        f"{activity_id}"
    )

    return activity_id


# =========================================================
# COMPLETE ACTIVITY
# =========================================================

def complete_activity(
    activity_id,
    status="completed",
    score=None,
    details=None,
):

    if not activity_id:
        return None

    now = utc_now()

    update_data = {

        "status":
            status,

        "completed_at":
            now,

        "updated_at":
            now,
    }

    if score is not None:

        update_data[
            "score"
        ] = score

    if details is not None:

        update_data[
            "details"
        ] = details

    result = (
        get_collection()
        .update_one(
            {
                "activity_id":
                    activity_id
            },
            {
                "$set":
                    update_data
            },
        )
    )

    if result.matched_count == 0:

        print()
        print(
            "⚠️ Activity record "
            "was not found."
        )

        return None

    saved = (
        get_collection()
        .find_one(
            {
                "activity_id":
                    activity_id
            },
            {
                "_id": 0,
            },
        )
    )

    print()
    print(
        f"✅ Activity finished: "
        f"{activity_id}"
    )

    print(
        f"📊 Status: "
        f"{status}"
    )

    return saved


# =========================================================
# GET RECENT ACTIVITIES
# =========================================================

def get_recent_activities(
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
            "started_at",
            -1,
        )
        .limit(
            int(limit)
        )
    )

    return list(
        cursor
    )


# =========================================================
# GET ACTIVITIES BY TYPE
# =========================================================

def get_activities_by_type(
    child_id,
    activity_type,
    limit=20,
):

    cursor = (
        get_collection()
        .find(
            {
                "child_id":
                    str(child_id),

                "activity_type":
                    str(activity_type),
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "started_at",
            -1,
        )
        .limit(
            int(limit)
        )
    )

    return list(
        cursor
    )


# =========================================================
# GET SINGLE ACTIVITY
# =========================================================

def get_activity(
    activity_id,
):

    return (
        get_collection()
        .find_one(
            {
                "activity_id":
                    activity_id
            },
            {
                "_id": 0,
            },
        )
    )


# =========================================================
# READ-ONLY TEST
# =========================================================

def test_activity_history():

    child_id = (
        "test_child_001"
    )

    print()
    print("=" * 60)
    print("📝 ACTIVITY HISTORY TEST")
    print("=" * 60)

    try:

        activities = (
            get_recent_activities(
                child_id,
                limit=10,
            )
        )

        print()
        print(
            f"👧 Child: "
            f"{child_id}"
        )

        print(
            f"📊 Activities found: "
            f"{len(activities)}"
        )

        for item in activities:

            print()
            print(
                item
            )

        print()
        print(
            "✅ Activity history "
            "read test completed."
        )

    except Exception as error:

        print()
        print(
            "❌ Activity history "
            "test failed:"
        )

        print(
            error
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    test_activity_history()
