import cv2


CAMERA_INDEX = 0
WINDOW_NAME = "Mimi Bot Face Detection"


def run_face_detection() -> None:
    face_cascade_path = (
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    face_detector = cv2.CascadeClassifier(face_cascade_path)

    if face_detector.empty():
        raise RuntimeError("Could not load the face detector")

    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)

    try:
        if not camera.isOpened():
            raise RuntimeError("Could not open /dev/video0")

        camera.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG"),
        )
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)

        print("✅ Face detection started")
        print("Press Q or ESC to close")

        while True:
            success, frame = camera.read()

            if not success:
                print("❌ Failed to read camera frame")
                break

            frame = cv2.flip(frame, 1)

            gray_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY,
            )

            faces = face_detector.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
            )

            for x, y, width, height in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2,
                )

            cv2.putText(
                frame,
                f"Faces: {len(faces)}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("✅ Camera closed safely")


if __name__ == "__main__":
    run_face_detection()
