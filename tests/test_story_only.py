import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.story_module import StoryModule


def main():
    print("\n==============================")
    print("MIMI STORY ONLY - AUDIO TEST")
    print("==============================\n")

    voice = VoiceModule()
    voice.start(listening=False)

    print("🔊 أولًا نجرب صوت ميمي نفسه...")
    ok = voice.say(
        "مرحبا! هذا اختبار صوت سؤال القصة.",
        resume_listening=False,
    )
    print("TTS test result:", ok)

    stories = StoryModule(
        voice_module=voice,
        face_module=None,
    )
    stories.start_module()

    print("\nاختاري القصة:")
    print("1 - الحيوانات")
    print("2 - مضحكة")
    print("3 - تعليمية")
    print("4 - مغامرة")

    choice = input("\nاختيارك: ").strip()

    story_text = {
        "1": "قصة حيوانات",
        "2": "قصة مضحكة",
        "3": "قصة تعليمية",
        "4": "قصة مغامرة",
    }.get(choice)

    if not story_text:
        print("❌ اختيار غير صحيح")
        voice.close()
        return

    print("\n▶️ بدء القصة...\n")
    result = stories.start(story_text)

    print("\n📌 Story result:", result)

    while stories.is_active():
        if stories.is_waiting_for_answer():
            answer = input("\n👧 جواب الطفل: ").strip()

            if answer in {"وقف", "خروج", "stop"}:
                stories.reset()
                print("⏹️ تم إيقاف القصة")
                break

            result = stories.answer(answer)
            print("\n📌 Story result:", result)

    stories.close()
    voice.close()
    print("\n✅ انتهى اختبار القصة")


if __name__ == "__main__":
    main()