from src.database.mongodb import (
    get_database,
)


# =========================================================
# COLLECTION
# =========================================================

COLLECTION_NAME = "quran_catalog"


# =========================================================
# DEFAULT READER
# =========================================================

DEFAULT_READER = "alafasy"

DEFAULT_AUDIO_PROVIDER = "everyayah"

DEFAULT_AUDIO_QUALITY = "128kbps"


# =========================================================
# FULL QURAN CATALOG
# =========================================================

QURAN_CATALOG = {
    1: {
        "name": "الفاتحه",
        "ayah_count": 7,
    },

    2: {
        "name": "البقره",
        "ayah_count": 286,
    },

    3: {
        "name": "ال عمران",
        "ayah_count": 200,
    },

    4: {
        "name": "النساء",
        "ayah_count": 176,
    },

    5: {
        "name": "المائده",
        "ayah_count": 120,
    },

    6: {
        "name": "الانعام",
        "ayah_count": 165,
    },

    7: {
        "name": "الاعراف",
        "ayah_count": 206,
    },

    8: {
        "name": "الانفال",
        "ayah_count": 75,
    },

    9: {
        "name": "التوبه",
        "ayah_count": 129,
    },

    10: {
        "name": "يونس",
        "ayah_count": 109,
    },

    11: {
        "name": "هود",
        "ayah_count": 123,
    },

    12: {
        "name": "يوسف",
        "ayah_count": 111,
    },

    13: {
        "name": "الرعد",
        "ayah_count": 43,
    },

    14: {
        "name": "ابراهيم",
        "ayah_count": 52,
    },

    15: {
        "name": "الحجر",
        "ayah_count": 99,
    },

    16: {
        "name": "النحل",
        "ayah_count": 128,
    },

    17: {
        "name": "الاسراء",
        "ayah_count": 111,
    },

    18: {
        "name": "الكهف",
        "ayah_count": 110,
    },

    19: {
        "name": "مريم",
        "ayah_count": 98,
    },

    20: {
        "name": "طه",
        "ayah_count": 135,
    },

    21: {
        "name": "الانبياء",
        "ayah_count": 112,
    },

    22: {
        "name": "الحج",
        "ayah_count": 78,
    },

    23: {
        "name": "المومنون",
        "ayah_count": 118,
    },

    24: {
        "name": "النور",
        "ayah_count": 64,
    },

    25: {
        "name": "الفرقان",
        "ayah_count": 77,
    },

    26: {
        "name": "الشعراء",
        "ayah_count": 227,
    },

    27: {
        "name": "النمل",
        "ayah_count": 93,
    },

    28: {
        "name": "القصص",
        "ayah_count": 88,
    },

    29: {
        "name": "العنكبوت",
        "ayah_count": 69,
    },

    30: {
        "name": "الروم",
        "ayah_count": 60,
    },

    31: {
        "name": "لقمان",
        "ayah_count": 34,
    },

    32: {
        "name": "السجده",
        "ayah_count": 30,
    },

    33: {
        "name": "الاحزاب",
        "ayah_count": 73,
    },

    34: {
        "name": "سبا",
        "ayah_count": 54,
    },

    35: {
        "name": "فاطر",
        "ayah_count": 45,
    },

    36: {
        "name": "يس",
        "ayah_count": 83,
    },

    37: {
        "name": "الصافات",
        "ayah_count": 182,
    },

    38: {
        "name": "ص",
        "ayah_count": 88,
    },

    39: {
        "name": "الزمر",
        "ayah_count": 75,
    },

    40: {
        "name": "غافر",
        "ayah_count": 85,
    },

    41: {
        "name": "فصلت",
        "ayah_count": 54,
    },

    42: {
        "name": "الشوري",
        "ayah_count": 53,
    },

    43: {
        "name": "الزخرف",
        "ayah_count": 89,
    },

    44: {
        "name": "الدخان",
        "ayah_count": 59,
    },

    45: {
        "name": "الجاثيه",
        "ayah_count": 37,
    },

    46: {
        "name": "الاحقاف",
        "ayah_count": 35,
    },

    47: {
        "name": "محمد",
        "ayah_count": 38,
    },

    48: {
        "name": "الفتح",
        "ayah_count": 29,
    },

    49: {
        "name": "الحجرات",
        "ayah_count": 18,
    },

    50: {
        "name": "ق",
        "ayah_count": 45,
    },

    51: {
        "name": "الذاريات",
        "ayah_count": 60,
    },

    52: {
        "name": "الطور",
        "ayah_count": 49,
    },

    53: {
        "name": "النجم",
        "ayah_count": 62,
    },

    54: {
        "name": "القمر",
        "ayah_count": 55,
    },

    55: {
        "name": "الرحمن",
        "ayah_count": 78,
    },

    56: {
        "name": "الواقعه",
        "ayah_count": 96,
    },

    57: {
        "name": "الحديد",
        "ayah_count": 29,
    },

    58: {
        "name": "المجادله",
        "ayah_count": 22,
    },

    59: {
        "name": "الحشر",
        "ayah_count": 24,
    },

    60: {
        "name": "الممتحنه",
        "ayah_count": 13,
    },

    61: {
        "name": "الصف",
        "ayah_count": 14,
    },

    62: {
        "name": "الجمعه",
        "ayah_count": 11,
    },

    63: {
        "name": "المنافقون",
        "ayah_count": 11,
    },

    64: {
        "name": "التغابن",
        "ayah_count": 18,
    },

    65: {
        "name": "الطلاق",
        "ayah_count": 12,
    },

    66: {
        "name": "التحريم",
        "ayah_count": 12,
    },

    67: {
        "name": "الملك",
        "ayah_count": 30,
    },

    68: {
        "name": "القلم",
        "ayah_count": 52,
    },

    69: {
        "name": "الحاقه",
        "ayah_count": 52,
    },

    70: {
        "name": "المعارج",
        "ayah_count": 44,
    },

    71: {
        "name": "نوح",
        "ayah_count": 28,
    },

    72: {
        "name": "الجن",
        "ayah_count": 28,
    },

    73: {
        "name": "المزمل",
        "ayah_count": 20,
    },

    74: {
        "name": "المدثر",
        "ayah_count": 56,
    },

    75: {
        "name": "القيامه",
        "ayah_count": 40,
    },

    76: {
        "name": "الانسان",
        "ayah_count": 31,
    },

    77: {
        "name": "المرسلات",
        "ayah_count": 50,
    },

    78: {
        "name": "النبا",
        "ayah_count": 40,
    },

    79: {
        "name": "النازعات",
        "ayah_count": 46,
    },

    80: {
        "name": "عبس",
        "ayah_count": 42,
    },

    81: {
        "name": "التكوير",
        "ayah_count": 29,
    },

    82: {
        "name": "الانفطار",
        "ayah_count": 19,
    },

    83: {
        "name": "المطففين",
        "ayah_count": 36,
    },

    84: {
        "name": "الانشقاق",
        "ayah_count": 25,
    },

    85: {
        "name": "البروج",
        "ayah_count": 22,
    },

    86: {
        "name": "الطارق",
        "ayah_count": 17,
    },

    87: {
        "name": "الاعلي",
        "ayah_count": 19,
    },

    88: {
        "name": "الغاشيه",
        "ayah_count": 26,
    },

    89: {
        "name": "الفجر",
        "ayah_count": 30,
    },

    90: {
        "name": "البلد",
        "ayah_count": 20,
    },

    91: {
        "name": "الشمس",
        "ayah_count": 15,
    },

    92: {
        "name": "الليل",
        "ayah_count": 21,
    },

    93: {
        "name": "الضحي",
        "ayah_count": 11,
    },

    94: {
        "name": "الشرح",
        "ayah_count": 8,
    },

    95: {
        "name": "التين",
        "ayah_count": 8,
    },

    96: {
        "name": "العلق",
        "ayah_count": 19,
    },

    97: {
        "name": "القدر",
        "ayah_count": 5,
    },

    98: {
        "name": "البينه",
        "ayah_count": 8,
    },

    99: {
        "name": "الزلزله",
        "ayah_count": 8,
    },

    100: {
        "name": "العاديات",
        "ayah_count": 11,
    },

    101: {
        "name": "القارعه",
        "ayah_count": 11,
    },

    102: {
        "name": "التكاثر",
        "ayah_count": 8,
    },

    103: {
        "name": "العصر",
        "ayah_count": 3,
    },

    104: {
        "name": "الهمزه",
        "ayah_count": 9,
    },

    105: {
        "name": "الفيل",
        "ayah_count": 5,
    },

    106: {
        "name": "قريش",
        "ayah_count": 4,
    },

    107: {
        "name": "الماعون",
        "ayah_count": 7,
    },

    108: {
        "name": "الكوثر",
        "ayah_count": 3,
    },

    109: {
        "name": "الكافرون",
        "ayah_count": 6,
    },

    110: {
        "name": "النصر",
        "ayah_count": 3,
    },

    111: {
        "name": "المسد",
        "ayah_count": 5,
    },

    112: {
        "name": "الاخلاص",
        "ayah_count": 4,
    },

    113: {
        "name": "الفلق",
        "ayah_count": 5,
    },

    114: {
        "name": "الناس",
        "ayah_count": 6,
    },
}


# =========================================================
# GET COLLECTION
# =========================================================

def get_collection():

    database = (
        get_database()
    )

    return database[
        COLLECTION_NAME
    ]


# =========================================================
# INDEXES
# =========================================================

def ensure_indexes():

    collection = (
        get_collection()
    )

    collection.create_index(
        "surah_number",
        unique=True,
    )

    collection.create_index(
        "name"
    )

    return True


# =========================================================
# BUILD DOCUMENT
# =========================================================

def build_surah_document(
    surah_number,
    info,
):

    return {
        "surah_number":
            int(
                surah_number
            ),

        "name":
            info[
                "name"
            ],

        "ayah_count":
            int(
                info[
                    "ayah_count"
                ]
            ),

        "reader":
            DEFAULT_READER,

        "audio_provider":
            DEFAULT_AUDIO_PROVIDER,

        "audio_quality":
            DEFAULT_AUDIO_QUALITY,

        "enabled":
            True,
    }


# =========================================================
# SEED FULL QURAN
# =========================================================

def seed_quran_catalog():

    ensure_indexes()

    collection = (
        get_collection()
    )

    inserted = 0
    updated = 0

    for (
        surah_number,
        info,
    ) in QURAN_CATALOG.items():

        document = (
            build_surah_document(
                surah_number,
                info,
            )
        )

        result = (
            collection.update_one(
                {
                    "surah_number":
                        surah_number
                },

                {
                    "$set":
                        document
                },

                upsert=True,
            )
        )

        if (
            result.upserted_id
            is not None
        ):

            inserted += 1

        elif (
            result.modified_count
            > 0
        ):

            updated += 1

    print()
    print("=" * 70)
    print("📖 QURAN CATALOG SEEDED")
    print("=" * 70)

    print(
        f"✅ Inserted: "
        f"{inserted}"
    )

    print(
        f"🔄 Updated: "
        f"{updated}"
    )

    print(
        f"📚 Total Surahs: "
        f"{collection.count_documents({})}"
    )

    print("=" * 70)

    return True


# =========================================================
# GET ONE SURAH
# =========================================================

def get_surah(
    surah_number,
):

    try:

        surah_number = int(
            surah_number
        )

    except Exception:

        return None

    if not 1 <= surah_number <= 114:
        return None

    # -----------------------------------------------------
    # Try MongoDB first.
    # -----------------------------------------------------

    try:

        collection = (
            get_collection()
        )

        document = collection.find_one(
            {
                "surah_number":
                    surah_number,

                "enabled":
                    True,
            },

            {
                "_id":
                    0
            },
        )

        if document is not None:
            return document

    except Exception as error:

        print()
        print(
            "⚠️ Quran catalog MongoDB unavailable."
        )
        print(
            "↩️ Using local Quran catalog fallback."
        )
        print(
            f"ℹ️ Database error: {error}"
        )

    # -----------------------------------------------------
    # Local fallback.
    #
    # QURAN_CATALOG already contains all 114 surahs, so
    # Quran memorization/reading must not stop just because
    # MongoDB Atlas is temporarily unavailable.
    # -----------------------------------------------------

    info = QURAN_CATALOG.get(
        surah_number
    )

    if info is None:
        return None

    return build_surah_document(
        surah_number,
        info,
    )


# =========================================================
# GET SURAH BY NAME
# =========================================================

def get_surah_by_name(
    name,
):

    name = str(
        name
    ).strip()

    if not name:

        return None

    # MongoDB first.
    try:

        collection = (
            get_collection()
        )

        document = collection.find_one(
            {
                "name":
                    name,

                "enabled":
                    True,
            },

            {
                "_id":
                    0
            },
        )

        if document is not None:
            return document

    except Exception as error:

        print()
        print(
            "⚠️ Quran catalog MongoDB unavailable."
        )
        print(
            "↩️ Using local Quran catalog fallback."
        )
        print(
            f"ℹ️ Database error: {error}"
        )

    # Local fallback by exact stored name.
    for surah_number, info in QURAN_CATALOG.items():

        if str(
            info.get(
                "name",
                ""
            )
        ).strip() == name:

            return build_surah_document(
                surah_number,
                info,
            )

    return None


# =========================================================
# GET ALL SURAHS
# =========================================================

def get_all_surahs():

    try:

        collection = (
            get_collection()
        )

        cursor = (
            collection.find(
                {
                    "enabled":
                        True
                },

                {
                    "_id":
                        0
                },
            )
            .sort(
                "surah_number",
                1,
            )
        )

        documents = list(
            cursor
        )

        if documents:
            return documents

    except Exception as error:

        print()
        print(
            "⚠️ Quran catalog MongoDB unavailable."
        )
        print(
            "↩️ Using local Quran catalog fallback."
        )
        print(
            f"ℹ️ Database error: {error}"
        )

    return [
        build_surah_document(
            surah_number,
            info,
        )
        for surah_number, info
        in sorted(
            QURAN_CATALOG.items()
        )
    ]


# =========================================================
# GET AYAH COUNT
# =========================================================

def get_ayah_count(
    surah_number,
):

    surah = (
        get_surah(
            surah_number
        )
    )

    if surah is None:

        return None

    return surah.get(
        "ayah_count"
    )


# =========================================================
# CHECK SURAH
# =========================================================

def surah_exists(
    surah_number,
):

    return (
        get_surah(
            surah_number
        )
        is not None
    )


# =========================================================
# GET AUDIO METADATA
# =========================================================

def get_audio_metadata(
    surah_number,
):

    surah = (
        get_surah(
            surah_number
        )
    )

    if surah is None:

        return None

    return {
        "surah_number":
            surah.get(
                "surah_number"
            ),

        "surah_name":
            surah.get(
                "name"
            ),

        "ayah_count":
            surah.get(
                "ayah_count"
            ),

        "reader":
            surah.get(
                "reader"
            ),

        "audio_provider":
            surah.get(
                "audio_provider"
            ),

        "audio_quality":
            surah.get(
                "audio_quality"
            ),
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    seed_quran_catalog()

    print()
    print(
        "🔎 Testing Surah Al-Mulk..."
    )

    surah = (
        get_surah(
            67
        )
    )

    print(
        surah
    )

    print()
    print(
        "🔎 Testing Surah Al-Baqarah..."
    )

    surah = (
        get_surah(
            2
        )
    )

    print(
        surah
    )

    print()
    print(
        "🔎 First 5 Surahs:"
    )

    all_surahs = (
        get_all_surahs()
    )

    for surah in (
        all_surahs[:5]
    ):

        print(
            surah[
                "surah_number"
            ],
            "-",
            surah[
                "name"
            ],
            "-",
            surah[
                "ayah_count"
            ],
            "آيات",
        )