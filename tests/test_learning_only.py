import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.learning_module import LearningModule


class KeyboardTestVoice:
    """
    للاختبار فقط:
    Mimi تحكي بصوتها، لكن ما بنخلي المايك يفتح تلقائيًا.
    جواب الطفل بندخله من الكيبورد.
    """

    def __init__(self, real_voice):
        self.real_voice = real_voice

    def say(self, text, resume_listening=False):
        return self.real_voice.say(
            text,
            resume_listening=False,
        )


def speak_pending_prompt(learning, voice):
    pending = None

    if hasattr(learning, "pop_pending_prompt"):
        pending = learning.pop_pending_prompt()

    elif hasattr(learning, "pending_prompt"):
        pending = learning.pending_prompt
        learning.pending_prompt = None

    if pending:
        print(f"\n🤖 Mimi Question: {pending}")
        voice.say(
            pending,
            resume_listening=False,
        )


def main():

    print("\n================================")
    print("MIMI LEARNING ONLY - NO SCREEN")
    print("================================\n")

    real_voice = VoiceModule()
    real_voice.start(listening=False)

    test_voice = KeyboardTestVoice(real_voice)

    learning = LearningModule(
        voice_module=test_voice
    )

    learning.start_module()

    print("اختاري النشاط:")
    print("1 - الألوان")
    print("2 - الأرقام")
    print("3 - الحروف")
    print("4 - الجمع")

    choice = input("\nاختيارك: ").strip()

    topic_text = {
        "1": "ألوان",
        "2": "أرقام",
        "3": "حروف",
        "4": "جمع",
    }.get(choice)

    if not topic_text:
        print("❌ اختيار غير صحيح")
        learning.close()
        real_voice.close()
        return

    print(f"\n🎓 بدء نشاط: {topic_text}\n")

    result = learning.start(topic_text)

    print("\n📌 Learning result:", result)

    # السؤال الأول بعد الـMP3
    speak_pending_prompt(
        learning,
        test_voice,
    )

    while learning.is_active():

        if not learning.is_waiting_for_answer():

            # لو الموديول جهز سؤال جديد، احكيه.
            speak_pending_prompt(
                learning,
                test_voice,
            )

            if not learning.is_waiting_for_answer():
                break

        answer = input(
            "\n👧 اكتبي جواب الطفل: "
        ).strip()

        if answer in {
            "وقف",
            "خروج",
            "stop",
        }:
            learning.reset()
            print("\n⏹️ تم إيقاف النشاط")
            break

        # الصحيح في LearningModule هو handle_input()
        # وليس answer()
        result = learning.handle_input(
            answer
        )

        print(
            "\n📌 Learning result:",
            result
        )

        # بعد تقييم الإجابة، الموديول يحضر السؤال التالي
        # داخل pending_prompt. نحكيه بصوت Mimi هنا.
        speak_pending_prompt(
            learning,
            test_voice,
        )

    print("\n✅ انتهى اختبار Learning")

    learning.close()
    real_voice.close()


if __name__ == "__main__":
    main()