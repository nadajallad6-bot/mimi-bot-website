import os

import cv2


CAMERA_INDEX = 0
WINDOW_NAME = "Mimi Bot Camera"


def run_camera() -> None:
    if not os.environ.get("DISPLAY"):
        raise RuntimeError(
            "No graphical display detected. Run this from the Raspberry Pi desktop or VNC."
        )

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

        print("✅ Camera started")
        print("Press Q or ESC to close")

        while True:
            success, frame = camera.read()

            if not success:
                print("❌ Failed to read a frame")
                break

            # جعل الصورة مثل المرآة
            frame = cv2.flip(frame, 1)

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("✅ Camera closed safely")


if __name__ == "__main__":
    run_camera()
