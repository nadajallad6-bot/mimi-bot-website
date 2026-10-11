import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.voice_module import VoiceModule
from src.modules.safety_module import SafetyModule


# =========================================================
# SETTINGS
# =========================================================

COMMAND_TIMEOUT = 20.0
POLL_DELAY = 0.05


# =========================================================
# HELPERS
# =========================================================

def print_menu():

    print()
    print("=" * 60)
    print("MIMI SAFETY ONLY - NO SCREEN")
    print("=" * 60)
    print("اختاري الاختبار:")
    print("1 - اختبار عبارات الطوارئ بالمايك")
    print("2 - اختبار الصوت العالي يدويًا")
    print("3 - اختبار كشف البكاء يدويًا")
    print("4 - عرض حالة Safety Module")
    print("0 - خروج")
    print("=" * 60)


def get_voice_command_direct(
    voice,
    timeout=COMMAND_TIMEOUT,
):
    """
    نقرأ مباشرة من Queue الخاصة بـ VoiceListener.

    هذا يتجنب أي انتظار إضافي داخل VoiceModule.wait_for_command()
    أثناء الاختبار المستقل.
    """

    start = time.monotonic()

    while (
        time.monotonic() - start
        <
        timeout
    ):

        command = (
            voice.listener.get_command()
        )

        if command:

            return command

        time.sleep(
            POLL_DELAY
        )

    return None


# =========================================================
# VOICE SAFETY TEST
# =========================================================

def test_voice_phrases(
    voice,
    safety,
):

    print()
    print("=" * 60)
    print("🎤 VOICE SAFETY TEST")
    print("=" * 60)
    print("جربي مثلاً:")
    print("- ميمي ساعدني")
    print("- ميمي ساعدني بالواجب")
    print("- أنا بخير")
    print()
    print(
        "بعد كل جملة رح يرجع يستنى جملة ثانية."
    )
    print(
        "للرجوع للقائمة اضغطي Ctrl+C مرة واحدة."
    )
    print("=" * 60)

    voice.clear_commands()
    voice.enable()

    try:

        while True:

            print()
            print("🎤 احكي الآن...")

            text = (
                get_voice_command_direct(
                    voice
                )
            )

            if not text:

                print(
                    "⚠️ ما وصل كلام واضح، "
                    "رح نجرب مرة ثانية."
                )

                continue

            print()
            print(
                f"👧 Child STT: {text}"
            )

            # Important:
            # Stop mic while Mimi responds so her own voice
            # is not interpreted as a new safety command.
            voice.disable()

            result = (
                safety.handle_voice(
                    text
                )
            )

            print()
            print(
                "📌 Safety result:"
            )
            print(
                result
            )

            print()
            print(
                "📌 Safety state:"
            )
            print(
                safety.get_state()
            )

            # safety.say() may re-enable the listener itself.
            # If not, ensure it is enabled for next child turn.
            voice.clear_commands()
            voice.enable()

    except KeyboardInterrupt:

        print()
        print(
            "↩️ رجعنا للقائمة."
        )

        voice.disable()

        voice.clear_commands()


# =========================================================
# LOUD SOUND TEST
# =========================================================

def test_loud_sound(
    safety,
):

    print()
    print("=" * 60)
    print("🔊 LOUD SOUND TEST")
    print("=" * 60)
    print(
        "اختبار للمنطق فقط بدون الحساس الحقيقي."
    )
    print(
        "رح نرسل 3 loud hits متقاربة."
    )

    safety.reset_detection_buffers()

    for i in range(
        1,
        4,
    ):

        print()
        print(
            f"🔊 Loud hit {i}/3"
        )

        result = (
            safety.register_loud_sound(
                sound_level=
                    90 + i,

                duration_ms=
                    350,
            )
        )

        print(
            "📌 Result:",
            result,
        )

        if safety.is_active():
            break

        time.sleep(
            0.7
        )

    print()
    print(
        "📌 Final Safety state:"
    )
    print(
        safety.get_state()
    )

    if safety.is_active():

        safety.clear_alert(
            reason=
                "manual_test_clear"
        )


# =========================================================
# CRY TEST
# =========================================================

def test_cry(
    safety,
):

    print()
    print("=" * 60)
    print("😢 CRY DETECTION TEST")
    print("=" * 60)
    print(
        "اختبار للمنطق فقط بدون مودل البكاء الحقيقي."
    )
    print(
        "رح نرسل كشفين بكاء متقاربين."
    )

    safety.reset_detection_buffers()

    for i in range(
        1,
        3,
    ):

        print()
        print(
            f"😢 Cry hit {i}/2"
        )

        result = (
            safety.register_cry(
                confidence=
                    0.90 + (i * 0.02),

                duration_ms=
                    1200,
            )
        )

        print(
            "📌 Result:",
            result,
        )

        if safety.is_active():
            break

        time.sleep(
            0.8
        )

    print()
    print(
        "📌 Final Safety state:"
    )
    print(
        safety.get_state()
    )

    if safety.is_active():

        safety.clear_alert(
            reason=
                "manual_test_clear"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("============================")
    print("MIMI SAFETY ONLY - NO SCREEN")
    print("============================")
    print()

    voice = VoiceModule()
    safety = None

    try:

        voice.start(
            listening=False
        )

        safety = SafetyModule(
            voice_module=voice
        )

        safety.start_module()

        safety.set_child(
            None
        )

        while True:

            print_menu()

            choice = input(
                "\nاختيارك: "
            ).strip()

            if choice == "1":

                test_voice_phrases(
                    voice,
                    safety,
                )

            elif choice == "2":

                voice.disable()

                test_loud_sound(
                    safety
                )

            elif choice == "3":

                voice.disable()

                test_cry(
                    safety
                )

            elif choice == "4":

                print()
                print(
                    "📌 Safety state:"
                )
                print(
                    safety.get_state()
                )

            elif choice == "0":

                break

            else:

                print(
                    "❌ اختيار غير صحيح."
                )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 تم إيقاف الاختبار."
        )

    finally:

        if safety is not None:
            safety.close()

        voice.close()

        print()
        print(
            "✅ انتهى اختبار Safety Module"
        )


if __name__ == "__main__":

    main()