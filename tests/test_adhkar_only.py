import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.adhkar_module import AdhkarModule


def main():
    print("\n==============================")
    print("MIMI ADHKAR ONLY - NO SCREEN")
    print("==============================\n")

    voice = VoiceModule()
    voice.start(listening=False)

    adhkar = AdhkarModule(
        voice_module=voice
    )

    adhkar.start_module()

    print("اختاري:")
    print("1 - أذكار الصباح")
    print("2 - أذكار المساء")
    print("3 - أذكار النوم")

    choice = input("\nاختيارك: ").strip()

    mode = {
        "1": "morning",
        "2": "evening",
        "3": "sleep",
    }.get(choice)

    if not mode:
        print("❌ اختيار غير صحيح")
        adhkar.close()
        voice.close()
        return

    print(f"\n🤲 بدء: {mode}\n")

    # AdhkarModule API الصحيح هو start_adhkar(mode)
    # وليس start(...)
    result = adhkar.start_adhkar(mode)

    print("\n📌 Adhkar result:", result)

    print("\n✅ انتهى اختبار الأذكار")

    adhkar.close()
    voice.close()


if __name__ == "__main__":
    main()