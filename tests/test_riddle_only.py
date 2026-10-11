import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.riddle_module import RiddleModule


class KeyboardTestVoice:
    """
    Wrapper للاختبار فقط:
    يشغّل صوت Mimi، لكن يمنع فتح المايك تلقائيًا بعد كل سؤال/تلميح.
    هيك جواب الطفل بنكتبه من الكيبورد بدون ما الـVoice Listener ينافس input().
    """

    def __init__(self, real_voice):
        self.real_voice = real_voice

    def say(self, text, resume_listening=False):
        return self.real_voice.say(
            text,
            resume_listening=False,
        )


def main():

    print("\n==============================")
    print("MIMI RIDDLE ONLY - KEYBOARD TEST")
    print("==============================\n")

    real_voice = VoiceModule()
    real_voice.start(listening=False)

    test_voice = KeyboardTestVoice(real_voice)

    print("🔊 اختبار صوت ميمي...")

    test_voice.say(
        "يلا نلعب ألغاز!",
        resume_listening=False,
    )

    riddles = RiddleModule(
        voice_module=test_voice
    )

    riddles.start_module()

    print("\n🧩 بدء لعبة الألغاز...\n")

    result = riddles.start()

    print("\n📌 Riddle result:", result)

    while riddles.is_active():

        answer = input(
            "\n👧 اكتبي جواب الطفل: "
        ).strip()

        if answer in {
            "وقف",
            "خروج",
            "stop",
        }:
            riddles.reset()
            print("\n⏹️ تم إيقاف الألغاز")
            break

        result = riddles.answer(answer)

        print(
            "\n📌 Riddle result:",
            result
        )

    print("\n✅ انتهت جولة الألغاز")

    riddles.close()
    real_voice.close()


if __name__ == "__main__":
    main()