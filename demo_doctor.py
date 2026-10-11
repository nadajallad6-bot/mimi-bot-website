import time

import cv2

from src.voice.speaker import speak

from src.vision.mimi_vision import (
    YUNET_MODEL,
    YUNET_URL,
    SFACE_MODEL,
    SFACE_URL,
    create_detector,
    create_recognizer,
    detect_largest_face,
    download_if_missing,
    extract_feature,
    load_database,
    open_camera,
    recognize_face_strict,
)


# =========================================================
# Settings
# =========================================================

WINDOW_NAME = "Mimi Bot - Doctor Demo"

RECOGNITION_INTERVAL = 2.0

UNKNOWN_REQUIRED_COUNT = 2

GREETING_COOLDOWN = 15.0


# =========================================================
# Names
# =========================================================

DISPLAY_NAMES = {
    "saraf": "Sara",
    "sara": "Sara",
}


# =========================================================
# Main
# =========================================================

def main():

    print()
    print("=" * 60)
    print("🤖 MIMI BOT - DOCTOR DEMO")
    print("=" * 60)

    # -----------------------------------------------------
    # Load models
    # -----------------------------------------------------

    print("🧠 Loading face models...")

    download_if_missing(
        YUNET_URL,
        YUNET_MODEL,
    )

    download_if_missing(
        SFACE_URL,
        SFACE_MODEL,
    )

    detector = create_detector()

    recognizer = create_recognizer()

    # -----------------------------------------------------
    # Load registered faces
    # -----------------------------------------------------

    print("👤 Loading face database...")

    face_database = load_database(
        detector,
        recognizer,
    )

    # -----------------------------------------------------
    # Camera
    # -----------------------------------------------------

    print("📷 Opening camera...")

    camera, camera_device = open_camera()

    print(
        f"✅ Camera ready: {camera_device}"
    )

    # -----------------------------------------------------
    # Window
    # -----------------------------------------------------

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL,
    )

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    last_recognition_time = 0.0

    last_greeting_time = 0.0

    last_person = None

    unknown_count = 0

    current_label = "Looking..."

    print()
    print("👀 Mimi is looking for someone...")
    print("اضغطي Q للخروج.")
    print()

    try:

        while True:

            success, frame = camera.read()

            if not success or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(
                frame,
                1,
            )

            face = detect_largest_face(
                detector,
                frame,
            )

            now = time.monotonic()

            # =================================================
            # Face detected
            # =================================================

            if face is not None:

                if (
                    now - last_recognition_time
                    >= RECOGNITION_INTERVAL
                ):

                    feature = extract_feature(
                        recognizer,
                        frame,
                        face,
                    )

                    if feature is not None:

                        (
                            recognized_name,
                            best_score,
                            average_score,
                            votes,
                        ) = recognize_face_strict(
                            recognizer,
                            feature,
                            face_database,
                        )

                        print()
                        print(
                            f"👀 Face: {recognized_name}"
                        )

                        print(
                            f"Best score: {best_score:.3f}"
                        )

                        # =====================================
                        # Registered person
                        # =====================================

                        if recognized_name != "Unknown":

                            unknown_count = 0

                            display_name = DISPLAY_NAMES.get(
                                recognized_name.lower(),
                                recognized_name,
                            )

                            current_label = display_name

                            should_greet = (
                                last_person != recognized_name
                                or
                                now - last_greeting_time
                                >= GREETING_COOLDOWN
                            )

                            if should_greet:

                                print()
                                print(
                                    f"✅ Recognized: "
                                    f"{display_name}"
                                )

                                speak(
                                    f"أهلًا {display_name}. "
                                    "أنا ميمي بوت. "
                                    "سعيدة إني شفتك. "
                                    "كيف بقدر أساعدك اليوم؟"
                                )

                                last_person = (
                                    recognized_name
                                )

                                last_greeting_time = now

                        # =====================================
                        # Unknown person
                        # =====================================

                        else:

                            unknown_count += 1

                            current_label = (
                                "Checking..."
                            )

                            print(
                                "👤 Unknown confirmation: "
                                f"{unknown_count}/"
                                f"{UNKNOWN_REQUIRED_COUNT}"
                            )

                            if (
                                unknown_count
                                >= UNKNOWN_REQUIRED_COUNT
                            ):

                                current_label = "Guest"

                                should_greet = (
                                    last_person != "guest"
                                    or
                                    now - last_greeting_time
                                    >= GREETING_COOLDOWN
                                )

                                if should_greet:

                                    print()
                                    print(
                                        "👤 Guest detected"
                                    )

                                    speak(
                                        "مرحبًا. "
                                        "أنا ميمي بوت. "
                                        "سعيدة إني شفتك. "
                                        "ممكن نحكي قصة، "
                                        "أو نحل لغز، "
                                        "أو نتعلم سوا."
                                    )

                                    last_person = "guest"

                                    last_greeting_time = now

                    last_recognition_time = now

                # =================================================
                # Draw face rectangle
                # =================================================

                x, y, width, height = (
                    face[:4].astype(int)
                )

                if current_label == "Guest":

                    color = (
                        0,
                        165,
                        255,
                    )

                elif current_label == "Checking...":

                    color = (
                        0,
                        165,
                        255,
                    )

                else:

                    color = (
                        0,
                        255,
                        0,
                    )

                cv2.rectangle(
                    frame,
                    (x, y),
                    (
                        x + width,
                        y + height,
                    ),
                    color,
                    2,
                )

                cv2.putText(
                    frame,
                    current_label,
                    (
                        x,
                        max(
                            y - 10,
                            25,
                        ),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2,
                    cv2.LINE_AA,
                )

            # =================================================
            # No face
            # =================================================

            else:

                current_label = "Looking..."

                unknown_count = 0

                last_person = None

            # =================================================
            # Mimi title
            # =================================================

            cv2.putText(
                frame,
                "MIMI BOT",
                (
                    15,
                    30,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (
                    255,
                    255,
                    255,
                ),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                current_label,
                (
                    15,
                    60,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (
                    255,
                    255,
                    255,
                ),
                1,
                cv2.LINE_AA,
            )

            # =================================================
            # Show camera
            # =================================================

            cv2.imshow(
                WINDOW_NAME,
                frame,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key in (
                ord("q"),
                27,
            ):
                break

            time.sleep(0.02)

    except KeyboardInterrupt:

        print()
        print("🛑 Demo stopped.")

    finally:

        camera.release()

        cv2.destroyAllWindows()

        print()
        print("✅ Doctor demo closed.")


if __name__ == "__main__":
    main()
