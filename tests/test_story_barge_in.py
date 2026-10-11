import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.story_module import (
    STORIES,
    StoryModule,
)
from src.modules.voice_module import VoiceModule


def main():

    print()
    print("=" * 60)
    print("📚 STORY BARGE-IN SHORT TEST")
    print("=" * 60)
    print("خلال تشغيل القصة جرّبي:")
    print("  وطي الصوت")
    print("  علي الصوت")
    print("  وقف")
    print()
    print("التست يشغّل أول 30 ثانية فقط إذا ما قلتي وقف.")
    print("=" * 60)

    voice = VoiceModule()
    story = None

    try:

        if not voice.start(
            listening=True
        ):
            return

        story = StoryModule(
            voice_module=voice
        )

        story.start_module()

        story.current_story_key = "animals"
        story.current_story = STORIES["animals"]
        story.current_position = 0.0
        story.active = True

        ok = story._play_audio_segment(
            0.0,
            30.0,
        )

        print()
        print("=" * 60)
        print("📌 TEST RESULT")
        print("=" * 60)
        print(
            "audio_ok:",
            ok,
        )
        print(
            "last_control_command:",
            story.last_control_command,
        )
        print(
            "current_position:",
            round(
                story.current_position,
                2,
            ),
        )
        print(
            "volume:",
            voice.get_volume(),
        )
        print("=" * 60)

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test stopped."
        )

    finally:

        if story is not None:
            story.close()

        voice.close()


if __name__ == "__main__":
    main()
