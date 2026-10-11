import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.database.quran_catalog import (
    get_surah,
)


# =========================================================
# AUDIO PROVIDER
# =========================================================

EVERYAYAH_BASE_URL = (
    "https://everyayah.com/data/"
    "Alafasy_128kbps"
)


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

AUDIO_ROOT = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "audio"
    / "alafasy"
)


# =========================================================
# SETTINGS
# =========================================================

DOWNLOAD_TIMEOUT = 25

DOWNLOAD_RETRIES = 3

RETRY_DELAY = 1.0

MIN_VALID_FILE_SIZE = 500


# =========================================================
# DOWNLOAD LOCK
# =========================================================
#
# يمنع Threadين من تنزيل نفس الآية بنفس اللحظة.
# =========================================================

_download_locks = {}

_download_locks_guard = (
    threading.Lock()
)


# =========================================================
# GET AYAH LOCK
# =========================================================

def get_ayah_lock(
    surah_number,
    ayah_number,
):

    key = (
        int(surah_number),
        int(ayah_number),
    )

    with _download_locks_guard:

        if key not in _download_locks:

            _download_locks[key] = (
                threading.Lock()
            )

        return _download_locks[key]


# =========================================================
# LOCAL SURAH FOLDER
# =========================================================

def get_surah_folder(
    surah_number,
):

    return (
        AUDIO_ROOT
        /
        f"{int(surah_number):03d}"
    )


# =========================================================
# LOCAL AYAH PATH
# =========================================================

def get_local_ayah_path(
    surah_number,
    ayah_number,
):

    return (
        get_surah_folder(
            surah_number
        )
        /
        f"{int(ayah_number):03d}.mp3"
    )


# =========================================================
# EVERYAYAH SOURCE FILE NAME
# =========================================================
#
# مثال:
#
# سورة الملك 67
# آية 1
#
# 067001.mp3
#
# =========================================================

def build_remote_filename(
    surah_number,
    ayah_number,
):

    return (
        f"{int(surah_number):03d}"
        f"{int(ayah_number):03d}"
        ".mp3"
    )


# =========================================================
# BUILD AUDIO URL
# =========================================================

def build_audio_url(
    surah_number,
    ayah_number,
):

    filename = (
        build_remote_filename(
            surah_number,
            ayah_number,
        )
    )

    return (
        f"{EVERYAYAH_BASE_URL}/"
        f"{filename}"
    )


# =========================================================
# CHECK LOCAL FILE
# =========================================================

def is_valid_local_audio(
    path,
):

    try:

        return (
            path.exists()
            and
            path.is_file()
            and
            path.stat().st_size
            >=
            MIN_VALID_FILE_SIZE
        )

    except Exception:

        return False


# =========================================================
# VALIDATE SURAH / AYAH
# =========================================================

def validate_ayah(
    surah_number,
    ayah_number,
):

    try:

        surah_number = int(
            surah_number
        )

        ayah_number = int(
            ayah_number
        )

    except Exception:

        return {
            "valid":
                False,

            "error":
                "invalid_number",
        }

    if (
        surah_number < 1
        or
        surah_number > 114
    ):

        return {
            "valid":
                False,

            "error":
                "invalid_surah_number",
        }

    try:

        surah = (
            get_surah(
                surah_number
            )
        )

    except Exception as error:

        print()
        print(
            "⚠️ Quran catalog database error:"
        )

        print(
            error
        )

        return {
            "valid":
                False,

            "error":
                "database_error",
        }

    if surah is None:

        return {
            "valid":
                False,

            "error":
                "surah_not_found",
        }

    ayah_count = int(
        surah.get(
            "ayah_count",
            0,
        )
        or 0
    )

    if (
        ayah_number < 1
        or
        ayah_number > ayah_count
    ):

        return {
            "valid":
                False,

            "error":
                "invalid_ayah_number",

            "surah":
                surah,

            "ayah_count":
                ayah_count,
        }

    return {
        "valid":
            True,

        "surah":
            surah,

        "ayah_count":
            ayah_count,

        "surah_number":
            surah_number,

        "ayah_number":
            ayah_number,
    }


# =========================================================
# DOWNLOAD AYAH
# =========================================================

def download_ayah(
    surah_number,
    ayah_number,
):

    local_path = (
        get_local_ayah_path(
            surah_number,
            ayah_number,
        )
    )

    # -----------------------------------------------------
    # Already cached
    # -----------------------------------------------------

    if is_valid_local_audio(
        local_path
    ):

        return {
            "success":
                True,

            "downloaded":
                False,

            "cached":
                True,

            "path":
                local_path,
        }

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    url = build_audio_url(
        surah_number,
        ayah_number,
    )

    temp_path = (
        local_path.with_suffix(
            ".part"
        )
    )

    for attempt in range(
        1,
        DOWNLOAD_RETRIES + 1,
    ):

        try:

            print()
            print(
                f"🌐 Downloading Quran audio..."
            )

            print(
                f"📖 Surah "
                f"{int(surah_number)} "
                f"- Ayah "
                f"{int(ayah_number)}"
            )

            request = (
                urllib.request.Request(
                    url,

                    headers={
                        "User-Agent":
                            "MimiBot/1.0"
                    },
                )
            )

            with urllib.request.urlopen(
                request,
                timeout=
                    DOWNLOAD_TIMEOUT,
            ) as response:

                with temp_path.open(
                    "wb"
                ) as output_file:

                    while True:

                        chunk = (
                            response.read(
                                64 * 1024
                            )
                        )

                        if not chunk:

                            break

                        output_file.write(
                            chunk
                        )

            if (
                not temp_path.exists()
                or
                temp_path.stat().st_size
                <
                MIN_VALID_FILE_SIZE
            ):

                raise RuntimeError(
                    "Downloaded audio "
                    "file is invalid."
                )

            temp_path.replace(
                local_path
            )

            print(
                f"✅ Ayah cached: "
                f"{local_path}"
            )

            return {
                "success":
                    True,

                "downloaded":
                    True,

                "cached":
                    False,

                "path":
                    local_path,

                "url":
                    url,
            }

        except urllib.error.HTTPError as error:

            print()
            print(
                f"❌ Quran HTTP error: "
                f"{error.code}"
            )

            if error.code == 404:

                break

        except urllib.error.URLError as error:

            print()
            print(
                "⚠️ Quran network error:"
            )

            print(
                error
            )

        except Exception as error:

            print()
            print(
                "⚠️ Quran download error:"
            )

            print(
                error
            )

        try:

            temp_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass

        if (
            attempt
            <
            DOWNLOAD_RETRIES
        ):

            time.sleep(
                RETRY_DELAY
            )

    return {
        "success":
            False,

        "downloaded":
            False,

        "cached":
            False,

        "path":
            None,

        "url":
            url,

        "error":
            "download_failed",
    }


# =========================================================
# ENSURE AYAH
# =========================================================
#
# هاي أهم function.
#
# quran_audio_player.py رح يستخدمها.
#
# إذا الآية موجودة:
#   يرجع path فورًا.
#
# إذا مش موجودة:
#   ينزلها ويرجع path.
#
# =========================================================

def ensure_ayah(
    surah_number,
    ayah_number,
):

    validation = (
        validate_ayah(
            surah_number,
            ayah_number,
        )
    )

    if not validation.get(
        "valid",
        False,
    ):

        print()
        print(
            "❌ Invalid Quran request:"
        )

        print(
            validation.get(
                "error"
            )
        )

        return None

    local_path = (
        get_local_ayah_path(
            surah_number,
            ayah_number,
        )
    )

    # -----------------------------------------------------
    # FAST PATH
    # -----------------------------------------------------

    if is_valid_local_audio(
        local_path
    ):

        print(
            f"⚡ Quran cache hit: "
            f"{int(surah_number):03d}/"
            f"{int(ayah_number):03d}.mp3"
        )

        return local_path

    # -----------------------------------------------------
    # PREVENT DUPLICATE DOWNLOAD
    # -----------------------------------------------------

    lock = get_ayah_lock(
        surah_number,
        ayah_number,
    )

    with lock:

        # Check again after obtaining lock.
        if is_valid_local_audio(
            local_path
        ):

            return local_path

        result = (
            download_ayah(
                surah_number,
                ayah_number,
            )
        )

        if result.get(
            "success",
            False,
        ):

            return result.get(
                "path"
            )

        return None


# =========================================================
# CHECK AYAH CACHED
# =========================================================

def is_ayah_cached(
    surah_number,
    ayah_number,
):

    path = (
        get_local_ayah_path(
            surah_number,
            ayah_number,
        )
    )

    return (
        is_valid_local_audio(
            path
        )
    )


# =========================================================
# SURAH CACHE INFO
# =========================================================

def get_surah_cache_info(
    surah_number,
):

    try:

        surah = (
            get_surah(
                surah_number
            )
        )

    except Exception:

        return None

    if surah is None:

        return None

    ayah_count = int(
        surah.get(
            "ayah_count",
            0,
        )
        or 0
    )

    cached = []

    missing = []

    for ayah_number in range(
        1,
        ayah_count + 1,
    ):

        if is_ayah_cached(
            surah_number,
            ayah_number,
        ):

            cached.append(
                ayah_number
            )

        else:

            missing.append(
                ayah_number
            )

    return {
        "surah_number":
            surah_number,

        "surah_name":
            surah.get(
                "name"
            ),

        "ayah_count":
            ayah_count,

        "cached_count":
            len(
                cached
            ),

        "missing_count":
            len(
                missing
            ),

        "complete":
            len(
                missing
            )
            == 0,

        "cached":
            cached,

        "missing":
            missing,
    }


# =========================================================
# DELETE ONE CACHED AYAH
# =========================================================

def delete_cached_ayah(
    surah_number,
    ayah_number,
):

    path = (
        get_local_ayah_path(
            surah_number,
            ayah_number,
        )
    )

    try:

        if path.exists():

            path.unlink()

            return True

    except Exception as error:

        print(
            "⚠️ Delete cache error:"
        )

        print(
            error
        )

    return False


# =========================================================
# PREFETCH ONE AYAH
# =========================================================
#
# بتنزل الآية الجاية بخلفية مستقلة.
#
# مثال:
# أثناء تشغيل آية 1
# نبدأ تجهيز آية 2.
#
# =========================================================

def prefetch_ayah(
    surah_number,
    ayah_number,
):

    validation = (
        validate_ayah(
            surah_number,
            ayah_number,
        )
    )

    if not validation.get(
        "valid",
        False,
    ):

        return False

    if is_ayah_cached(
        surah_number,
        ayah_number,
    ):

        return True

    def worker():

        try:

            ensure_ayah(
                surah_number,
                ayah_number,
            )

        except Exception as error:

            print()
            print(
                "⚠️ Quran prefetch error:"
            )

            print(
                error
            )

    thread = (
        threading.Thread(
            target=
                worker,

            daemon=
                True,
        )
    )

    thread.start()

    return True


# =========================================================
# PREFETCH NEXT AYAH
# =========================================================

def prefetch_next_ayah(
    surah_number,
    current_ayah,
):

    try:

        surah = (
            get_surah(
                surah_number
            )
        )

    except Exception:

        return False

    if surah is None:

        return False

    ayah_count = int(
        surah.get(
            "ayah_count",
            0,
        )
        or 0
    )

    next_ayah = (
        int(current_ayah)
        +
        1
    )

    if next_ayah > ayah_count:

        return False

    return (
        prefetch_ayah(
            surah_number,
            next_ayah,
        )
    )


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("📖 MIMI QURAN AUDIO CACHE TEST")
    print("=" * 70)

    # =====================================================
    # TEST 1
    # Existing file
    # =====================================================

    print()
    print(
        "TEST 1:"
        " سورة الفلق - آية 1"
    )

    path = ensure_ayah(
        113,
        1,
    )

    print(
        "Result:",
        path,
    )

    # =====================================================
    # TEST 2
    # New Surah
    # =====================================================
    #
    # سورة الملك لم ننزلها سابقًا.
    # هذا الاختبار ينزل آية واحدة فقط.
    # =====================================================

    print()
    print(
        "TEST 2:"
        " سورة الملك - آية 1"
    )

    path = ensure_ayah(
        67,
        1,
    )

    print(
        "Result:",
        path,
    )

    # =====================================================
    # TEST 3
    # Run same Ayah again
    # Must use local cache.
    # =====================================================

    print()
    print(
        "TEST 3:"
        " سورة الملك - آية 1 مرة ثانية"
    )

    start = (
        time.monotonic()
    )

    path = ensure_ayah(
        67,
        1,
    )

    elapsed = (
        time.monotonic()
        -
        start
    )

    print(
        "Result:",
        path,
    )

    print(
        f"Cache lookup time: "
        f"{elapsed:.4f}s"
    )

    # =====================================================
    # CACHE STATUS
    # =====================================================

    print()
    print(
        "CACHE INFO:"
    )

    info = (
        get_surah_cache_info(
            67
        )
    )

    print(
        info
    )

    print()
    print("=" * 70)
