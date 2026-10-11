import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.achievement_module import AchievementModule


award_calls = []


def fake_award_achievement(
    child_id,
    achievement_key,
    details=None,
):

    pair = (
        child_id,
        achievement_key,
    )

    if pair in award_calls:

        return {
            "awarded": False,
            "already_exists": True,
        }

    award_calls.append(
        pair
    )

    return {
        "awarded": True,
        "achievement": {
            "key":
                achievement_key,
            "title":
                achievement_key,
            "emoji":
                "🏆",
        },
    }


def main():

    print()
    print("=" * 60)
    print("🏆 ACHIEVEMENT MODULE TEST")
    print("=" * 60)

    achievements = AchievementModule(
        voice_module=None
    )

    achievements.start_module()
    achievements.set_child(
        "test_child_001"
    )

    with patch(
        "src.modules.achievement_module.award_achievement",
        side_effect=
            fake_award_achievement,
    ):

        first = achievements.check_event(
            "story_completed",
            story_id="story_001",
        )

        second = achievements.check_event(
            "story_completed",
            story_id="story_001",
        )

    print()
    print(
        "First event:",
        first,
    )

    print()
    print(
        "Repeated event:",
        second,
    )

    assert len(first) == 1
    assert second == []

    achievements.close()

    print()
    print(
        "✅ Achievement duplicate-protection flow passed."
    )


if __name__ == "__main__":
    main()