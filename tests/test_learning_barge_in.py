import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.learning_module import LearningModule
from src.modules.voice_module import VoiceModule


def main():

    print()
    print("=" * 60)
    print("🎓 LEARNING BARGE-IN TEST")
    print("=" * 60)
    print("خلال درس الألوان جرّبي:")
    print("  وطي الصوت")
    print("  علي الصوت")
    print("  وقف")
    print("=" * 60)

    voice = VoiceModule()
    learning = None

    try:

        if not voice.start(
            listening=True
        ):
            return

        learning = LearningModule(
            voice_module=voice
        )

        learning.start_module()

        ok = learning.play_lesson_audio(
            "colors"
        )

        print()
        print("=" * 60)
        print("📌 TEST RESULT")
        print("=" * 60)
        print(
            "audio_ok:",
            ok,
        )
        print(
            "stop_requested:",
            learning.learning_stop_requested,
        )
        print(
            "last_control_command:",
            learning.last_control_command,
        )

        try:
            print(
                "volume:",
                voice.get_volume(),
            )
        except Exception:
            pass

        print("=" * 60)

    except KeyboardInterrupt:
        print()
        print("🛑 Test stopped.")

    finally:

        if learning is not None:
            learning.close()

        voice.close()


if __name__ == "__main__":
    main()