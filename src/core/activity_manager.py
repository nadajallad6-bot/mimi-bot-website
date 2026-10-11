class ActivityManager:
    """
    مسؤول عن تحديد النشاط الذي طلبه الطفل.
    """

    def detect_activity(self, text: str) -> str:
        text = text.strip().lower()

        quran_words = [
            "قرآن",
            "القرآن",
            "سورة",
            "احفظ",
            "حفظ",
        ]

        story_words = [
            "قصة",
            "قصه",
            "حكاية",
            "احكيلي",
        ]

        riddle_words = [
            "لغز",
            "الغاز",
            "ألغاز",
        ]

        task_words = [
            "مهامي",
            "مهمتي",
            "المهام",
            "شو علي",
        ]

        adhkar_words = [
            "اذكار",
            "أذكار",
            "ذكر",
        ]

        learning_words = [
            "تعلم",
            "علمني",
            "نتعلم",
        ]

        if any(word in text for word in quran_words):
            return "quran"

        if any(word in text for word in story_words):
            return "stories"

        if any(word in text for word in riddle_words):
            return "riddles"

        if any(word in text for word in task_words):
            return "tasks"

        if any(word in text for word in adhkar_words):
            return "adhkar"

        if any(word in text for word in learning_words):
            return "learning"

        # أي شيء غير معروف يروح للأسئلة العامة
        return "general_question"


if __name__ == "__main__":
    manager = ActivityManager()

    tests = [
        "ميمي بدي أحفظ قرآن",
        "احكيلي قصة",
        "اعطيني لغز",
        "شو مهامي اليوم",
        "بدي أذكار",
        "علمني الأرقام",
        "ليش السماء زرقا",
    ]

    for text in tests:
        activity = manager.detect_activity(text)
        print(f"{text} -> {activity}")
