from datetime import datetime, timezone
from typing import Any

from src.database.mongodb import (
    close_connection,
    get_database,
)


# =========================================================
# Helpers
# =========================================================

def utc_now():
    return datetime.now(timezone.utc)


# =========================================================
# Get Reward Account
# =========================================================

def get_reward_account(
    child_id: str,
) -> dict[str, Any] | None:

    database = get_database()

    return database.rewards.find_one(
        {
            "child_id": child_id
        },
        {
            "_id": 0
        },
    )


# =========================================================
# Get Total Points
# =========================================================

def get_points(
    child_id: str,
) -> int:

    account = get_reward_account(
        child_id
    )

    if account is None:
        return 0

    return int(
        account.get(
            "total_points",
            0,
        )
    )


# =========================================================
# Add Points
# =========================================================

def add_points(
    child_id: str,
    points: int,
    reason: str,
    activity_type: str,
) -> int:
    """
    Adds points to a child and saves a reward event.

    Returns:
        New total points.
    """

    points = int(points)

    if points <= 0:
        return get_points(
            child_id
        )

    database = get_database()

    now = utc_now()

    # -----------------------------------------------------
    # Update total points
    # -----------------------------------------------------

    database.rewards.update_one(
        {
            "child_id": child_id
        },
        {
            "$inc": {
                "total_points": points
            },
            "$set": {
                "updated_at": now
            },
            "$setOnInsert": {
                "child_id": child_id,
                "created_at": now,
            },
        },
        upsert=True,
    )

    # -----------------------------------------------------
    # Save history event
    # -----------------------------------------------------

    database.reward_events.insert_one(
        {
            "child_id": child_id,
            "points": points,
            "reason": reason,
            "activity_type": activity_type,
            "created_at": now,
        }
    )

    # -----------------------------------------------------
    # Return new total
    # -----------------------------------------------------

    return get_points(
        child_id
    )


# =========================================================
# Reward History
# =========================================================

def get_reward_history(
    child_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:

    database = get_database()

    return list(
        database.reward_events.find(
            {
                "child_id": child_id
            },
            {
                "_id": 0
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .limit(
            limit
        )
    )


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    try:

        test_child = (
            "test_child_001"
        )

        print()
        print("=" * 55)
        print("⭐ Mimi Rewards Test")
        print("=" * 55)

        before = get_points(
            test_child
        )

        print(
            f"Points before: {before}"
        )

        total = add_points(
            child_id=test_child,
            points=5,
            reason="حل لغز تجريبي",
            activity_type="riddle",
        )

        print(
            "✅ Added: 5 points"
        )

        print(
            f"⭐ New total: {total}"
        )

        print()
        print("Reward history:")

        history = get_reward_history(
            test_child,
            limit=5,
        )

        for event in history:

            print(
                f"- +{event['points']} | "
                f"{event['activity_type']} | "
                f"{event['reason']}"
            )

    finally:

        close_connection()
