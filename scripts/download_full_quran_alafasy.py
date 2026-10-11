import time
import urllib.error
import urllib.request
from pathlib import Path


# =========================================================
# EVERYAYAH
# =========================================================

BASE_URL = (
    "https://everyayah.com/data/"
    "Alafasy_128kbps"
)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "audio"
    / "alafasy"
)


# =========================================================
# AYAH COUNTS
# =========================================================

AYAH_COUNTS = {
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


# =========================================================
# DOWNLOAD ONE FILE
# =========================================================

def download_file(
    url,
    destination,
    retries=3,
):

    if (
        destination.exists()
        and
        destination.stat().st_size > 0
    ):

        return "exists"

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = (
        destination.with_suffix(
            ".part"
        )
    )

    for attempt in range(
        1,
        retries + 1,
    ):

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "MimiBot-Quran-Downloader/1.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:

                data = response.read()

            if not data:

                raise RuntimeError(
                    "Empty audio file"
                )

            temp_path.write_bytes(
                data
            )

            temp_path.replace(
                destination
            )

            return "downloaded"

        except urllib.error.HTTPError as error:

            if error.code == 404:

                return "missing"

            print(
                f"⚠️ HTTP error "
                f"{error.code}: {url}"
            )

        except Exception as error:

            print(
                f"⚠️ Attempt "
                f"{attempt}/{retries} failed:"
            )

            print(
                error
            )

        time.sleep(
            1.5
        )

    try:

        temp_path.unlink(
            missing_ok=True
        )

    except Exception:

        pass

    return "failed"


# =========================================================
# DOWNLOAD SURAH
# =========================================================

def download_surah(
    surah_number,
):

    ayah_count = (
        AYAH_COUNTS[
            surah_number
        ]
    )

    folder = (
        OUTPUT_ROOT
        /
        f"{surah_number:03d}"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 70)

    print(
        f"📖 Surah "
        f"{surah_number:03d}"
    )

    print(
        f"آيات: {ayah_count}"
    )

    print("=" * 70)

    downloaded = 0
    existing = 0
    failed = 0

    # =====================================================
    # BASMALA FILE
    # =====================================================
    #
    # EveryAyah includes 000 files for many Surahs.
    # If a particular 000 file does not exist,
    # simply skip it.
    # =====================================================

    source_name = (
        f"{surah_number:03d}"
        f"000.mp3"
    )

    url = (
        f"{BASE_URL}/"
        f"{source_name}"
    )

    destination = (
        folder
        /
        "000.mp3"
    )

    status = download_file(
        url,
        destination,
    )

    if status == "downloaded":

        print(
            "  ✅ 000.mp3"
        )

    elif status == "exists":

        print(
            "  ⏭️ 000.mp3 موجود"
        )

    # =====================================================
    # AYAHS
    # =====================================================

    for ayah_number in range(
        1,
        ayah_count + 1,
    ):

        source_name = (
            f"{surah_number:03d}"
            f"{ayah_number:03d}"
            f".mp3"
        )

        url = (
            f"{BASE_URL}/"
            f"{source_name}"
        )

        destination = (
            folder
            /
            f"{ayah_number:03d}.mp3"
        )

        status = download_file(
            url,
            destination,
        )

        if status == "downloaded":

            downloaded += 1

            print(
                f"  ✅ "
                f"{ayah_number:03d}/"
                f"{ayah_count:03d}"
            )

        elif status == "exists":

            existing += 1

        else:

            failed += 1

            print(
                f"  ❌ "
                f"{ayah_number:03d}"
            )

    print()
    print(
        f"✅ Downloaded: "
        f"{downloaded}"
    )

    print(
        f"⏭️ Existing: "
        f"{existing}"
    )

    print(
        f"❌ Failed: "
        f"{failed}"
    )

    return failed


# =========================================================
# VERIFY
# =========================================================

def verify_quran():

    missing = []

    for (
        surah_number,
        ayah_count,
    ) in AYAH_COUNTS.items():

        folder = (
            OUTPUT_ROOT
            /
            f"{surah_number:03d}"
        )

        for ayah_number in range(
            1,
            ayah_count + 1,
        ):

            path = (
                folder
                /
                f"{ayah_number:03d}.mp3"
            )

            if (
                not path.exists()
                or
                path.stat().st_size == 0
            ):

                missing.append(
                    (
                        surah_number,
                        ayah_number,
                    )
                )

    print()
    print("=" * 70)
    print("🔎 QURAN AUDIO VERIFICATION")
    print("=" * 70)

    if not missing:

        print(
            "✅ جميع ملفات الآيات موجودة."
        )

        return True

    print(
        f"❌ Missing files: "
        f"{len(missing)}"
    )

    for (
        surah,
        ayah,
    ) in missing[:50]:

        print(
            f"Surah "
            f"{surah:03d}, "
            f"Ayah "
            f"{ayah:03d}"
        )

    if len(missing) > 50:

        print(
            "..."
        )

    return False


# =========================================================
# MAIN
# =========================================================

def main():

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 70)
    print("📖 MIMI BOT - FULL QURAN AUDIO")
    print("🎙️ Reciter: Alafasy")
    print("=" * 70)

    total_failed = 0

    for surah_number in range(
        1,
        115,
    ):

        total_failed += (
            download_surah(
                surah_number
            )
        )

    print()
    print("=" * 70)

    print(
        f"Finished downloading."
    )

    print(
        f"Failed files: "
        f"{total_failed}"
    )

    print("=" * 70)

    verify_quran()


if __name__ == "__main__":

    main()
