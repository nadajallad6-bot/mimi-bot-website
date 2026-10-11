"""
Mimi Bot - All Devices Integration
Raspberry Pi screen + USB camera + USB microphone + USB speaker

Features
--------
1. Full-screen Mimi face on the Raspberry Pi screen.
2. Lightweight strict face recognition using OpenCV YuNet + SFace.
3. Greets Sara automatically with audio/welcome_sara.wav.
4. Keeps other faces as Unknown.
5. M key: records the microphone for 4 seconds, then plays it.
6. S key: tests the speaker.
7. R key: forces face recognition.
8. F key: toggles full-screen.
9. Q key: safely exits.

No DeepFace and no TensorFlow.
"""

import glob
import math
import re
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np


# =========================================================
# Project paths
# =========================================================

# mimi_vision.py موجود داخل:
# src/vision/mimi_vision.py
# لذلك parents[2] يرجعنا إلى مجلد mimi-bot
PROJECT_PATH = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_PATH / "faces_db"
MODELS_PATH = PROJECT_PATH / "models"
AUDIO_PATH = PROJECT_PATH / "audio"

YUNET_MODEL = MODELS_PATH / "face_detection_yunet_2023mar.onnx"
SFACE_MODEL = MODELS_PATH / "face_recognition_sface_2021dec.onnx"

GREETING_AUDIO = AUDIO_PATH / "welcome_sara.wav"
MIC_TEST_AUDIO = AUDIO_PATH / "mic_test.wav"

YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_detection_yunet/"
    "face_detection_yunet_2023mar.onnx"
)

SFACE_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_recognition_sface/"
    "face_recognition_sface_2021dec.onnx"
)


# =========================================================
# General settings
# =========================================================

# نخلي OpenCV يستخدم Thread واحد فقط
# حتى يكون أخف على Raspberry Pi
cv2.setNumThreads(1)

WINDOW_NAME = "Mimi Bot"

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 8

DETECTION_SCORE_THRESHOLD = 0.65
RECOGNITION_INTERVAL_SECONDS = 2.0

MAX_IMAGES_PER_PERSON = 6

# =========================================================
# Speaker settings
# =========================================================

# مستوى صوت السماعة
SPEAKER_VOLUME = "100%"

# =========================================================
# Strict recognition rules
# =========================================================

MIN_BEST_SCORE = 0.50
MIN_TOP_AVERAGE_SCORE = 0.45
MIN_MATCHING_PHOTOS = 2
PHOTO_VOTE_THRESHOLD = 0.40
TOP_SCORES_COUNT = 3

GREETING_COOLDOWN_SECONDS = 30.0
MIC_RECORD_SECONDS = 4

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

DISPLAY_NAME_MAP = {
    "saraf": "Sara",
    "sara": "Sara",
    "سارة": "Sara",
}


# =========================================================
# Shared application state
# =========================================================

state_lock = threading.Lock()
audio_lock = threading.Lock()

app_state = {
    "status": "Starting Mimi Bot...",
    "expression": "neutral",
    "microphone": "Searching...",
    "speaker": "Searching...",
}


def set_state(status=None, expression=None):
    with state_lock:
        if status is not None:
            app_state["status"] = status

        if expression is not None:
            app_state["expression"] = expression

    if status:
        print("STATUS:", status)


def get_state():
    with state_lock:
        return dict(app_state)


# =========================================================
# Models
# =========================================================

def download_if_missing(url, destination):
    if destination.exists() and destination.stat().st_size > 10_000:
        return

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part"
    )

    print(f"Downloading {destination.name}...")

    try:
        urllib.request.urlretrieve(
            url,
            temporary,
        )

        temporary.replace(destination)

    except Exception:
        temporary.unlink(
            missing_ok=True,
        )
        raise

    print(f"Saved: {destination}")


def create_detector():
    if hasattr(cv2, "FaceDetectorYN_create"):
        return cv2.FaceDetectorYN_create(
            str(YUNET_MODEL),
            "",
            (FRAME_WIDTH, FRAME_HEIGHT),
            DETECTION_SCORE_THRESHOLD,
            0.3,
            5000,
        )

    return cv2.FaceDetectorYN.create(
        str(YUNET_MODEL),
        "",
        (FRAME_WIDTH, FRAME_HEIGHT),
        DETECTION_SCORE_THRESHOLD,
        0.3,
        5000,
    )


def create_recognizer():
    if hasattr(cv2, "FaceRecognizerSF_create"):
        return cv2.FaceRecognizerSF_create(
            str(SFACE_MODEL),
            "",
        )

    return cv2.FaceRecognizerSF.create(
        str(SFACE_MODEL),
        "",
    )


# =========================================================
# Face database
# =========================================================

def read_image(path):
    try:
        data = np.fromfile(
            str(path),
            dtype=np.uint8,
        )

        return cv2.imdecode(
            data,
            cv2.IMREAD_COLOR,
        )

    except Exception:
        return None


def detect_largest_face(detector, image):
    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    return max(
        faces,
        key=lambda face:
        float(face[2]) * float(face[3]),
    )


def extract_feature(
    recognizer,
    image,
    face,
):
    aligned = recognizer.alignCrop(
        image,
        face,
    )

    return recognizer.feature(
        aligned
    )


def load_database(
    detector,
    recognizer,
):
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Face database folder not found: "
            f"{DATABASE_PATH}"
        )

    database = {}

    folders = sorted(
        folder
        for folder in DATABASE_PATH.iterdir()
        if folder.is_dir()
    )

    print("Loading registered faces...")

    for folder in folders:
        loaded = 0

        image_paths = sorted(
            path
            for path in folder.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in IMAGE_EXTENSIONS
            )
        )

        for image_path in image_paths:

            if loaded >= MAX_IMAGES_PER_PERSON:
                break

            image = read_image(
                image_path
            )

            if image is None:
                print(
                    f"Skipped unreadable image: "
                    f"{image_path}"
                )
                continue

            face = detect_largest_face(
                detector,
                image,
            )

            if face is None:
                print(
                    f"No clear face, skipped: "
                    f"{image_path}"
                )
                continue

            feature = extract_feature(
                recognizer,
                image,
                face,
            )

            if feature is None:
                continue

            database.setdefault(
                folder.name,
                [],
            ).append(feature)

            loaded += 1

            print(
                f"Loaded: "
                f"{folder.name}/"
                f"{image_path.name}"
            )

    count = sum(
        len(features)
        for features in database.values()
    )

    if count == 0:
        raise RuntimeError(
            "No usable registered face "
            "photos were loaded."
        )

    print(
        f"Database ready: "
        f"{len(database)} people, "
        f"{count} photos."
    )

    return database


def recognize_face_strict(
    recognizer,
    query_feature,
    database,
):
    best_person = "Unknown"
    best_average = -1.0
    best_single = -1.0
    best_votes = 0

    for (
        person_name,
        saved_features,
    ) in database.items():

        scores = []

        for saved_feature in saved_features:

            score = float(
                recognizer.match(
                    query_feature,
                    saved_feature,
                    cv2.FaceRecognizerSF_FR_COSINE,
                )
            )

            scores.append(score)

        if not scores:
            continue

        scores.sort(
            reverse=True
        )

        top_scores = scores[
            : min(
                TOP_SCORES_COUNT,
                len(scores),
            )
        ]

        average_score = (
            sum(top_scores)
            / len(top_scores)
        )

        single_score = scores[0]

        votes = sum(
            score >= PHOTO_VOTE_THRESHOLD
            for score in scores
        )

        print(
            f"Candidate {person_name}: "
            f"best={single_score:.3f}, "
            f"avg={average_score:.3f}, "
            f"votes={votes}/{len(scores)}"
        )

        if average_score > best_average:
            best_person = person_name
            best_average = average_score
            best_single = single_score
            best_votes = votes

    accepted = (
        best_single >= MIN_BEST_SCORE
        and
        best_average >= MIN_TOP_AVERAGE_SCORE
        and
        best_votes >= MIN_MATCHING_PHOTOS
    )

    if not accepted:
        best_person = "Unknown"

    return (
        best_person,
        best_single,
        best_average,
        best_votes,
    )


def display_name(database_name):
    key = database_name.strip().lower()

    return DISPLAY_NAME_MAP.get(
        key,
        database_name,
    )


# =========================================================
# Camera auto-detection
# =========================================================

def camera_candidates():
    candidates = []

    # USB stable symlink
    for link in sorted(
        glob.glob(
            "/dev/v4l/by-id/*video-index0"
        )
    ):
        try:
            resolved = str(
                Path(link).resolve()
            )

            if resolved not in candidates:
                candidates.append(
                    resolved
                )

        except OSError:
            pass

    # v4l2 USB camera detection
    try:
        result = subprocess.run(
            [
                "v4l2-ctl",
                "--list-devices",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        current_is_usb = False

        for raw_line in (
            result.stdout.splitlines()
        ):
            line = raw_line.strip()

            if not line:
                continue

            if not raw_line.startswith(
                (" ", "\t")
            ):
                lowered = line.lower()

                current_is_usb = any(
                    word in lowered
                    for word in (
                        "logitech",
                        "uvc",
                        "usb camera",
                        "usb video",
                    )
                )

                continue

            if (
                current_is_usb
                and line.startswith(
                    "/dev/video"
                )
            ):
                if line not in candidates:
                    candidates.append(
                        line
                    )

    except FileNotFoundError:
        pass

    # Fallback
    for index in range(10):
        device = (
            f"/dev/video{index}"
        )

        if (
            Path(device).exists()
            and device not in candidates
        ):
            candidates.append(
                device
            )

    return candidates


def open_camera():
    candidates = camera_candidates()

    print(
        "Camera candidates:",
        candidates,
    )

    for device in candidates:

        camera = cv2.VideoCapture(
            device,
            cv2.CAP_V4L2,
        )

        if not camera.isOpened():
            camera.release()
            continue

        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH,
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT,
        )

        camera.set(
            cv2.CAP_PROP_FPS,
            FRAME_RATE,
        )

        camera.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )

        valid_frame = None

        for _ in range(12):
            success, frame = (
                camera.read()
            )

            if (
                success
                and frame is not None
            ):
                valid_frame = frame
                break

            time.sleep(0.08)

        if valid_frame is not None:
            print(
                f"Camera opened: "
                f"{device}"
            )

            return (
                camera,
                device,
            )

        camera.release()

    raise RuntimeError(
        "USB camera was not found. "
        "Check lsusb and "
        "v4l2-ctl --list-devices."
    )


# =========================================================
# Audio auto-detection
# =========================================================

def find_alsa_device(
    command,
    preferred_words,
):
    try:
        result = subprocess.run(
            [
                command,
                "-l",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    lines = result.stdout.splitlines()

    for preferred_word in preferred_words:

        for line in lines:

            if (
                preferred_word.lower()
                not in line.lower()
            ):
                continue

            match = re.search(
                r"card\s+(\d+):"
                r".*device\s+(\d+):",
                line,
            )

            if match:
                return (
                    f"plughw:"
                    f"{match.group(1)},"
                    f"{match.group(2)}"
                )

    # fallback لأول USB device
    for line in lines:

        if "USB" not in line.upper():
            continue

        match = re.search(
            r"card\s+(\d+):"
            r".*device\s+(\d+):",
            line,
        )

        if match:
            return (
                f"plughw:"
                f"{match.group(1)},"
                f"{match.group(2)}"
            )

    return None


def detect_audio_devices():

    microphone = find_alsa_device(
        "arecord",
        (
            "USB PnP",
            "USB Audio",
            "Microphone",
        ),
    )

    # السماعة الجديدة عندك:
    # UACDemoV1.0 / UACDemoV10
    speaker = find_alsa_device(
        "aplay",
        (
            "UACDemoV1.0",
            "UACDemoV10",
            "Device_1",
            "USB Audio Device",
            "USB Audio",
        ),
    )

    with state_lock:

        app_state["microphone"] = (
            microphone
            or "Not found"
        )

        app_state["speaker"] = (
            speaker
            or "Not found"
        )

    print(
        "Microphone:",
        microphone or "not found",
    )

    print(
        "Speaker:",
        speaker or "not found",
    )

    return (
        microphone,
        speaker,
    )


# =========================================================
# Speaker volume
# =========================================================

def set_speaker_volume(
    speaker_device,
):
    """
    ضبط مستوى صوت السماعة قبل التشغيل.
    مثال speaker_device:
    plughw:2,0
    """

    if not speaker_device:
        return False

    match = re.search(
        r"plughw:(\d+),",
        speaker_device,
    )

    if not match:
        print(
            "Could not determine "
            "speaker card number."
        )
        return False

    card_number = match.group(1)

    # نجلب أسماء mixer controls
    controls_result = subprocess.run(
        [
            "amixer",
            "-c",
            card_number,
            "scontrols",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    controls_text = (
        controls_result.stdout
    )

    # نجرب أشهر أسماء الصوت
    possible_controls = (
        "PCM",
        "Speaker",
        "Master",
        "Playback",
    )

    for control in possible_controls:

        if (
            f"'{control}'"
            not in controls_text
        ):
            continue

        result = subprocess.run(
            [
                "amixer",
                "-c",
                card_number,
                "sset",
                control,
                SPEAKER_VOLUME,
                "unmute",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode == 0:
            print(
                f"Speaker volume: "
                f"{SPEAKER_VOLUME}"
            )
            return True

    print(
        "Speaker has no ALSA "
        "software volume control. "
        "Using current hardware volume."
    )

    return False


def play_audio_file(
    path,
    speaker_device,
):
    if not speaker_device:

        set_state(
            "USB speaker was not found",
            "sad",
        )

        return False

    if not path.exists():

        set_state(
            f"Missing audio file: "
            f"{path.name}",
            "sad",
        )

        return False

    # =====================================================
    # هنا نرفع الصوت قبل تشغيل أي ملف
    # =====================================================

    set_speaker_volume(
        speaker_device
    )

    # تشغيل الصوت
    result = subprocess.run(
        [
            "aplay",
            "-q",
            "-D",
            speaker_device,
            str(path),
        ],
        check=False,
    )

    return (
        result.returncode == 0
    )


# =========================================================
# Greeting
# =========================================================

def greeting_worker(
    speaker_device,
):
    if not audio_lock.acquire(
        blocking=False
    ):
        return

    try:
        set_state(
            "Hello Sara! Nice to see you.",
            "happy",
        )

        worked = play_audio_file(
            GREETING_AUDIO,
            speaker_device,
        )

        if not worked:

            set_state(
                "Greeting audio "
                "could not play",
                "sad",
            )

            time.sleep(2)

    finally:
        audio_lock.release()


# =========================================================
# Speaker test
# =========================================================

def speaker_test_worker():

    if not audio_lock.acquire(
        blocking=False
    ):
        set_state(
            "Audio is busy",
            "neutral",
        )
        return

    try:
        (
            _,
            speaker_device,
        ) = detect_audio_devices()

        test_file = Path(
            "/usr/share/sounds/"
            "alsa/Front_Center.wav"
        )

        if test_file.exists():

            set_state(
                "Testing speaker...",
                "talking",
            )

            worked = play_audio_file(
                test_file,
                speaker_device,
            )

        else:

            set_state(
                "Testing greeting audio...",
                "talking",
            )

            worked = play_audio_file(
                GREETING_AUDIO,
                speaker_device,
            )

        if worked:

            set_state(
                "Speaker works",
                "happy",
            )

        else:

            set_state(
                "Speaker test failed",
                "sad",
            )

        time.sleep(1.5)

    finally:
        audio_lock.release()


# =========================================================
# Microphone test
# =========================================================

def microphone_test_worker():

    if not audio_lock.acquire(
        blocking=False
    ):
        set_state(
            "Audio is busy",
            "neutral",
        )
        return

    try:
        (
            microphone_device,
            speaker_device,
        ) = detect_audio_devices()

        if not microphone_device:

            set_state(
                "USB microphone "
                "was not found",
                "sad",
            )
            return

        if not speaker_device:

            set_state(
                "USB speaker "
                "was not found",
                "sad",
            )
            return

        AUDIO_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        set_state(
            f"Listening for "
            f"{MIC_RECORD_SECONDS} seconds...",
            "listening",
        )

        record_result = subprocess.run(
            [
                "arecord",
                "-q",
                "-D",
                microphone_device,
                "-f",
                "S16_LE",
                "-r",
                "16000",
                "-c",
                "1",
                "-d",
                str(
                    MIC_RECORD_SECONDS
                ),
                str(
                    MIC_TEST_AUDIO
                ),
            ],
            check=False,
        )

        if (
            record_result.returncode
            != 0
        ):

            set_state(
                "Microphone "
                "recording failed",
                "sad",
            )

            return

        set_state(
            "Playing your "
            "recorded voice...",
            "talking",
        )

        worked = play_audio_file(
            MIC_TEST_AUDIO,
            speaker_device,
        )

        if worked:

            set_state(
                "Camera, mic, speaker "
                "and screen work",
                "happy",
            )

        else:

            set_state(
                "Recording worked, "
                "playback failed",
                "sad",
            )

        time.sleep(2)

    finally:
        audio_lock.release()


# =========================================================
# Screen drawing
# =========================================================

def draw_mimi_face(
    canvas,
    expression,
    blink_phase,
):
    height, width = (
        canvas.shape[:2]
    )

    center_x = int(
        width * 0.37
    )

    center_y = int(
        height * 0.50
    )

    face_radius = int(
        min(
            width,
            height,
        ) * 0.23
    )

    # Head
    cv2.circle(
        canvas,
        (
            center_x,
            center_y,
        ),
        face_radius,
        (
            235,
            225,
            255,
        ),
        -1,
        cv2.LINE_AA,
    )

    cv2.circle(
        canvas,
        (
            center_x,
            center_y,
        ),
        face_radius,
        (
            160,
            115,
            220,
        ),
        8,
        cv2.LINE_AA,
    )

    eye_y = (
        center_y
        - int(
            face_radius * 0.25
        )
    )

    eye_dx = int(
        face_radius * 0.38
    )

    eye_w = int(
        face_radius * 0.20
    )

    eye_h = int(
        face_radius * 0.28
    )

    eyes_closed = (
        blink_phase < 0.08
    )

    if expression == "listening":
        eye_h = int(
            face_radius * 0.34
        )

    for eye_x in (
        center_x - eye_dx,
        center_x + eye_dx,
    ):

        if eyes_closed:

            cv2.line(
                canvas,
                (
                    eye_x - eye_w,
                    eye_y,
                ),
                (
                    eye_x + eye_w,
                    eye_y,
                ),
                (
                    45,
                    25,
                    70,
                ),
                7,
                cv2.LINE_AA,
            )

        else:

            cv2.ellipse(
                canvas,
                (
                    eye_x,
                    eye_y,
                ),
                (
                    eye_w,
                    eye_h,
                ),
                0,
                0,
                360,
                (
                    255,
                    255,
                    255,
                ),
                -1,
                cv2.LINE_AA,
            )

            pupil_shift = 0

            if (
                expression
                == "listening"
            ):
                pupil_shift = -3

            cv2.circle(
                canvas,
                (
                    eye_x,
                    eye_y
                    + pupil_shift,
                ),
                max(
                    8,
                    int(
                        eye_w
                        * 0.45
                    ),
                ),
                (
                    45,
                    25,
                    70,
                ),
                -1,
                cv2.LINE_AA,
            )

            cv2.circle(
                canvas,
                (
                    eye_x
                    - max(
                        2,
                        eye_w // 5,
                    ),
                    eye_y
                    - max(
                        2,
                        eye_h // 4,
                    ),
                ),
                max(
                    3,
                    eye_w // 6,
                ),
                (
                    255,
                    255,
                    255,
                ),
                -1,
                cv2.LINE_AA,
            )

    mouth_y = (
        center_y
        + int(
            face_radius * 0.35
        )
    )

    if expression == "happy":

        cv2.ellipse(
            canvas,
            (
                center_x,
                mouth_y - 10,
            ),
            (
                int(
                    face_radius
                    * 0.34
                ),
                int(
                    face_radius
                    * 0.24
                ),
            ),
            0,
            10,
            170,
            (
                80,
                40,
                100,
            ),
            8,
            cv2.LINE_AA,
        )

    elif expression == "sad":

        cv2.ellipse(
            canvas,
            (
                center_x,
                mouth_y + 35,
            ),
            (
                int(
                    face_radius
                    * 0.30
                ),
                int(
                    face_radius
                    * 0.18
                ),
            ),
            0,
            190,
            350,
            (
                80,
                40,
                100,
            ),
            8,
            cv2.LINE_AA,
        )

    elif expression == "talking":

        mouth_height = int(
            face_radius
            * (
                0.13
                + 0.08
                * abs(
                    math.sin(
                        time.time()
                        * 8
                    )
                )
            )
        )

        cv2.ellipse(
            canvas,
            (
                center_x,
                mouth_y,
            ),
            (
                int(
                    face_radius
                    * 0.22
                ),
                mouth_height,
            ),
            0,
            0,
            360,
            (
                80,
                40,
                100,
            ),
            -1,
            cv2.LINE_AA,
        )

    elif expression == "listening":

        cv2.circle(
            canvas,
            (
                center_x,
                mouth_y,
            ),
            int(
                face_radius
                * 0.12
            ),
            (
                80,
                40,
                100,
            ),
            -1,
            cv2.LINE_AA,
        )

    else:

        cv2.line(
            canvas,
            (
                center_x
                - int(
                    face_radius
                    * 0.25
                ),
                mouth_y,
            ),
            (
                center_x
                + int(
                    face_radius
                    * 0.25
                ),
                mouth_y,
            ),
            (
                80,
                40,
                100,
            ),
            7,
            cv2.LINE_AA,
        )


def fit_preview(
    frame,
    target_width,
    target_height,
):
    if frame is None:

        return np.zeros(
            (
                target_height,
                target_width,
                3,
            ),
            dtype=np.uint8,
        )

    return cv2.resize(
        frame,
        (
            target_width,
            target_height,
        ),
        interpolation=cv2.INTER_AREA,
    )


def draw_camera_overlay(
    frame,
    face,
    name,
    best_score,
    average_score,
    votes,
):
    shown = frame.copy()

    if face is None:

        cv2.putText(
            shown,
            "No face",
            (
                15,
                35,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (
                0,
                0,
                255,
            ),
            2,
            cv2.LINE_AA,
        )

        return shown

    (
        x,
        y,
        width,
        height,
    ) = face[:4].astype(int)

    if name == "Unknown":

        color = (
            0,
            0,
            255,
        )

        label = "Unknown"

    else:

        color = (
            0,
            255,
            0,
        )

        label = display_name(
            name
        )

    cv2.rectangle(
        shown,
        (
            x,
            y,
        ),
        (
            x + width,
            y + height,
        ),
        color,
        3,
    )

    cv2.putText(
        shown,
        label,
        (
            x,
            max(
                28,
                y - 10,
            ),
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        color,
        2,
        cv2.LINE_AA,
    )

    details = (
        f"{best_score:.2f} "
        f"avg "
        f"{average_score:.2f} "
        f"v{votes}"
    )

    cv2.putText(
        shown,
        details,
        (
            10,
            shown.shape[0] - 12,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
        cv2.LINE_AA,
    )

    return shown


def build_screen(
    camera_frame,
    face,
    name,
    best_score,
    average_score,
    votes,
):
    screen_width = 1280
    screen_height = 720

    canvas = np.zeros(
        (
            screen_height,
            screen_width,
            3,
        ),
        dtype=np.uint8,
    )

    canvas[:] = (
        28,
        18,
        48,
    )

    state = get_state()

    expression = (
        state["expression"]
    )

    status = (
        state["status"]
    )

    blink_phase = (
        time.time() % 4.0
    )

    draw_mimi_face(
        canvas,
        expression,
        blink_phase,
    )

    preview_width = 430
    preview_height = 323

    preview_x = (
        screen_width
        - preview_width
        - 35
    )

    preview_y = 55

    overlay = draw_camera_overlay(
        camera_frame,
        face,
        name,
        best_score,
        average_score,
        votes,
    )

    preview = fit_preview(
        overlay,
        preview_width,
        preview_height,
    )

    canvas[
        preview_y:
        preview_y + preview_height,
        preview_x:
        preview_x + preview_width,
    ] = preview

    cv2.rectangle(
        canvas,
        (
            preview_x - 4,
            preview_y - 4,
        ),
        (
            preview_x
            + preview_width
            + 4,
            preview_y
            + preview_height
            + 4,
        ),
        (
            190,
            140,
            245,
        ),
        4,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        "CAMERA",
        (
            preview_x,
            preview_y - 15,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (
            235,
            225,
            255,
        ),
        2,
        cv2.LINE_AA,
    )

    # Status panel
    cv2.rectangle(
        canvas,
        (
            40,
            screen_height - 150,
        ),
        (
            screen_width - 40,
            screen_height - 35,
        ),
        (
            48,
            34,
            72,
        ),
        -1,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        status,
        (
            65,
            screen_height - 105,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (
            255,
            255,
            255,
        ),
        2,
        cv2.LINE_AA,
    )

    devices_line = (
        f"Mic: "
        f"{state['microphone']}    "
        f"Speaker: "
        f"{state['speaker']}"
    )

    cv2.putText(
        canvas,
        devices_line,
        (
            65,
            screen_height - 70,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (
            205,
            195,
            225,
        ),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        (
            "M: mic test   "
            "S: speaker   "
            "R: recognize   "
            "F: fullscreen   "
            "Q: exit"
        ),
        (
            preview_x,
            430,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (
            220,
            210,
            240,
        ),
        1,
        cv2.LINE_AA,
    )

    return canvas


# =========================================================
# Main
# =========================================================

def main():
    print(
        "=" * 55
    )

    print(
        "Mimi Bot - "
        "all devices integration"
    )

    print(
        "=" * 55
    )

    AUDIO_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    download_if_missing(
        YUNET_URL,
        YUNET_MODEL,
    )

    download_if_missing(
        SFACE_URL,
        SFACE_MODEL,
    )

    detector = create_detector()

    recognizer = (
        create_recognizer()
    )

    database = load_database(
        detector,
        recognizer,
    )

    (
        microphone_device,
        speaker_device,
    ) = detect_audio_devices()

    # نضبط صوت السماعة من البداية
    if speaker_device:
        set_speaker_volume(
            speaker_device
        )

    (
        camera,
        camera_device,
    ) = open_camera()

    set_state(
        f"Ready - camera "
        f"{camera_device}",
        "neutral",
    )

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL,
    )

    cv2.setWindowProperty(
        WINDOW_NAME,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN,
    )

    is_fullscreen = True

    current_name = "Unknown"
    current_best_score = -1.0
    current_average_score = -1.0
    current_votes = 0

    last_recognition_time = 0.0

    last_greeting_time = (
        -GREETING_COOLDOWN_SECONDS
    )

    greeted_for_current_presence = False

    print(
        "Q exit | "
        "M mic | "
        "S speaker | "
        "R recognize | "
        "F fullscreen"
    )

    try:
        while True:

            success, frame = (
                camera.read()
            )

            if (
                not success
                or frame is None
            ):

                set_state(
                    "Camera frame "
                    "was lost",
                    "sad",
                )

                time.sleep(0.1)

                continue

            frame = cv2.flip(
                frame,
                1,
            )

            face = detect_largest_face(
                detector,
                frame,
            )

            if face is None:

                current_name = "Unknown"
                current_best_score = -1.0
                current_average_score = -1.0
                current_votes = 0

                greeted_for_current_presence = False

                if not audio_lock.locked():

                    set_state(
                        "Waiting for a face...",
                        "neutral",
                    )

            else:

                now = time.monotonic()

                if (
                    now
                    - last_recognition_time
                    >=
                    RECOGNITION_INTERVAL_SECONDS
                ):

                    feature = extract_feature(
                        recognizer,
                        frame,
                        face,
                    )

                    if feature is not None:

                        (
                            current_name,
                            current_best_score,
                            current_average_score,
                            current_votes,
                        ) = recognize_face_strict(
                            recognizer,
                            feature,
                            database,
                        )

                        print(
                            f"FINAL: "
                            f"{current_name} | "
                            f"best="
                            f"{current_best_score:.3f} | "
                            f"avg="
                            f"{current_average_score:.3f} | "
                            f"votes="
                            f"{current_votes}"
                        )

                        is_sara = (
                            current_name
                            != "Unknown"
                            and
                            display_name(
                                current_name
                            )
                            == "Sara"
                        )

                        if is_sara:

                            if not audio_lock.locked():

                                set_state(
                                    "I know you: Sara",
                                    "happy",
                                )

                            can_greet = (
                                not
                                greeted_for_current_presence
                                and
                                (
                                    now
                                    - last_greeting_time
                                    >=
                                    GREETING_COOLDOWN_SECONDS
                                )
                            )

                            if can_greet:

                                (
                                    microphone_device,
                                    speaker_device,
                                ) = detect_audio_devices()

                                threading.Thread(
                                    target=greeting_worker,
                                    args=(
                                        speaker_device,
                                    ),
                                    daemon=True,
                                ).start()

                                last_greeting_time = now

                                greeted_for_current_presence = True

                        else:

                            greeted_for_current_presence = False

                            if not audio_lock.locked():

                                set_state(
                                    "Unknown person",
                                    "neutral",
                                )

                    last_recognition_time = now

            screen = build_screen(
                frame,
                face,
                current_name,
                current_best_score,
                current_average_score,
                current_votes,
            )

            cv2.imshow(
                WINDOW_NAME,
                screen,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key == ord("q"):
                break

            if key == ord("r"):

                last_recognition_time = 0.0

                set_state(
                    "Recognizing now...",
                    "listening",
                )

            if key == ord("s"):

                threading.Thread(
                    target=speaker_test_worker,
                    daemon=True,
                ).start()

            if key == ord("m"):

                threading.Thread(
                    target=microphone_test_worker,
                    daemon=True,
                ).start()

            if key == ord("f"):

                is_fullscreen = (
                    not is_fullscreen
                )

                cv2.setWindowProperty(
                    WINDOW_NAME,
                    cv2.WND_PROP_FULLSCREEN,
                    (
                        cv2.WINDOW_FULLSCREEN
                        if is_fullscreen
                        else
                        cv2.WINDOW_NORMAL
                    ),
                )

            time.sleep(0.02)

    except KeyboardInterrupt:

        print(
            "Stopped by keyboard."
        )

    finally:

        camera.release()

        cv2.destroyAllWindows()

        print(
            "Mimi Bot closed safely."
        )


if __name__ == "__main__":
    main()
