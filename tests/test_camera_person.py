import cv2
import sys
from pathlib import Path

from src.core.child_session import create_child_session
from src.modules.vision_module import VisionModule


def get_gender_from_session(session):
    if not session:
        return "UNKNOWN"

    child = session.get("child", {})

    gender = str(
        child.get("gender", "")
    ).strip().lower()

    if gender in {
        "girl",
        "female",
        "بنت",
        "انثى",
        "أنثى",
    }:
        return "GIRL"

    if gender in {
        "boy",
        "male",
        "ولد",
        "ذكر",
    }:
        return "BOY"

    return "UNKNOWN"


def main():

    print()
    print("=" * 60)
    print("📷 MIMI BOT - KNOWN / UNKNOWN + GENDER TEST")
    print("=" * 60)

    vision = VisionModule()
    vision.start()

    print()
    print("👀 Looking for people...")
    print("Q = quit")
    print()

    try:
        while True:

            frame = vision.get_frame()

            if frame is None:
                continue

            result = vision.get_latest_recognition()

            label = "UNKNOWN"
            gender = "UNKNOWN"

            if isinstance(result, dict):

                face_id = result.get("face_id")

                if face_id:

                    try:
                        session = create_child_session(
                            face_id
                        )
                    except Exception as error:
                        print(
                            "⚠️ DB error:",
                            error,
                        )
                        session = None

                    if session:

                        child = session.get(
                            "child",
                            {},
                        )

                        name = child.get(
                            "name",
                            face_id,
                        )

                        gender = (
                            get_gender_from_session(
                                session
                            )
                        )

                        label = (
                            f"{name} | {gender}"
                        )

                    else:
                        label = "UNKNOWN"

            cv2.putText(
                frame,
                label,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

            cv2.imshow(
                "Mimi Camera Test",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:

        try:
            vision.close()
        except Exception:
            pass

        cv2.destroyAllWindows()

        print()
        print("🛑 Test finished.")


if __name__ == "__main__":
    main()