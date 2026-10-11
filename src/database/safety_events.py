from datetime import datetime, timezone
from uuid import uuid4

from src.database.mongodb import get_database


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc)


# =========================================================
# COLLECTION
# =========================================================

def get_collection():

    db = get_database()

    return db["safety_events"]


# =========================================================
# INDEXES
# =========================================================

def ensure_indexes():

    collection = get_collection()

    collection.create_index(
        "event_id",
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
            ("status", 1),
            ("created_at", -1),
        ]
    )


# =========================================================
# CREATE SAFETY EVENT
# =========================================================

def create_safety_event(
    child_id,
    trigger_type,
    trigger_text=None,
    severity="high",
    details=None,
):

    # -----------------------------------------------------
    # We currently save safety events only for
    # registered children.
    # Guest safety still works locally.
    # -----------------------------------------------------

    if not child_id:
        return None

    ensure_indexes()

    event_id = (
        "safety_"
        + uuid4().hex[:16]
    )

    now = utc_now()

    document = {
        "event_id":
            event_id,

        "child_id":
            str(child_id),

        "trigger_type":
            str(trigger_type),

        "trigger_text":
            trigger_text,

        "severity":
            severity,

        "status":
            "active",

        "details":
            details or {},

        "created_at":
            now,

        "resolved_at":
            None,

        "resolution":
            None,

        "updated_at":
            now,
    }

    get_collection().insert_one(
        document
    )

    print()
    print("=" * 60)
    print("🚨 SAFETY EVENT SAVED")
    print("=" * 60)

    print(
        f"Event ID: {event_id}"
    )

    print(
        f"Child: {child_id}"
    )

    print(
        f"Trigger: {trigger_type}"
    )

    print("=" * 60)

    return event_id


# =========================================================
# RESOLVE SAFETY EVENT
# =========================================================

def resolve_safety_event(
    event_id,
    resolution="manual_clear",
):

    if not event_id:
        return None

    now = utc_now()

    result = (
        get_collection()
        .update_one(
            {
                "event_id":
                    event_id
            },
            {
                "$set": {
                    "status":
                        "resolved",

                    "resolution":
                        resolution,

                    "resolved_at":
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
# GET ACTIVE EVENTS
# =========================================================

def get_active_events(
    child_id,
):

    if not child_id:
        return []

    cursor = (
        get_collection()
        .find(
            {
                "child_id":
                    str(child_id),

                "status":
                    "active",
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
    )

    return list(cursor)


# =========================================================
# GET RECENT EVENTS
# =========================================================

def get_recent_events(
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

def test_safety_events():

    child_id = "test_child_001"

    print()
    print("=" * 60)
    print("🚨 SAFETY EVENTS TEST")
    print("=" * 60)

    events = get_recent_events(
        child_id,
        limit=10,
    )

    print(
        f"Child: {child_id}"
    )

    print(
        f"Events found: {len(events)}"
    )

    for event in events:

        print()
        print(event)

    print()
    print(
        "✅ Read-only safety test finished."
    )


if __name__ == "__main__":
    test_safety_events()
