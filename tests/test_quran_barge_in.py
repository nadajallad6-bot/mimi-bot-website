import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.quran_module import QuranModule
from src.modules.voice_module import VoiceModule


def main():

    print()
    print("=" * 60)
    print("📖 QURAN BARGE-IN TEST")
    print("=" * 60)
    print("خلال تلاوة الشيخ جرّبي:")
    print("  وطي الصوت")
    print("  علي الصوت")
    print("  وقف")
    print()
    print(
        "التست يشغّل سورة الملك - الآية 1."
    )
    print("=" * 60)

    voice = VoiceModule()
    quran = None

    try:

        if not voice.start(
            listening=True
        ):
            return

        quran = QuranModule(
            voice_module=voice,
            child_id=None,
            repeat_target=3,
            pass_threshold=85.0,
        )

        quran.start_module()

        quran.quran_stop_requested = False
        quran.last_control_command = None

        success = quran.play_ayah_audio(
            67,
            1,
            resume_after=True,
            prefetch=True,
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
            quran.quran_stop_requested,
        )
        print(
            "last_control_command:",
            quran.last_control_command,
        )
        print(
            "quran_volume:",
            quran.player.volume,
        )
        print("=" * 60)

    except KeyboardInterrupt:
        print()
        print("🛑 Test stopped.")

    finally:

        if quran is not None:
            quran.close()

        voice.close()


if __name__ == "__main__":
    main()
