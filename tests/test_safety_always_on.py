import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.safety_module import SafetyModule
from src.modules.voice_module import VoiceModule


def main():

    print()
    print("=" * 60)
    print("🚨 SAFETY ALWAYS-ON TEST")
    print("=" * 60)
    print("هذا التست يفحص:")
    print("1) العبارة العادية ما تعمل Alert")
    print("2) ساعدني تعمل Alert")
    print("3) أنا بخير تلغي Alert")
    print("4) منطق الصوت العالي: 3 hits خلال 4 ثواني")
    print("=" * 60)

    voice = VoiceModule()
    safety = None

    try:

        if not voice.start(
            listening=True
        ):
            return

        safety = SafetyModule(
            voice_module=voice
        )

        safety.start_module()
        safety.set_child(None)

        print()
        print("--- 1) False-positive test ---")
        result = safety.handle_voice(
            "ميمي ساعدني بالواجب"
        )
        print(result)

        print()
        print("--- 2) Emergency phrase test ---")
        result = safety.handle_voice(
            "ميمي ساعدني"
        )
        print(result)

        print()
        print("--- 3) Cancel test ---")
        result = safety.handle_voice(
            "أنا بخير"
        )
        print(result)

        print()
        print("--- 4) Loud confirmation logic ---")
        print("Simulating 3 confirmed loud candidates...")

        result = None

        for index in range(3):

            result = safety.register_loud_sound(
                sound_level=18000.0,
                duration_ms=250,
            )

            print(
                f"hit {index + 1}:",
                result,
            )

            if index < 2:
                time.sleep(0.9)

        print()
        print("FINAL STATE:")
        print(
            safety.get_state()
        )

        if safety.is_active():
            safety.clear_alert(
                reason="test_finished"
            )

        print()
        print("✅ Safety logic test finished.")
        print()
        print(
            "ملاحظة: لاختبار الخبط الحقيقي، لازم src/voice/listener.py "
            "يكون نسخة listener_safety_always_on.py."
        )

    except KeyboardInterrupt:
        print()
        print("🛑 Safety test stopped.")

    finally:

        if safety is not None:
            safety.close()

        voice.close()


if __name__ == "__main__":
    main()