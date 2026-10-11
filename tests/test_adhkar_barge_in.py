import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.adhkar_module import AdhkarModule
from src.modules.voice_module import VoiceModule


def main():

    print()
    print("=" * 60)
    print("🤲 ADHKAR BARGE-IN TEST")
    print("=" * 60)
    print("خلال أذكار الصباح جرّبي:")
    print("  وطي الصوت")
    print("  علي الصوت")
    print("  وقف")
    print("=" * 60)

    voice = VoiceModule()
    adhkar = None

    try:

        if not voice.start(
            listening=True
        ):
            return

        adhkar = AdhkarModule(
            voice_module=voice,
            face_module=None,
        )

        adhkar.start_module()

        adhkar.mode = "morning"

        success = adhkar.play_segment(
            "morning"
        )

        print()
        print("=" * 60)
        print("📌 TEST RESULT")
        print("=" * 60)
        print(
            "audio_ok:",
            success,
        )
        print(
            "stop_requested:",
            adhkar.adhkar_stop_requested,
        )
        print(
            "last_control_command:",
            adhkar.last_control_command,
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
        print(
            "🛑 Test stopped."
        )

    finally:

        if adhkar is not None:
            adhkar.close()

        voice.close()


if __name__ == "__main__":
    main()