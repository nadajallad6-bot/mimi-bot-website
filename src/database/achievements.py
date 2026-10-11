from datetime import datetime, timezone

from src.database.mongodb import get_database


# =========================================================
# ACHIEVEMENT DEFINITIONS
# =========================================================

ACHIEVEMENTS = {
    "first_riddle": {
        "title": "بطل الألغاز",
        "description": "حل أول لغز بشكل صحيح",
        "emoji": "🧩",
    },

    "points_10": {
        "title": "جامع النجوم",
        "description": "وصل إلى 10 نقاط",
        "emoji": "⭐",
    },

    "points_25": {
        "title": "النجم الصغير",
        "description": "وصل إلى 25 نقطة",
        "emoji": "🌟",
    },

    "points_50": {
        "title": "النجم الذهبي",
        "description": "وصل إلى 50 نقطة",
        "emoji": "🏆",
    },

    "first_story": {
        "title": "محب القصص",
        "description": "أكمل أول قصة",
        "emoji": "📚",
    },

    "first_learning": {
        "title": "المتعلم الصغير",
        "description": "أكمل أول نشاط تعليمي",
        "emoji": "🎓",
    },

    "first_quran_ayah": {
        "title": "بداية مباركة",
        "description": "أتقن أول آية في وضع الحفظ",
        "emoji": "📖",
    },

    "first_surah": {
        "title": "حافظ صغير",
        "description": "أكمل حفظ أول سورة",
        "emoji": "🌙",
    },

    "first_quran_read": {
        "title": "رفيق القرآن",
        "description": "أكمل أول جلسة استماع للقرآن",
        "emoji": "🎧",
    },

    "first_adhkar": {
        "title": "ذاكر صغير",
        "description": "أكمل أول جلسة أذكار",
        "emoji": "🤲",
    },

    "first_tasks_view": {
        "title": "منظم صغير",
        "description": "راجع مهامه لأول مرة",
        "emoji": "📋",
    },
}


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
        "achievements"
    ]


# =========================================================
# INDEXES
# =========================================================

def ensure_indexes():

    collection = get_collection()

    collection.create_index(
        [
            ("child_id", 1),
            ("achievement_key", 1),
        ],
        unique=True,
    )

    collection.create_index(
        [
            ("child_id", 1),
            ("earned_at", -1),
        ]
    )


# =========================================================
# GET ACHIEVEMENT INFO
# =========================================================

def get_achievement_definition(
    achievement_key,
):

    return ACHIEVEMENTS.get(
        achievement_key
    )


# =========================================================
# AWARD ACHIEVEMENT
# =========================================================

def award_achievement(
    child_id,
    achievement_key,
    details=None,
):

    if not child_id:

        return {
            "awarded": False,
            "reason": "missing_child_id",
        }

    definition = (
        get_achievement_definition(
            achievement_key
        )
    )

    if definition is None:

        return {
            "awarded": False,
            "reason": "unknown_achievement",
        }

    ensure_indexes()

    collection = get_collection()

    now = utc_now()

    document = {
        "child_id": str(child_id),

        "achievement_key":
            achievement_key,

        "title":
            definition[
                "title"
            ],

        "description":
            definition[
                "description"
            ],

        "emoji":
            definition[
                "emoji"
            ],

        "details":
            details or {},

        "earned_at":
            now,
    }

    result = collection.update_one(
        {
            "child_id":
                str(child_id),

            "achievement_key":
                achievement_key,
        },
        {
            "$setOnInsert":
                document
        },
        upsert=True,
    )

    newly_awarded = (
        result.upserted_id
        is not None
    )

    saved = collection.find_one(
        {
            "child_id":
                str(child_id),

            "achievement_key":
                achievement_key,
        },
        {
            "_id": 0,
        },
    )

    return {
        "awarded":
            newly_awarded,

        "achievement":
            saved,
    }


# =========================================================
# HAS ACHIEVEMENT
# =========================================================

def has_achievement(
    child_id,
    achievement_key,
):

    if not child_id:

        return False

    record = (
        get_collection()
        .find_one(
            {
                "child_id":
                    str(child_id),

                "achievement_key":
                    achievement_key,
            }
        )
    )

    return (
        record is not None
    )


# =========================================================
# GET CHILD ACHIEVEMENTS
# =========================================================

def get_child_achievements(
    child_id,
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
            "earned_at",
            -1,
        )
    )

    return list(
        cursor
    )


# =========================================================
# COUNT
# =========================================================

def count_child_achievements(
    child_id,
):

    if not child_id:

        return 0

    return (
        get_collection()
        .count_documents(
            {
                "child_id":
                    str(child_id)
            }
        )
    )


# =========================================================
# READ TEST
# =========================================================

def test_achievements():

    child_id = (
        "test_child_001"
    )

    print()
    print("=" * 60)
    print("🏆 ACHIEVEMENTS TEST")
    print("=" * 60)

    achievements = (
        get_child_achievements(
            child_id
        )
    )

    print(
        f"Child: {child_id}"
    )

    print(
        f"Achievements: "
        f"{len(achievements)}"
    )

    for item in achievements:

        print()
        print(
            f"{item.get('emoji', '')} "
            f"{item.get('title', '')}"
        )

        print(
            item.get(
                "description",
                ""
            )
        )

    print()
    print(
        "✅ Read-only test finished."
    )


if __name__ == "__main__":

    test_achievements()
