from src.database.achievements import (
    award_achievement,
    count_child_achievements,
    get_child_achievements,
)


# =========================================================
# ACHIEVEMENT MODULE
# =========================================================

class AchievementModule:

    def __init__(
        self,
        voice_module=None,
    ):

        self.voice = (
            voice_module
        )

        self.child_id = None

        self.started = False

    # =====================================================
    # START
    # =====================================================

    def start_module(self):

        if self.started:

            return

        print()
        print("=" * 60)
        print("🏆 STARTING ACHIEVEMENT MODULE")
        print("=" * 60)

        self.started = True

        print(
            "✅ Achievement Module ready."
        )

        print("=" * 60)

    # =====================================================
    # SET VOICE
    # =====================================================

    def set_voice(
        self,
        voice_module,
    ):

        self.voice = (
            voice_module
        )


    # =====================================================
    # SET CHILD
    # =====================================================

    def set_child(
        self,
        child_id,
    ):

        if child_id:

            self.child_id = str(
                child_id
            )

            print()
            print(
                f"🏆 Achievement child: "
                f"{self.child_id}"
            )

        else:

            self.child_id = None

            print()
            print(
                "🏆 Achievement Module: "
                "Guest mode"
            )

    # =====================================================
    # CLEAR CHILD
    # =====================================================

    def clear_child(self):

        self.child_id = None

    # =====================================================
    # ANNOUNCE
    # =====================================================

    def announce(
        self,
        achievement,
    ):

        if not achievement:
            return False

        emoji = achievement.get(
            "emoji",
            "🏆",
        )

        title = achievement.get(
            "title",
            "إنجاز جديد",
        )

        print()
        print("=" * 60)

        print(
            f"{emoji} NEW ACHIEVEMENT"
        )

        print(
            f"🏆 {title}"
        )

        print("=" * 60)

        if self.voice is None:

            return True

        try:

            result = self.voice.say(
                f"مبروك! "
                f"حصلت على شارة "
                f"{title}."
            )

            return (
                True
                if result is None
                else bool(result)
            )

        except TypeError:

            try:

                result = self.voice.say(
                    f"مبروك! "
                    f"حصلت على شارة "
                    f"{title}."
                )

                return (
                    True
                    if result is None
                    else bool(result)
                )

            except Exception as error:

                print(
                    "⚠️ Achievement voice error:",
                    error,
                )

                return False

        except Exception as error:

            print(
                "⚠️ Achievement voice error:",
                error,
            )

            return False


    # =====================================================
    # TRY AWARD
    # =====================================================

    def try_award(
        self,
        achievement_key,
        details=None,
    ):

        if not self.child_id:

            return None

        try:

            result = award_achievement(
                child_id=
                    self.child_id,

                achievement_key=
                    achievement_key,

                details=
                    details or {},
            )

        except Exception as error:

            print()
            print(
                "⚠️ Achievement DB error:"
            )

            print(
                error
            )

            return None

        if not isinstance(
            result,
            dict,
        ):

            return None

        if result.get(
            "awarded",
            False,
        ):

            achievement = (
                result.get(
                    "achievement"
                )
            )

            self.announce(
                achievement
            )

            return achievement

        return None

    # =====================================================
    # CHECK EVENT
    # =====================================================

    def check_event(
        self,
        event_type,
        **data,
    ):

        if not self.child_id:

            return []

        event_type = str(
            event_type or ""
        ).strip().lower()

        awarded = []

        # -------------------------------------------------
        # Riddle
        # -------------------------------------------------

        if event_type == "riddle_correct":

            item = self.try_award(
                "first_riddle",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

            total_points = int(
                data.get(
                    "total_points",
                    0,
                )
                or 0
            )

            if total_points >= 10:

                item = self.try_award(
                    "points_10",
                    details={
                        "total_points":
                            total_points
                    },
                )

                if item:
                    awarded.append(
                        item
                    )

            if total_points >= 25:

                item = self.try_award(
                    "points_25",
                    details={
                        "total_points":
                            total_points
                    },
                )

                if item:
                    awarded.append(
                        item
                    )

            if total_points >= 50:

                item = self.try_award(
                    "points_50",
                    details={
                        "total_points":
                            total_points
                    },
                )

                if item:
                    awarded.append(
                        item
                    )

        # -------------------------------------------------
        # Story
        # -------------------------------------------------

        elif event_type == "story_completed":

            item = self.try_award(
                "first_story",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Learning
        # -------------------------------------------------

        elif event_type == "learning_completed":

            item = self.try_award(
                "first_learning",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Quran Ayah
        # -------------------------------------------------

        elif event_type == "quran_ayah_mastered":

            item = self.try_award(
                "first_quran_ayah",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Quran Surah
        # -------------------------------------------------

        elif event_type == "quran_surah_completed":

            item = self.try_award(
                "first_surah",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Quran Read
        # -------------------------------------------------

        elif event_type == "quran_read_completed":

            item = self.try_award(
                "first_quran_read",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Adhkar
        # -------------------------------------------------

        elif event_type == "adhkar_completed":

            item = self.try_award(
                "first_adhkar",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        # -------------------------------------------------
        # Tasks
        # -------------------------------------------------

        elif event_type == "tasks_viewed":

            item = self.try_award(
                "first_tasks_view",
                details=data,
            )

            if item:
                awarded.append(
                    item
                )

        return awarded

    # =====================================================
    # GET ALL
    # =====================================================

    def get_all(self):

        if not self.child_id:

            return []

        try:

            return (
                get_child_achievements(
                    self.child_id
                )
            )

        except Exception:

            return []

    # =====================================================
    # COUNT
    # =====================================================

    def count(self):

        if not self.child_id:

            return 0

        try:

            return (
                count_child_achievements(
                    self.child_id
                )
            )

        except Exception:

            return 0

    # =====================================================
    # STATE
    # =====================================================

    def get_state(self):

        return {
            "started":
                self.started,

            "child_id":
                self.child_id,

            "guest":
                self.child_id
                is None,

            "count":
                self.count()
                if self.child_id
                else 0,
        }


    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.clear_child()

        self.started = False

        print(
            "✅ Achievement Module closed."
        )


# =========================================================
# TEST
# =========================================================

def test_module():

    achievements = (
        AchievementModule()
    )

    achievements.start_module()

    achievements.set_child(
        "test_child_001"
    )

    print()
    print(
        "Current achievements:"
    )

    for item in achievements.get_all():

        print(
            item
        )

    achievements.close()


if __name__ == "__main__":

    test_module()