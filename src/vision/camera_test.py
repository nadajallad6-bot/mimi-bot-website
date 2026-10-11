from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "camera_test.jpg"


def capture_test_image() -> None:
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

    try:
        if not camera.isOpened():
            raise RuntimeError("Could not open camera /dev/video0")

        camera.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG"),
        )
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)

        frame = None

        # التخلص من أول صور حتى يثبت الضوء والتركيز
        for _ in range(20):
            success, current_frame = camera.read()

            if success:
                frame = current_frame

        if frame is None:
            raise RuntimeError("Camera opened but no frame was received")

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not cv2.imwrite(str(OUTPUT_PATH), frame):
            raise RuntimeError("Could not save camera image")

        height, width = frame.shape[:2]

        print("✅ Camera is working successfully")
        print(f"✅ Captured resolution: {width}x{height}")
        print(f"✅ Image saved at: {OUTPUT_PATH}")

    finally:
        camera.release()


if __name__ == "__main__":
    capture_test_image()
