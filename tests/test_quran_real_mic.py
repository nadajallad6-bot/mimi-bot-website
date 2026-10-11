from src.modules.voice_module import VoiceModule
from src.modules.quran_module import QuranModule


def main():

    voice = VoiceModule()

    quran = None

    try:

        print()
        print("=" * 70)
        print("📖 MIMI QURAN REAL MICROPHONE TEST")
        print("=" * 70)

        # -------------------------------------------------
        # Voice
        # -------------------------------------------------

        voice.start(
            listening=False
        )

        # -------------------------------------------------
        # Quran
        # -------------------------------------------------

        quran = QuranModule(
            voice_module=voice,
            child_id=None,      # Guest - no MongoDB saving
            reader="alafasy",
            repeat_target=3,    # الشيخ ×3 في وضع الحفظ
            pass_threshold=85.0,
        )

        quran.start_module()

        # -------------------------------------------------
        # Test Surah Al-Ikhlas
        # -------------------------------------------------

        print()
        print("🧠 Starting memorization...")
        print("📖 Surah: Al-Ikhlas (112)")
        print()

        result = quran.start_memorization(
            surah_number=112
        )

        print()
        print("START RESULT:")
        print(result)

        if not result.get(
            "started",
            False,
        ):

            print()
            print(
                "❌ Memorization could not start."
            )

            return

        # =================================================
        # INTERACTIVE LOOP
        # =================================================

        while quran.is_active():

            # ---------------------------------------------
            # Wait only after Sheikh finishes ×3
            # ---------------------------------------------

            if quran.is_waiting_for_child():

                print()
                print("=" * 70)
                print("🎤 احكي الآية هسا...")
                print("=" * 70)

                child_text = voice.wait_for_command(
                    timeout=30
                )

                if not child_text:

                    print()
                    print(
                        "⚠️ ما سمعت قراءة."
                    )

                    continue

                print()
                print(
                    "🎤 STT HEARD:"
                )

                print(
                    child_text
                )

                result = quran.handle_input(
                    child_text
                )

                print()
                print("=" * 70)
                print("📊 RESULT")
                print("=" * 70)

                print(
                    result
                )

                # -----------------------------------------
                # Surah finished
                # -----------------------------------------

                if (
                    isinstance(result, dict)
                    and
                    result.get(
                        "surah_completed",
                        False,
                    )
                ):

                    print()
                    print(
                        "🏆 SURAH COMPLETED"
                    )

                    break

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test stopped."
        )

    finally:

        if quran is not None:

            try:
                quran.close()
            except Exception:
                pass

        try:
            voice.close()
        except Exception:
            pass

        print()
        print(
            "✅ Test closed."
        )


if __name__ == "__main__":

    main()
