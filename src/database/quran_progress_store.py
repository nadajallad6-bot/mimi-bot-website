from datetime import datetime, timezone

from src.database.mongodb import get_database


# =========================================================
# Helpers
# =========================================================

def utc_now():
    return datetime.now(
        timezone.utc
    )


# =========================================================
# Collection
# =========================================================

def get_collection():
    db = get_database()

    return db[
        "quran_progress"
    ]


# =========================================================
# Save Mastered Ayah
# =========================================================

def save_mastered_ayah(
    child_id,
    surah_number,
    ayah_number,
    score,
    attempts,
    successful_repetitions=3,
    repeat_target=3,
    pass_threshold=85.0,
):
    """
    يحفظ أن الطفل أتقن آية.

    يتم استدعاؤها فقط بعد نجاح
    repeat_target مرات صحيحة.
    """

    if not child_id:
        return None

    child_id = str(
        child_id
    ).strip()

    surah_number = int(
        surah_number
    )

    ayah_number = int(
        ayah_number
    )

    score = float(
        score
    )

    attempts = int(
        attempts
    )

    successful_repetitions = int(
        successful_repetitions
    )

    repeat_target = int(
        repeat_target
    )

    pass_threshold = float(
        pass_threshold
    )

    collection = (
        get_collection()
    )

    now = utc_now()

    query = {
        "child_id":
            child_id,

        "surah_number":
            surah_number,

        "ayah_number":
            ayah_number,
    }

    update = {

        "$set": {

            "child_id":
                child_id,

            "surah_number":
                surah_number,

            "ayah_number":
                ayah_number,

            "last_score":
                score,

            "successful_repetitions":
                successful_repetitions,

            "repeat_target":
                repeat_target,

            "pass_threshold":
                pass_threshold,

            "mastered":
                True,

            "mastered_at":
                now,

            "updated_at":
                now,
        },

        "$max": {

            "best_score":
                score,
        },

        "$inc": {

            "attempts":
                attempts,
        },

        "$setOnInsert": {

            "created_at":
                now,
        },
    }

    collection.update_one(
        query,
        update,
        upsert=True,
    )

    saved = (
        collection.find_one(
            query,
            {
                "_id": 0,
            },
        )
    )

    return saved


# =========================================================
# Get One Ayah
# =========================================================

def get_ayah_progress(
    child_id,
    surah_number,
    ayah_number,
):

    collection = (
        get_collection()
    )

    return (
        collection.find_one(
            {
                "child_id":
                    str(child_id),

                "surah_number":
                    int(
                        surah_number
                    ),

                "ayah_number":
                    int(
                        ayah_number
                    ),
            },
            {
                "_id": 0,
            },
        )
    )


# =========================================================
# Get Surah Progress
# =========================================================

def get_surah_progress(
    child_id,
    surah_number,
):

    collection = (
        get_collection()
    )

    cursor = (
        collection.find(
            {
                "child_id":
                    str(child_id),

                "surah_number":
                    int(
                        surah_number
                    ),
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "ayah_number",
            1,
        )
    )

    return list(
        cursor
    )


# =========================================================
# Get Mastered Ayahs
# =========================================================

def get_mastered_ayahs(
    child_id,
    surah_number,
):

    records = (
        get_surah_progress(
            child_id,
            surah_number,
        )
    )

    mastered = []

    for record in records:

        if record.get(
            "mastered",
            False,
        ):

            mastered.append(
                int(
                    record[
                        "ayah_number"
                    ]
                )
            )

    return mastered


# =========================================================
# Get Next Ayah
# =========================================================

def get_next_ayah(
    child_id,
    surah_number,
    ayah_count,
):
    """
    يرجع أول آية غير محفوظة.

    مثال:
        mastered = [1, 2]
        -> returns 3

    إذا السورة كاملة:
        -> returns None
    """

    mastered = set(
        get_mastered_ayahs(
            child_id,
            surah_number,
        )
    )

    for ayah_number in range(
        1,
        int(
            ayah_count
        ) + 1,
    ):

        if (
            ayah_number
            not in mastered
        ):

            return ayah_number

    return None


# =========================================================
# Is Surah Completed
# =========================================================

def is_surah_completed(
    child_id,
    surah_number,
    ayah_count,
):

    next_ayah = (
        get_next_ayah(
            child_id,
            surah_number,
            ayah_count,
        )
    )

    return (
        next_ayah is None
    )


# =========================================================
# Summary
# =========================================================

def get_surah_summary(
    child_id,
    surah_number,
    ayah_count,
):

    records = (
        get_surah_progress(
            child_id,
            surah_number,
        )
    )

    mastered = [
        record
        for record in records
        if record.get(
            "mastered",
            False,
        )
    ]

    next_ayah = (
        get_next_ayah(
            child_id,
            surah_number,
            ayah_count,
        )
    )

    return {

        "child_id":
            str(child_id),

        "surah_number":
            int(
                surah_number
            ),

        "ayah_count":
            int(
                ayah_count
            ),

        "mastered_count":
            len(
                mastered
            ),

        "mastered_ayahs": [
            item[
                "ayah_number"
            ]
            for item in mastered
        ],

        "next_ayah":
            next_ayah,

        "completed":
            next_ayah is None,
    }


# =========================================================
# Standalone READ-ONLY Test
# =========================================================

def test_progress():

    child_id = (
        "test_child_001"
    )

    print()
    print("=" * 60)
    print("📖 QURAN PROGRESS DATABASE TEST")
    print("=" * 60)

    try:

        print()
        print(
            "Child:",
            child_id,
        )

        print()

        print(
            "Surah 113 progress:"
        )

        records = (
            get_surah_progress(
                child_id,
                113,
            )
        )

        if not records:

            print(
                "No progress records yet."
            )

        else:

            for record in records:

                print(
                    record
                )

        print()
        print(
            "Summary:"
        )

        summary = (
            get_surah_summary(
                child_id,
                113,
                5,
            )
        )

        print(
            summary
        )

        print()
        print(
            "✅ Database read test completed."
        )

    except Exception as error:

        print()
        print(
            "❌ Quran database test failed:"
        )

        print(
            error
        )


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    test_progress()
