import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.quran_module import QuranModule


def main():
    print("\n============================")
    print("MIMI QURAN ONLY - NO SCREEN")
    print("============================\n")

    voice = VoiceModule()
    voice.start(listening=False)

    quran = QuranModule(
        voice_module=voice,
        child_id=None,
        reader="alafasy",
        repeat_target=3,
        pass_threshold=85.0,
    )

    quran.start_module()

    print("اختاري:")
    print("1 - سماع سورة")
    print("2 - تحفيظ سورة")

    choice = input("\nاختيارك: ").strip()

    if choice == "1":
        surah_text = input(
            "\nاكتبي اسم السورة (مثال: الإخلاص): "
        ).strip()

        print(f"\n📖 تشغيل قراءة: {surah_text}\n")

        result = quran.start_reading(
            request_text=surah_text
        )

        print("\n📌 Quran result:", result)

    elif choice == "2":
        surah_text = input(
            "\nاكتبي اسم السورة (مثال: الإخلاص): "
        ).strip()

        print(f"\n🧠 بدء التحفيظ: {surah_text}\n")

        result = quran.start_memorization(
            request_text=surah_text
        )

        print("\n📌 Quran result:", result)

        # في وضع التحفيظ، QuranModule نفسه يشغّل المايك
        # بعد أن يقرأ الشيخ الآية 3 مرات.
        while quran.is_active():

            if quran.is_waiting_for_child():
                print("\n🎤 احكي الآية الآن...")

                child_text = voice.wait_for_command(
                    timeout=20
                )

                if not child_text:
                    print(
                        "\n⚠️ ما وصل كلام واضح. "
                        "رح نستنى مرة ثانية."
                    )
                    continue

                print(
                    f"\n👧 Child STT: {child_text}"
                )

                result = quran.handle_input(
                    child_text
                )

                print(
                    "\n📌 Quran result:",
                    result
                )

            elif quran.is_waiting_for_surah():
                print(
                    "\n⚠️ الموديول بانتظار اسم سورة."
                )
                break

            else:
                # إذا الموديول عم يشغّل صوت/ينتقل بين مراحل،
                # ما نعمل شيء هنا.
                import time
                time.sleep(0.10)

    else:
        print("❌ اختيار غير صحيح")

    quran.close()
    voice.close()

    print("\n✅ انتهى اختبار القرآن")


if __name__ == "__main__":
    main()