import json
from pathlib import Path


# =========================================================
# MIMI BOT
# TANZIL UTHMANI QURAN TEXT IMPORTER
# =========================================================
#
# Current Tanzil source used by Mimi:
#
# Plain UTF-8 text
# One ayah per line
# 6236 Quran ayahs total
#
# IMPORTANT:
# Quran text itself is NEVER modified.
#
# =========================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "source"
    / "quran-uthmani.txt"
)


OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "quran_text.json"
)


BACKUP_FILE = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "quran_text_before_full.json"
)


SOURCE_INFO_FILE = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "QURAN_TEXT_SOURCE.txt"
)


# =========================================================
# QURAN STRUCTURE
# =========================================================

EXPECTED_COUNTS = {
    1: 7,
    2: 286,
    3: 200,
    4: 176,
    5: 120,
    6: 165,
    7: 206,
    8: 75,
    9: 129,
    10: 109,
    11: 123,
    12: 111,
    13: 43,
    14: 52,
    15: 99,
    16: 128,
    17: 111,
    18: 110,
    19: 98,
    20: 135,
    21: 112,
    22: 78,
    23: 118,
    24: 64,
    25: 77,
    26: 227,
    27: 93,
    28: 88,
    29: 69,
    30: 60,
    31: 34,
    32: 30,
    33: 73,
    34: 54,
    35: 45,
    36: 83,
    37: 182,
    38: 88,
    39: 75,
    40: 85,
    41: 54,
    42: 53,
    43: 89,
    44: 59,
    45: 37,
    46: 35,
    47: 38,
    48: 29,
    49: 18,
    50: 45,
    51: 60,
    52: 49,
    53: 62,
    54: 55,
    55: 78,
    56: 96,
    57: 29,
    58: 22,
    59: 24,
    60: 13,
    61: 14,
    62: 11,
    63: 11,
    64: 18,
    65: 12,
    66: 12,
    67: 30,
    68: 52,
    69: 52,
    70: 44,
    71: 28,
    72: 28,
    73: 20,
    74: 56,
    75: 40,
    76: 31,
    77: 50,
    78: 40,
    79: 46,
    80: 42,
    81: 29,
    82: 19,
    83: 36,
    84: 25,
    85: 22,
    86: 17,
    87: 19,
    88: 26,
    89: 30,
    90: 20,
    91: 15,
    92: 21,
    93: 11,
    94: 8,
    95: 8,
    96: 19,
    97: 5,
    98: 8,
    99: 8,
    100: 11,
    101: 11,
    102: 8,
    103: 3,
    104: 9,
    105: 5,
    106: 4,
    107: 7,
    108: 3,
    109: 6,
    110: 3,
    111: 5,
    112: 4,
    113: 5,
    114: 6,
}


EXPECTED_TOTAL_AYAHS = sum(
    EXPECTED_COUNTS.values()
)


# =========================================================
# READ SOURCE
# =========================================================

def read_source_lines():

    if not SOURCE_FILE.exists():

        raise FileNotFoundError(
            "Source file not found:\n"
            f"{SOURCE_FILE}"
        )

    text = SOURCE_FILE.read_text(
        encoding="utf-8"
    )

    # splitlines removes only newline separators.
    # It does NOT normalize or alter Quran text.
    return text.splitlines()


# =========================================================
# EXTRACT QURAN LINES
# =========================================================
#
# Tanzil plain-text Quran starts directly with Quran text.
#
# The Quran body contains exactly 6236 ayah lines.
#
# Any attribution / license / metadata appearing after
# those lines is kept OUTSIDE quran_text.json.
#
# =========================================================

def extract_quran_lines(
    source_lines,
):

    quran_lines = []

    started = False

    for line in source_lines:

        # ---------------------------------------------
        # Before Quran starts:
        # ignore empty lines only.
        # ---------------------------------------------

        if not started:

            if line == "":

                continue

            started = True

        # ---------------------------------------------
        # Once Quran starts, collect exactly 6236 lines.
        # ---------------------------------------------

        if (
            len(quran_lines)
            <
            EXPECTED_TOTAL_AYAHS
        ):

            if line == "":

                raise ValueError(
                    "Unexpected blank line inside "
                    "the Quran body at ayah index "
                    f"{len(quran_lines) + 1}."
                )

            quran_lines.append(
                line
            )

            continue

        # ---------------------------------------------
        # Everything after 6236 Quran lines is metadata
        # from the downloaded source and is not imported.
        # ---------------------------------------------

    return quran_lines


# =========================================================
# MAP SEQUENTIAL LINES TO SURAH / AYAH
# =========================================================

def build_quran_structure(
    quran_lines,
):

    if (
        len(quran_lines)
        !=
        EXPECTED_TOTAL_AYAHS
    ):

        raise ValueError(
            "Wrong Quran ayah count.\n"
            f"Expected: {EXPECTED_TOTAL_AYAHS}\n"
            f"Found   : {len(quran_lines)}"
        )

    quran = {}

    line_index = 0

    for surah_number in range(
        1,
        115,
    ):

        surah_key = str(
            surah_number
        )

        quran[
            surah_key
        ] = {}

        ayah_count = (
            EXPECTED_COUNTS[
                surah_number
            ]
        )

        for ayah_number in range(
            1,
            ayah_count + 1,
        ):

            if (
                line_index
                >=
                len(quran_lines)
            ):

                raise ValueError(
                    "Source ended unexpectedly "
                    f"at Surah {surah_number}, "
                    f"Ayah {ayah_number}."
                )

            # -----------------------------------------
            # CRITICAL:
            # Store Tanzil text EXACTLY as downloaded.
            # No replace(), normalization, strip(), etc.
            # -----------------------------------------

            verse_text = (
                quran_lines[
                    line_index
                ]
            )

            quran[
                surah_key
            ][
                str(ayah_number)
            ] = verse_text

            line_index += 1

    if (
        line_index
        !=
        EXPECTED_TOTAL_AYAHS
    ):

        raise ValueError(
            "Internal mapping count mismatch."
        )

    return quran


# =========================================================
# VALIDATE STRUCTURE
# =========================================================

def validate_quran(
    quran,
):

    errors = []

    if len(quran) != 114:

        errors.append(
            "Expected 114 surahs, "
            f"found {len(quran)}."
        )

    total = 0

    for surah_number in range(
        1,
        115,
    ):

        surah_key = str(
            surah_number
        )

        surah = quran.get(
            surah_key
        )

        if surah is None:

            errors.append(
                f"Missing Surah {surah_number}."
            )

            continue

        expected_count = (
            EXPECTED_COUNTS[
                surah_number
            ]
        )

        actual_count = len(
            surah
        )

        total += actual_count

        if (
            actual_count
            !=
            expected_count
        ):

            errors.append(
                f"Surah {surah_number}: "
                f"expected {expected_count}, "
                f"found {actual_count}."
            )

        for ayah_number in range(
            1,
            expected_count + 1,
        ):

            ayah_key = str(
                ayah_number
            )

            if (
                ayah_key
                not in
                surah
            ):

                errors.append(
                    "Missing Ayah "
                    f"{surah_number}:"
                    f"{ayah_number}."
                )

                continue

            verse_text = (
                surah[
                    ayah_key
                ]
            )

            if not verse_text:

                errors.append(
                    "Empty Ayah "
                    f"{surah_number}:"
                    f"{ayah_number}."
                )

    if (
        total
        !=
        EXPECTED_TOTAL_AYAHS
    ):

        errors.append(
            "Expected total "
            f"{EXPECTED_TOTAL_AYAHS} ayahs, "
            f"found {total}."
        )

    return (
        errors,
        total,
    )


# =========================================================
# BACKUP OLD FILE
# =========================================================

def backup_old_file():

    if not OUTPUT_FILE.exists():

        return

    if BACKUP_FILE.exists():

        print(
            "💾 Previous backup already exists:"
        )

        print(
            BACKUP_FILE
        )

        return

    BACKUP_FILE.write_bytes(
        OUTPUT_FILE.read_bytes()
    )

    print()
    print(
        "💾 Backup created:"
    )

    print(
        BACKUP_FILE
    )


# =========================================================
# SAVE JSON
# =========================================================

def save_quran(
    quran,
):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            quran,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# =========================================================
# SAVE SOURCE ATTRIBUTION
# =========================================================

def save_source_info():

    text = (
        "Mimi Bot Quran Text Source\n"
        "==========================\n"
        "\n"
        "Source: Tanzil Project\n"
        "Text type: Uthmani Quran Text\n"
        "Website: https://tanzil.net/\n"
        "Download: https://tanzil.net/download/\n"
        "\n"
        "Quran text is used verbatim and is not modified.\n"
    )

    SOURCE_INFO_FILE.write_text(
        text,
        encoding="utf-8",
    )


# =========================================================
# PRINT SMALL STRUCTURE TEST
# =========================================================

def print_structure_test(
    quran,
):

    print()
    print(
        "🔎 Structure check:"
    )

    tests = [
        (1, 7),
        (2, 286),
        (67, 30),
        (113, 5),
        (114, 6),
    ]

    for (
        surah_number,
        expected,
    ) in tests:

        actual = len(
            quran[
                str(surah_number)
            ]
        )

        print(
            f"Surah {surah_number:3d}: "
            f"{actual} ayahs "
            f"(expected {expected})"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print(
        "📖 MIMI QURAN TEXT IMPORT"
    )
    print("=" * 70)

    print(
        "Source:"
    )

    print(
        SOURCE_FILE
    )

    print()

    # =====================================================
    # READ
    # =====================================================

    source_lines = (
        read_source_lines()
    )

    print(
        "Source file lines:",
        len(source_lines),
    )

    # =====================================================
    # EXTRACT 6236 QURAN LINES
    # =====================================================

    quran_lines = (
        extract_quran_lines(
            source_lines
        )
    )

    print(
        "Quran ayah lines:",
        len(quran_lines),
    )

    extra_lines = (
        len(source_lines)
        -
        len(quran_lines)
    )

    print(
        "Remaining source lines:",
        extra_lines,
    )

    # =====================================================
    # BUILD
    # =====================================================

    quran = (
        build_quran_structure(
            quran_lines
        )
    )

    # =====================================================
    # VALIDATE
    # =====================================================

    (
        errors,
        total_ayahs,
    ) = validate_quran(
        quran
    )

    print()
    print(
        "Surahs:",
        len(quran),
    )

    print(
        "Total ayahs:",
        total_ayahs,
    )

    # =====================================================
    # VALIDATION FAILURE
    # =====================================================

    if errors:

        print()
        print(
            "❌ QURAN VALIDATION FAILED"
        )

        for error in errors[:50]:

            print(
                " -",
                error,
            )

        print()
        print(
            "Existing quran_text.json "
            "was NOT replaced."
        )

        raise SystemExit(
            1
        )

    # =====================================================
    # STRUCTURE TEST
    # =====================================================

    print_structure_test(
        quran
    )

    # =====================================================
    # BACKUP
    # =====================================================

    backup_old_file()

    # =====================================================
    # SAVE
    # =====================================================

    save_quran(
        quran
    )

    save_source_info()

    # =====================================================
    # SUCCESS
    # =====================================================

    print()
    print("=" * 70)

    print(
        "✅ QURAN TEXT IMPORT SUCCESS"
    )

    print("=" * 70)

    print(
        "✅ 114 Surahs"
    )

    print(
        f"✅ {total_ayahs} Ayahs"
    )

    print(
        "✅ Tanzil Uthmani text preserved"
    )

    print()
    print(
        "Saved:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Source attribution:"
    )

    print(
        SOURCE_INFO_FILE
    )

    print("=" * 70)


if __name__ == "__main__":

    main()