import json
import random
import re
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

STORIES_FILE = (
    PROJECT_ROOT
    / "data"
    / "stories"
    / "stories.json"
)

STORIES_AUDIO_DIR = (
    PROJECT_ROOT
    / "data"
    / "stories"
    / "audio"
)


# =========================================================
# CATEGORY WORDS
# =========================================================

CATEGORY_WORDS = {

    "animals": [
        "حيوان",
        "حيوانات",
        "الحيوانات",
        "حيوانية",
        "حيوانيه",
        "أرنب",
        "ارنب",
        "سلحفاة",
        "سلحفاه",
    ],

    "adventure": [
        "مغامرة",
        "مغامره",
        "مغامرات",
        "مغامراتي",
    ],

    "educational": [
        "تربوية",
        "تربويه",
        "تعليمية",
        "تعليميه",
        "مفيدة",
        "مفيده",
        "تعليم",
    ],

    "funny": [
        "مضحكة",
        "مضحكه",
        "مضحك",
        "ضحك",
        "كوميدية",
        "كوميدي",
    ],
}


# =========================================================
# NORMALIZE ARABIC
# =========================================================

def normalize_arabic(
    text,
):

    text = str(
        text
    ).strip().lower()

    # حذف التشكيل
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    # توحيد الألف
    text = (
        text
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
    )

    # توحيد الياء
    text = text.replace(
        "ى",
        "ي",
    )

    # علامات الترقيم
    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text,
    )

    # المسافات
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# STORY MANAGER
# =========================================================

class StoryManager:

    def __init__(self):

        self.stories = []

        self.current_story = None

        # رقم checkpoint الحالي
        self.current_checkpoint_index = 0

        # هل Mimi تنتظر جواب الطفل؟
        self.waiting_for_answer = False

        # آخر قصة تم تشغيلها
        self.last_story_id = None

        # آخر category
        self.last_category = None

        self.load_stories()

    # =====================================================
    # LOAD STORIES
    # =====================================================

    def load_stories(self):

        if not STORIES_FILE.exists():

            raise FileNotFoundError(
                f"Stories file not found: "
                f"{STORIES_FILE}"
            )

        with open(
            STORIES_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        self.stories = (
            data.get(
                "stories",
                [],
            )
        )

        print()
        print(
            f"📚 Loaded "
            f"{len(self.stories)} stories."
        )

        for story in self.stories:

            print(
                f"   📖 "
                f"{story.get('title')} "
                f"[{story.get('category')}]"
            )

    # =====================================================
    # LIST STORIES
    # =====================================================

    def list_stories(
        self,
        category=None,
    ):

        stories = self.stories

        if category:

            stories = (
                self.get_stories_by_category(
                    category
                )
            )

        return [
            {
                "story_id":
                    story.get(
                        "story_id"
                    ),

                "title":
                    story.get(
                        "title"
                    ),

                "category":
                    story.get(
                        "category"
                    ),

                "duration_seconds":
                    story.get(
                        "duration_seconds"
                    ),
            }
            for story in stories
        ]

    # =====================================================
    # GET STORY
    # =====================================================

    def get_story(
        self,
        story_id,
    ):

        for story in self.stories:

            if (
                story.get(
                    "story_id"
                )
                ==
                story_id
            ):

                return story

        return None

    # =====================================================
    # GET STORIES BY CATEGORY
    # =====================================================

    def get_stories_by_category(
        self,
        category,
    ):

        if not category:

            return list(
                self.stories
            )

        category = str(
            category
        ).strip().lower()

        return [
            story
            for story in self.stories
            if (
                str(
                    story.get(
                        "category",
                        "",
                    )
                )
                .strip()
                .lower()
                ==
                category
            )
        ]

    # =====================================================
    # DETECT CATEGORY
    # =====================================================

    def detect_category(
        self,
        text,
    ):

        normalized_text = (
            normalize_arabic(
                text
            )
        )

        for (
            category,
            words,
        ) in CATEGORY_WORDS.items():

            for word in words:

                normalized_word = (
                    normalize_arabic(
                        word
                    )
                )

                if (
                    normalized_word
                    in
                    normalized_text
                ):

                    return category

        return None

    # =====================================================
    # FIND STORY BY TITLE
    # =====================================================

    def find_story_from_text(
        self,
        text,
    ):

        normalized_text = (
            normalize_arabic(
                text
            )
        )

        for story in self.stories:

            title = (
                normalize_arabic(
                    story.get(
                        "title",
                        "",
                    )
                )
            )

            if (
                title
                and
                title in normalized_text
            ):

                return (
                    story.get(
                        "story_id"
                    )
                )

            story_id = (
                story.get(
                    "story_id"
                )
            )

            # ---------------------------------------------
            # Special story keywords
            # ---------------------------------------------

            if (
                story_id
                ==
                "rabbit_turtle"
            ):

                if any(
                    word in normalized_text
                    for word in (
                        "ارنب",
                        "سلحفاة",
                        "سلحفاه",
                    )
                ):

                    return story_id

            if (
                story_id
                ==
                "adventure"
            ):

                if any(
                    word in normalized_text
                    for word in (
                        "نملة",
                        "نمله",
                        "قمح",
                    )
                ):

                    return story_id

            if (
                story_id
                ==
                "educational"
            ):

                if any(
                    word in normalized_text
                    for word in (
                        "كتكوت",
                        "كوك",
                        "وعد",
                    )
                ):

                    return story_id

            if (
                story_id
                ==
                "funny"
            ):

                if any(
                    word in normalized_text
                    for word in (
                        "زوزو",
                        "استحم",
                        "يتحمم",
                    )
                ):

                    return story_id

        return None

    # =====================================================
    # ANOTHER STORY REQUEST
    # =====================================================

    def is_another_story_request(
        self,
        text,
    ):

        text = (
            normalize_arabic(
                text
            )
        )

        phrases = (
            "قصة ثانية",
            "قصه ثانيه",
            "قصة غيرها",
            "قصه غيرها",
            "غير القصة",
            "غير القصه",
            "غيرها",
            "واحدة ثانية",
            "واحده ثانيه",
        )

        for phrase in phrases:

            if (
                normalize_arabic(
                    phrase
                )
                in text
            ):

                return True

        return False

    # =====================================================
    # CHOOSE RANDOM STORY
    # =====================================================

    def choose_random_story(
        self,
        category=None,
        avoid_story_id=None,
    ):

        if category:

            candidates = (
                self.get_stories_by_category(
                    category
                )
            )

        else:

            candidates = list(
                self.stories
            )

        if not candidates:

            return None

        # ---------------------------------------------
        # Avoid previous story when possible
        # ---------------------------------------------

        different = [
            story
            for story in candidates
            if (
                story.get(
                    "story_id"
                )
                !=
                avoid_story_id
            )
        ]

        if different:

            candidates = different

        return random.choice(
            candidates
        )

    # =====================================================
    # START STORY FROM REQUEST
    # =====================================================

    def start_story_from_request(
        self,
        request_text="",
    ):

        request_text = str(
            request_text
        ).strip()

        # ---------------------------------------------
        # Exact story request
        # ---------------------------------------------

        story_id = (
            self.find_story_from_text(
                request_text
            )
        )

        if story_id:

            return self.start_story(
                story_id=
                    story_id
            )

        # ---------------------------------------------
        # Category
        # ---------------------------------------------

        category = (
            self.detect_category(
                request_text
            )
        )

        # ---------------------------------------------
        # "قصة ثانية"
        # ---------------------------------------------

        if (
            self.is_another_story_request(
                request_text
            )
        ):

            if not category:

                category = (
                    self.last_category
                )

        return self.start_story(
            category=category,
            avoid_last=True,
        )

    # =====================================================
    # START STORY
    # =====================================================

    def start_story(
        self,
        story_id=None,
        category=None,
        avoid_last=True,
    ):

        if not self.stories:

            return None

        story = None

        # ---------------------------------------------
        # Exact story
        # ---------------------------------------------

        if story_id:

            story = (
                self.get_story(
                    story_id
                )
            )

        # ---------------------------------------------
        # Category / random
        # ---------------------------------------------

        else:

            avoid_id = None

            if avoid_last:

                avoid_id = (
                    self.last_story_id
                )

            story = (
                self.choose_random_story(
                    category=
                        category,

                    avoid_story_id=
                        avoid_id,
                )
            )

        if story is None:

            return None

        # ---------------------------------------------
        # Set active story
        # ---------------------------------------------

        self.current_story = story

        self.current_checkpoint_index = 0

        self.waiting_for_answer = False

        self.last_story_id = (
            story.get(
                "story_id"
            )
        )

        self.last_category = (
            story.get(
                "category"
            )
        )

        # ---------------------------------------------
        # Audio
        # ---------------------------------------------

        audio_relative = (
            story.get(
                "audio"
            )
        )

        audio_path = None

        if audio_relative:

            audio_path = (
                STORIES_AUDIO_DIR
                /
                audio_relative
            )

        print()
        print("=" * 60)

        print(
            f"📖 Story selected: "
            f"{story.get('title')}"
        )

        print(
            f"📂 Category: "
            f"{story.get('category')}"
        )

        print(
            f"🎧 Audio: "
            f"{audio_path}"
        )

        print("=" * 60)

        return {
            "type":
                "story_started",

            "story_id":
                story.get(
                    "story_id"
                ),

            "title":
                story.get(
                    "title"
                ),

            "category":
                story.get(
                    "category"
                ),

            "audio":
                audio_relative,

            "audio_path":
                str(
                    audio_path
                )
                if audio_path
                else None,

            "audio_exists":
                bool(
                    audio_path
                    and
                    audio_path.exists()
                ),

            "duration_seconds":
                float(
                    story.get(
                        "duration_seconds",
                        0,
                    )
                    or 0
                ),

            "checkpoint":
                self.get_next_checkpoint(),

            "lesson":
                story.get(
                    "lesson",
                    "",
                ),
        }

    # =====================================================
    # GET NEXT CHECKPOINT
    # =====================================================

    def get_next_checkpoint(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return None

        checkpoints = (
            self.current_story.get(
                "checkpoints",
                [],
            )
        )

        if (
            self.current_checkpoint_index
            >=
            len(checkpoints)
        ):

            return None

        checkpoint = (
            checkpoints[
                self.current_checkpoint_index
            ]
        )

        return {
            "index":
                self.current_checkpoint_index,

            "at_seconds":
                float(
                    checkpoint.get(
                        "at_seconds",
                        0,
                    )
                    or 0
                ),

            "question":
                checkpoint.get(
                    "question",
                    "",
                ),

            "expected_keywords":
                checkpoint.get(
                    "expected_keywords",
                    [],
                ),

            "correct_response":
                checkpoint.get(
                    "correct_response",
                    "شطور!",
                ),

            "other_response":
                checkpoint.get(
                    "other_response",
                    "حلو، خلينا نكمل.",
                ),
        }

    # =====================================================
    # REACH CHECKPOINT
    # =====================================================

    def reach_checkpoint(
        self,
    ):

        checkpoint = (
            self.get_next_checkpoint()
        )

        if checkpoint is None:

            self.waiting_for_answer = False

            return None

        self.waiting_for_answer = True

        return {
            "type":
                "story_question",

            "checkpoint":
                checkpoint,
        }

    # =====================================================
    # ANSWER QUESTION
    # =====================================================

    def answer_question(
        self,
        child_answer,
    ):

        if (
            self.current_story
            is None
        ):

            return {
                "type":
                    "no_story",

                "message":
                    "ما في قصة شغالة حاليًا.",
            }

        if not self.waiting_for_answer:

            return {
                "type":
                    "not_waiting",

                "message":
                    "ميمي مش مستنية جواب حاليًا.",
            }

        checkpoint = (
            self.get_next_checkpoint()
        )

        if checkpoint is None:

            return {
                "type":
                    "not_waiting"
            }

        normalized_answer = (
            normalize_arabic(
                child_answer
            )
        )

        expected_keywords = (
            checkpoint.get(
                "expected_keywords",
                [],
            )
        )

        matched = False

        for keyword in expected_keywords:

            normalized_keyword = (
                normalize_arabic(
                    keyword
                )
            )

            if (
                normalized_keyword
                and
                normalized_keyword
                in normalized_answer
            ):

                matched = True
                break

        if matched:

            reaction = (
                checkpoint.get(
                    "correct_response",
                    "شطور!",
                )
            )

        else:

            reaction = (
                checkpoint.get(
                    "other_response",
                    "حلو، خلينا نكمل.",
                )
            )

        # ---------------------------------------------
        # Move to next checkpoint
        # ---------------------------------------------

        self.waiting_for_answer = False

        self.current_checkpoint_index += 1

        next_checkpoint = (
            self.get_next_checkpoint()
        )

        return {
            "type":
                "story_resume",

            "correct":
                matched,

            "reaction":
                reaction,

            "next_checkpoint":
                next_checkpoint,
        }

    # =====================================================
    # FINISH STORY
    # =====================================================

    def finish_story(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return None

        story = (
            self.current_story
        )

        result = {
            "type":
                "story_finished",

            "story_id":
                story.get(
                    "story_id"
                ),

            "title":
                story.get(
                    "title",
                    "القصة",
                ),

            "category":
                story.get(
                    "category"
                ),

            "lesson":
                story.get(
                    "lesson",
                    "",
                ),

            "message":
                (
                    f"وهيك خلصت قصة "
                    f"{story.get('title', 'القصة')}."
                ),
        }

        # ---------------------------------------------
        # Keep last_story/category
        # but clear active story
        # ---------------------------------------------

        self.current_story = None

        self.current_checkpoint_index = 0

        self.waiting_for_answer = False

        return result

    # =====================================================
    # RESET
    # =====================================================

    def reset_story(
        self,
    ):

        self.current_story = None

        self.current_checkpoint_index = 0

        self.waiting_for_answer = False

    # =====================================================
    # STATE
    # =====================================================

    def is_story_active(
        self,
    ):

        return (
            self.current_story
            is not None
        )

    def is_waiting_for_answer(
        self,
    ):

        return bool(
            self.waiting_for_answer
        )

    def get_current_story_id(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return None

        return (
            self.current_story.get(
                "story_id"
            )
        )

    def get_current_category(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return None

        return (
            self.current_story.get(
                "category"
            )
        )

    def get_audio_path(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return None

        audio_relative = (
            self.current_story.get(
                "audio"
            )
        )

        if not audio_relative:

            return None

        return (
            STORIES_AUDIO_DIR
            /
            audio_relative
        )

    def get_duration(
        self,
    ):

        if (
            self.current_story
            is None
        ):

            return 0.0

        return float(
            self.current_story.get(
                "duration_seconds",
                0,
            )
            or 0
        )

    def get_state(
        self,
    ):

        return {
            "active":
                self.is_story_active(),

            "story_id":
                self.get_current_story_id(),

            "category":
                self.get_current_category(),

            "checkpoint_index":
                self.current_checkpoint_index,

            "waiting_for_answer":
                self.waiting_for_answer,

            "next_checkpoint":
                self.get_next_checkpoint(),

            "last_story_id":
                self.last_story_id,

            "last_category":
                self.last_category,
        }


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    manager = (
        StoryManager()
    )

    print()
    print("=" * 60)
    print("📚 STORY MANAGER TEST")
    print("=" * 60)

    print()
    print("Available stories:")

    for story in (
        manager.list_stories()
    ):

        print(
            f"- {story['story_id']} "
            f"| {story['title']} "
            f"| {story['category']} "
            f"| {story['duration_seconds']} sec"
        )

    print()
    print("=" * 60)

    request = (
        "بدي قصة مغامرة"
    )

    print(
        f"👧 Request: {request}"
    )

    result = (
        manager
        .start_story_from_request(
            request
        )
    )

    if result is None:

        print(
            "❌ Story not found."
        )

        raise SystemExit(
            1
        )

    print()
    print(
        f"📖 Selected: "
        f"{result.get('title')}"
    )

    print(
        f"🎧 Audio: "
        f"{result.get('audio_path')}"
    )

    print(
        f"📁 Audio exists: "
        f"{result.get('audio_exists')}"
    )

    print(
        f"⏱️ Duration: "
        f"{result.get('duration_seconds')}"
    )

    print(
        f"❓ First checkpoint: "
        f"{result.get('checkpoint')}"
    )

    print()
    print("=" * 60)