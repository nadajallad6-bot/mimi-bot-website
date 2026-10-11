"""
Mimi Bot - Standalone QuranModule Test
======================================

اختبار مستقل لكل سور القرآن (1 إلى 114) بدون تشغيل main.py.

يدعم:
1) Reading Mode: كل آية مرة واحدة.
2) Memorization Mode: القارئ 3 مرات ثم إدخال قراءة الطفل يدويًا للتقييم.
3) Surah Detection لأي سورة.
4) عرض حالة QuranModule.

تشغيل:
    cd ~/Projects/mimi-bot
    source .venv/bin/activate
    python tests/test_quran.py
"""

from src.modules.quran_module import QuranModule


def divider(char="=", width=72):
    print(char * width)


def print_title(title):
    print()
    divider()
    print(title)
    divider()


def print_main_menu():
    print()
    divider()
    print("📖 MIMI BOT - QURAN STANDALONE TEST")
    divider()
    print("1) اختبار القراءة لأي سورة")
    print("2) اختبار التحفيظ لأي سورة")
    print("3) اختبار اكتشاف سورة")
    print("4) عرض حالة QuranModule")
    print("0) خروج")
    divider()


def get_surah_number_from_user(quran):
    while True:
        print()
        user_input = input(
            "اكتبي اسم السورة أو رقمها (أو /back للرجوع) > "
        ).strip()

        if user_input.lower() == "/back":
            return None

        if not user_input:
            print("⚠️ الإدخال فارغ.")
            continue

        if user_input.isdigit():
            number = int(user_input)
            if 1 <= number <= 114:
                surah = quran.get_surah(number)
                if surah:
                    print()
                    print(
                        f"✅ تم اختيار {surah['name']} "
                        f"({surah['ayah_count']} آية)"
                    )
                    return number

        number = quran.detect_surah(user_input)

        if number is None:
            print(
                "❌ ما قدرت أحدد السورة. "
                "جربي مثلًا: الملك، سورة الإخلاص، أو 112."
            )
            continue

        surah = quran.get_surah(number)

        if surah is None:
            print("❌ السورة غير موجودة في Quran Catalog.")
            continue

        print()
        print(
            f"✅ تم اختيار {surah['name']} "
            f"({surah['ayah_count']} آية)"
        )
        return number


def test_surah_detection(quran):
    print_title("🔎 SURAH DETECTION TEST")

    while True:
        text = input(
            "اكتبي اسم/رقم السورة (أو /back للرجوع) > "
        ).strip()

        if text.lower() == "/back":
            return

        if not text:
            print("⚠️ الإدخال فارغ.")
            continue

        if text.isdigit():
            number = int(text)
            if not 1 <= number <= 114:
                number = None
        else:
            number = quran.detect_surah(text)

        if number is None:
            print("❌ لم يتم اكتشاف سورة.")
            continue

        surah = quran.get_surah(number)

        if not surah:
            print(f"❌ تم اكتشاف الرقم {number} لكن بيانات السورة غير متاحة.")
            continue

        print()
        print("✅ Detection successful")
        print(f"NUMBER     : {surah['number']}")
        print(f"NAME       : {surah['name']}")
        print(f"SHORT NAME : {surah['short_name']}")
        print(f"AYAH COUNT : {surah['ayah_count']}")
        print()


def test_reading(quran):
    print_title("📖 READING MODE TEST")

    surah_number = get_surah_number_from_user(quran)
    if surah_number is None:
        return

    surah = quran.get_surah(surah_number)

    print()
    divider("-")
    print(f"📖 سورة: {surah['name']}")
    print(f"📚 عدد الآيات: {surah['ayah_count']}")
    print("✅ كل آية يجب أن تُشغّل مرة واحدة فقط.")
    print("✅ لا يوجد تكرار ×3 في Reading Mode.")
    divider("-")

    input("\nاضغطي Enter لبدء القراءة (Ctrl+C للإيقاف)...")

    result = quran.start_reading(
        surah_number=surah_number
    )

    print()
    divider()
    print("📋 READING RESULT")
    divider()
    print(result)
    divider()


def test_memorization(quran):
    print_title("🧠 MEMORIZATION MODE TEST")

    surah_number = get_surah_number_from_user(quran)
    if surah_number is None:
        return

    surah = quran.get_surah(surah_number)

    print()
    divider("-")
    print(f"🧠 سورة: {surah['name']}")
    print(f"📚 عدد الآيات: {surah['ayah_count']}")
    print("1) القارئ يشغّل نفس الآية 3 مرات.")
    print("2) بعدها نكتب نص قراءة الطفل يدويًا.")
    print("3) Score >= 85% → الآية التالية.")
    print("4) Score < 85% → نفس الآية 3 مرات من جديد.")
    print()
    print("/state  → عرض حالة QuranModule")
    print("/quit   → إنهاء جلسة التحفيظ")
    divider("-")

    input("\nاضغطي Enter لبدء التحفيظ (Ctrl+C للإيقاف)...")

    result = quran.start_memorization(
        surah_number=surah_number
    )

    print()
    divider()
    print("📋 START RESULT")
    divider()
    print(result)
    divider()

    if not result.get("started"):
        print("❌ جلسة التحفيظ لم تبدأ.")
        return

    while quran.is_memorizing():
        if not quran.is_waiting_for_child():
            print()
            print("⚠️ QuranModule في وضع التحفيظ لكنه لا ينتظر قراءة الطفل.")
            print("STATE:")
            print(quran.get_state())
            quran.reset()
            return

        print()
        divider("-")
        print(
            f"🎤 دور الطفل | {quran.surah_name} | "
            f"الآية {quran.current_ayah}"
        )
        divider("-")

        child_text = input(
            "اكتبي النص الذي قرأه الطفل > "
        ).strip()

        if child_text.lower() == "/quit":
            print()
            print("🛑 تم إيقاف جلسة التحفيظ.")
            quran.reset()
            return

        if child_text.lower() == "/state":
            print()
            print("📊 CURRENT QURAN STATE")
            print(quran.get_state())
            continue

        if not child_text:
            print("⚠️ النص فارغ. اكتبي قراءة الطفل.")
            continue

        evaluation_result = quran.register_repeat(
            child_text=child_text
        )

        print()
        divider()
        print("📊 CHILD ATTEMPT RESULT")
        divider()
        print(evaluation_result)
        divider()

        if evaluation_result.get("surah_completed", False):
            print()
            print(f"🏆 اكتمل اختبار تحفيظ {surah['name']}.")
            return


def show_module_state(quran):
    print_title("📊 QURAN MODULE STATE")
    print(quran.get_state())


def main():
    quran = QuranModule(
        voice_module=None,
        child_id=None,
        reader="alafasy",
        repeat_target=3,
        pass_threshold=85.0,
    )

    try:
        quran.start_module()

        while True:
            print_main_menu()
            choice = input("اختاري الاختبار > ").strip()

            if choice == "1":
                test_reading(quran)
            elif choice == "2":
                test_memorization(quran)
            elif choice == "3":
                test_surah_detection(quran)
            elif choice == "4":
                show_module_state(quran)
            elif choice == "0":
                print()
                print("👋 انتهى اختبار القرآن.")
                break
            else:
                print()
                print("⚠️ اختيار غير صحيح. اكتبي 1 أو 2 أو 3 أو 4 أو 0.")

    except KeyboardInterrupt:
        print()
        print()
        print("🛑 تم إيقاف الاختبار بـ Ctrl+C.")

    except Exception as error:
        print()
        divider()
        print("❌ UNEXPECTED TEST ERROR")
        divider()
        print(type(error).__name__)
        print(error)
        divider()

    finally:
        try:
            quran.close()
        except Exception as error:
            print("⚠️ Error while closing QuranModule:", error)


if __name__ == "__main__":
    main()