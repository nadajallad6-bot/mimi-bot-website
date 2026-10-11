import time

import cv2

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
# Vision Module
# =========================================================

class VisionModule:
    """
    Background-only face vision for Mimi Bot.

    Responsibilities:
    - Open the camera.
    - Detect the largest face.
    - Recognize known people.
    - Keep a clean current recognition state.
    - Emit an identity event when a known person appears.

    Important:
    - No OpenCV camera window is created.
    - No cv2.imshow() is used.
    - Unknown people do NOT create identity events.
    - A known person is marked first_seen=True only once per run.
      If the same person leaves and returns later, the event has
      returned=True and first_seen=False.
    """

    def __init__(
        self,
        window_name="Mimi Bot",
        recognition_interval=2.0,
        absence_timeout=2.5,
    ):

        # Kept only for backward compatibility.
        # This module no longer creates an OpenCV window.
        self.window_name = window_name

        self.recognition_interval = max(
            0.1,
            float(recognition_interval),
        )

        self.absence_timeout = max(
            0.5,
            float(absence_timeout),
        )

        # -------------------------------------------------
        # Models
        # -------------------------------------------------

        self.detector = None
        self.recognizer = None
        self.face_database = None

        # -------------------------------------------------
        # Camera
        # -------------------------------------------------

        self.camera = None
        self.camera_device = None

        # -------------------------------------------------
        # Recognition state
        # -------------------------------------------------

        self.last_recognition_time = 0.0
        self.last_face_seen_time = 0.0

        self.recognized_name = "Unknown"
        self.best_score = -1.0
        self.average_score = -1.0
        self.votes = 0

        self.face_present = False

        # Known-person session tracking.
        self.current_present_name = None
        self.seen_known_names = set()
        self._pending_identity_event = None

        self.started = False

    # =====================================================
    # Start
    # =====================================================

    def start(self):
        """
        Prepare models and camera.

        Camera runs in the background only.
        """

        if self.started:
            return True

        print()
        print("=" * 60)
        print("📷 STARTING VISION MODULE")
        print("=" * 60)

        # -------------------------------------------------
        # Download models if missing
        # -------------------------------------------------

        print()
        print(
            "🧠 Checking face recognition models..."
        )

        download_if_missing(
            YUNET_URL,
            YUNET_MODEL,
        )

        download_if_missing(
            SFACE_URL,
            SFACE_MODEL,
        )

        # -------------------------------------------------
        # Create models
        # -------------------------------------------------

        print(
            "🧠 Loading YuNet detector..."
        )

        self.detector = (
            create_detector()
        )

        print(
            "🧠 Loading SFace recognizer..."
        )

        self.recognizer = (
            create_recognizer()
        )

        # -------------------------------------------------
        # Face database
        # -------------------------------------------------

        print()
        print(
            "👤 Loading face database..."
        )

        self.face_database = (
            load_database(
                self.detector,
                self.recognizer,
            )
        )

        # -------------------------------------------------
        # Camera
        # -------------------------------------------------

        print()
        print(
            "📷 Opening camera..."
        )

        (
            self.camera,
            self.camera_device,
        ) = open_camera()

        if self.camera is None:

            print(
                "❌ Vision camera could not be opened."
            )

            self.started = False
            return False

        print(
            f"✅ Camera: {self.camera_device}"
        )

        # IMPORTANT:
        # No cv2.namedWindow() here.
        # Camera frames stay in the background.

        self.started = True

        print()
        print(
            "✅ Vision Module ready in background mode."
        )

        print("=" * 60)

        return True

    # =====================================================
    # Read Frame
    # =====================================================

    def read_frame(self):
        """
        Read one camera frame.

        Returns:
            frame or None
        """

        if (
            not self.started
            or
            self.camera is None
        ):
            return None

        success, frame = (
            self.camera.read()
        )

        if (
            not success
            or frame is None
        ):
            return None

        # Mirror for consistent face alignment behavior.
        frame = cv2.flip(
            frame,
            1,
        )

        return frame

    # =====================================================
    # Detect Face
    # =====================================================

    def detect_face(
        self,
        frame,
    ):
        """
        Detect the largest face.
        """

        if frame is None:
            return None

        return detect_largest_face(
            self.detector,
            frame,
        )

    # =====================================================
    # Known Person Event
    # =====================================================

    def _register_known_presence(
        self,
        name,
    ):

        name = str(
            name or ""
        ).strip()

        if (
            not name
            or
            name == "Unknown"
        ):
            return

        if (
            self.current_present_name
            ==
            name
        ):
            return

        first_seen = (
            name
            not in
            self.seen_known_names
        )

        if first_seen:
            self.seen_known_names.add(
                name
            )

        self.current_present_name = name

        self._pending_identity_event = {
            "name":
                name,
            "known":
                True,
            "first_seen":
                first_seen,
            "returned":
                not first_seen,
            "best_score":
                self.best_score,
            "average_score":
                self.average_score,
            "votes":
                self.votes,
        }

        if first_seen:

            print(
                f"👋 Known person appeared: {name}"
            )

        else:

            print(
                f"↩️ Known person returned: {name}"
            )

    def consume_identity_event(self):
        """
        Return the next known-person event once.

        Unknown people never create an event.

        MimiBot can use:
            first_seen=True  -> greet once
            returned=True    -> resume silently
        """

        event = (
            self._pending_identity_event
        )

        self._pending_identity_event = None

        return event

    # =====================================================
    # Recognize
    # =====================================================

    def recognize(
        self,
        frame,
        face,
        force=False,
    ):
        """
        Recognize a detected face.

        recognition_interval prevents running recognition
        on every video frame.
        """

        if (
            frame is None
            or
            face is None
        ):

            return self.get_result()

        now = time.monotonic()

        if (
            not force
            and
            now - self.last_recognition_time
            <
            self.recognition_interval
        ):

            return self.get_result()

        feature = extract_feature(
            self.recognizer,
            frame,
            face,
        )

        if feature is None:

            self.last_recognition_time = now

            return self.get_result()

        (
            name,
            best_score,
            average_score,
            votes,
        ) = recognize_face_strict(
            self.recognizer,
            feature,
            self.face_database,
        )

        self.recognized_name = (
            str(
                name or "Unknown"
            ).strip()
            or
            "Unknown"
        )

        self.best_score = float(
            best_score
        )

        self.average_score = float(
            average_score
        )

        self.votes = int(
            votes
        )

        self.last_recognition_time = now

        print()
        print("-" * 50)

        print(
            f"👀 Face: "
            f"{self.recognized_name}"
        )

        print(
            f"Best score: "
            f"{self.best_score:.3f}"
        )

        print(
            f"Average score: "
            f"{self.average_score:.3f}"
        )

        print(
            f"Votes: "
            f"{self.votes}"
        )

        print("-" * 50)

        if (
            self.recognized_name
            !=
            "Unknown"
        ):

            self._register_known_presence(
                self.recognized_name
            )

        else:

            # Unknown people are intentionally ignored.
            # Do not generate a greeting/event.
            self.current_present_name = None

        return self.get_result()

    # =====================================================
    # No Face / Absence
    # =====================================================

    def _handle_no_face(self):

        self.face_present = False

        now = time.monotonic()

        if (
            self.last_face_seen_time <= 0.0
        ):
            return

        if (
            now
            -
            self.last_face_seen_time
            <
            self.absence_timeout
        ):
            return

        # Prevent a stale recognized child from remaining
        # active after leaving the camera.
        if (
            self.recognized_name
            !=
            "Unknown"
            or
            self.current_present_name
            is not None
        ):

            print(
                "👤 Face left camera."
            )

        self.recognized_name = "Unknown"
        self.best_score = -1.0
        self.average_score = -1.0
        self.votes = 0

        self.current_present_name = None

    # =====================================================
    # Process Frame
    # =====================================================

    def process(self):
        """
        Backward-compatible process method.

        Returns:
            frame
            face
            recognition_result

        The frame is NOT displayed by this module.
        """

        frame = self.read_frame()

        if frame is None:

            self._handle_no_face()

            return (
                None,
                None,
                self.get_result(),
            )

        face = self.detect_face(
            frame
        )

        if face is not None:

            self.face_present = True
            self.last_face_seen_time = (
                time.monotonic()
            )

            result = self.recognize(
                frame,
                face,
            )

        else:

            self._handle_no_face()

            result = (
                self.get_result()
            )

        return (
            frame,
            face,
            result,
        )

    def poll(self):
        """
        Background-friendly helper for MimiBot.

        Returns only the recognition result.
        """

        _, _, result = self.process()

        return result

    # =====================================================
    # Recognition Result
    # =====================================================

    def get_result(self):
        """
        Return the current clean recognition state.
        """

        known = (
            self.face_present
            and
            self.recognized_name
            !=
            "Unknown"
        )

        return {
            "name":
                self.recognized_name,

            "best_score":
                self.best_score,

            "average_score":
                self.average_score,

            "votes":
                self.votes,

            "known":
                known,

            "present":
                self.face_present,

            "camera_device":
                self.camera_device,
        }

    # =====================================================
    # Reset Recognition
    # =====================================================

    def reset_recognition(
        self,
        clear_seen=False,
    ):

        self.recognized_name = "Unknown"

        self.best_score = -1.0
        self.average_score = -1.0
        self.votes = 0

        self.last_recognition_time = 0.0
        self.last_face_seen_time = 0.0

        self.face_present = False
        self.current_present_name = None
        self._pending_identity_event = None

        if clear_seen:

            self.seen_known_names.clear()

    # =====================================================
    # Optional Debug Drawing
    # =====================================================

    def draw_face(
        self,
        frame,
        face,
        label,
        color=(255, 255, 255),
    ):
        """
        Kept for compatibility/debugging only.

        This function may draw on a frame, but VisionModule
        never displays that frame.
        """

        if (
            frame is None
            or
            face is None
        ):
            return frame

        (
            x,
            y,
            width,
            height,
        ) = face[:4].astype(
            int
        )

        cv2.rectangle(
            frame,
            (
                x,
                y,
            ),
            (
                x + width,
                y + height,
            ),
            color,
            2,
        )

        cv2.putText(
            frame,
            str(label),
            (
                x,
                max(
                    y - 10,
                    25,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            color,
            2,
            cv2.LINE_AA,
        )

        return frame

    def draw_status(
        self,
        frame,
        mode_text="",
        activity_text="",
        points=None,
    ):
        """
        Kept for compatibility/debugging only.
        """

        if frame is None:
            return frame

        if mode_text:

            cv2.putText(
                frame,
                str(mode_text),
                (
                    15,
                    30,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (
                    255,
                    255,
                    255,
                ),
                2,
                cv2.LINE_AA,
            )

        if activity_text:

            cv2.putText(
                frame,
                str(activity_text),
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
                2,
                cv2.LINE_AA,
            )

        if points is not None:

            cv2.putText(
                frame,
                f"Points: {points}",
                (
                    15,
                    90,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (
                    255,
                    255,
                    255,
                ),
                1,
                cv2.LINE_AA,
            )

        return frame

    # =====================================================
    # Show - intentionally disabled
    # =====================================================

    def show(
        self,
        frame,
    ):
        """
        Backward-compatible no-op.

        Camera video must not appear on Mimi's display.
        """

        return -1

    # =====================================================
    # State Helpers
    # =====================================================

    def is_started(self):

        return bool(
            self.started
        )

    def is_known_person_present(self):

        result = self.get_result()

        return bool(
            result["known"]
        )

    def get_current_name(self):

        result = self.get_result()

        if not result["known"]:
            return None

        return result["name"]

    # =====================================================
    # Close
    # =====================================================

    def close(self):

        print()
        print(
            "🧹 Closing Vision Module..."
        )

        if self.camera is not None:

            try:
                self.camera.release()
            except Exception:
                pass

        self.camera = None
        self.camera_device = None

        self.reset_recognition(
            clear_seen=True
        )

        self.started = False

        print(
            "✅ Vision Module closed."
        )


# =========================================================
# Standalone Background Test
# =========================================================

def test_vision_module():

    vision = VisionModule(
        recognition_interval=2.0,
        absence_timeout=2.5,
    )

    try:

        if not vision.start():
            return

        print()
        print("=" * 60)
        print("👀 BACKGROUND VISION TEST")
        print("=" * 60)
        print(
            "No camera window will open."
        )
        print(
            "Stand in front of Mimi and watch the terminal."
        )
        print(
            "Unknown faces are ignored."
        )
        print(
            "Press Ctrl+C to stop."
        )
        print("=" * 60)

        last_status = None

        while True:

            result = vision.poll()

            event = (
                vision.consume_identity_event()
            )

            status = (
                result["present"],
                result["known"],
                result["name"],
            )

            if status != last_status:

                print()
                print(
                    "VISION STATE:",
                    result,
                )

                last_status = status

            if event is not None:

                print()
                print(
                    "IDENTITY EVENT:",
                    event,
                )

            time.sleep(
                0.05
            )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Vision test stopped."
        )

    finally:

        vision.close()


if __name__ == "__main__":

    test_vision_module()