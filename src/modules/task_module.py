# =========================================================
# MIMI BOT - TASK MODULE
# =========================================================


class TaskModule:

    def __init__(
        self,
        voice_module=None,
    ):

        self.voice = voice_module

        self.started = False

        # -------------------------------------------------
        # Current child/session
        # -------------------------------------------------

        self.child_id = None

        self.child_name = None

        self.tasks = []

        # -------------------------------------------------
        # State
        # -------------------------------------------------

        self.active = False

    # =====================================================
    # START MODULE
    # =====================================================

    def start_module(self):

        if self.started:
            return

        print()
        print("=" * 60)
        print("📋 STARTING TASK MODULE")
        print("=" * 60)

        self.started = True

        print(
            "✅ Task Module ready."
        )

        print("=" * 60)

    # =====================================================
    # SET VOICE
    # =====================================================

    def set_voice(
        self,
        voice_module,
    ):

        self.voice = voice_module

    # =====================================================
    # SAY
    # =====================================================

    def say(
        self,
        text,
        resume_listening=True,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:
            return False

        if self.voice is not None:

            try:

                result = self.voice.say(
                    text,
                    resume_listening=
                        resume_listening,
                )

                return (
                    True
                    if result is None
                    else bool(result)
                )

            except TypeError:

                result = self.voice.say(
                    text
                )

                return (
                    True
                    if result is None
                    else bool(result)
                )

            except Exception as error:

                print(
                    "⚠️ Task voice error:",
                    error,
                )

                return False

        print(
            f"🤖 Mimi: {text}"
        )

        return True


    # =====================================================
    # SET CHILD SESSION
    # =====================================================

    def set_session(
        self,
        session,
    ):

        self.reset()

        # -------------------------------------------------
        # Guest / no session
        # -------------------------------------------------

        if session is None:

            self.child_id = None

            self.child_name = None

            self.tasks = []

            print()
            print(
                "👤 Task Module: Guest mode"
            )

            return

        child = (
            session.get(
                "child",
                {}
            )
        )

        self.child_id = (
            child.get(
                "child_id"
            )
        )

        self.child_name = (
            child.get(
                "name",
                "صديقي",
            )
        )

        raw_tasks = (
            session.get(
                "tasks",
                []
            )
            or []
        )

        self.tasks = [
            dict(task)
            for task in raw_tasks
            if isinstance(
                task,
                dict,
            )
        ]

        print()
        print("=" * 60)
        print("📋 TASK SESSION LOADED")
        print("=" * 60)

        print(
            f"👧 Child: "
            f"{self.child_name}"
        )

        print(
            f"🆔 Child ID: "
            f"{self.child_id}"
        )

        print(
            f"📋 Tasks loaded: "
            f"{len(self.tasks)}"
        )

        print("=" * 60)

    # =====================================================
    # CLEAR SESSION
    # =====================================================

    def clear_session(self):

        self.reset()

        self.child_id = None

        self.child_name = None

        self.tasks = []

        print()
        print(
            "📋 Task session cleared."
        )

    # =====================================================
    # TASK HELPERS
    # =====================================================

    def get_task_by_id(
        self,
        task_id,
    ):

        task_id = str(
            task_id or ""
        ).strip()

        if not task_id:
            return None

        for task in self.tasks:

            if (
                str(
                    task.get(
                        "task_id",
                        "",
                    )
                ).strip()
                ==
                task_id
            ):

                return task

        return None

    def get_task_by_number(
        self,
        number,
        active_only=True,
    ):
        """
        number is 1-based, exactly like the number Mimi says aloud.
        """

        try:
            number = int(number)
        except Exception:
            return None

        if number < 1:
            return None

        source = (
            self.get_active_tasks()
            if active_only
            else self.tasks
        )

        index = number - 1

        if index >= len(source):
            return None

        return source[index]

    def replace_tasks(
        self,
        tasks,
    ):
        """
        Refresh the in-memory task snapshot.

        Persistence stays owned by the database/session layer.
        """

        self.tasks = [
            dict(task)
            for task in (
                tasks or []
            )
            if isinstance(
                task,
                dict,
            )
        ]

        return len(
            self.tasks
        )

    # =====================================================
    # ACTIVE TASKS
    # =====================================================

    def get_active_tasks(self):

        return [
            task
            for task in self.tasks
            if task.get(
                "status"
            )
            in (
                "pending",
                "repeat",
                "in_progress",
            )
        ]

    # =====================================================
    # COMPLETED TASKS
    # =====================================================

    def get_completed_tasks(self):

        return [
            task
            for task in self.tasks
            if task.get(
                "status"
            )
            == "completed"
        ]

    # =====================================================
    # TASK STATUS NAME
    # =====================================================

    def get_status_name(
        self,
        status,
    ):

        names = {

            "pending":
                "لسا ما بدأت",

            "in_progress":
                "قيد التنفيذ",

            "repeat":
                "بدها إعادة",

            "completed":
                "مكتملة",

            "cancelled":
                "ملغاة",
        }

        return names.get(
            status,
            status,
        )

    # =====================================================
    # START TASK ACTIVITY
    # =====================================================

    def start(
        self,
        request_text="",
    ):

        if not self.started:

            self.start_module()

        self.active = True

        print()
        print("=" * 60)
        print("📋 TASK MODE")
        print("=" * 60)

        # -------------------------------------------------
        # Guest
        # -------------------------------------------------

        if self.child_id is None:

            self.say(
                "المهام خاصة بالأطفال "
                "المسجلين عندي."
            )

            self.active = False

            return {
                "handled": True,
                "guest": True,
                "tasks": [],
            }

        # -------------------------------------------------
        # Active Tasks
        # -------------------------------------------------

        active_tasks = (
            self.get_active_tasks()
        )

        print(
            f"👧 Child: "
            f"{self.child_name}"
        )

        print(
            f"📋 Active tasks: "
            f"{len(active_tasks)}"
        )

        # -------------------------------------------------
        # No tasks
        # -------------------------------------------------

        if not active_tasks:

            self.say(
                f"{self.child_name}، "
                "ما عندك مهام معلقة حاليًا."
            )

            self.active = False

            return {
                "handled": True,
                "count": 0,
                "tasks": [],
            }

        # -------------------------------------------------
        # Build speech
        # -------------------------------------------------

        if len(active_tasks) == 1:

            response = (
                f"{self.child_name}، "
                "عندك مهمة واحدة. "
            )

        else:

            response = (
                f"{self.child_name}، "
                f"عندك "
                f"{len(active_tasks)} "
                "مهام. "
            )

        for index, task in enumerate(
            active_tasks,
            start=1,
        ):

            title = (
                task.get(
                    "title",
                    "مهمة",
                )
            )

            status = (
                task.get(
                    "status",
                    "pending",
                )
            )

            status_name = (
                self.get_status_name(
                    status
                )
            )

            print()
            print(
                f"{index}. "
                f"{title}"
            )

            print(
                f"   Status: "
                f"{status}"
            )

            response += (
                f"المهمة رقم "
                f"{index}: "
                f"{title}. "
                f"وحالتها "
                f"{status_name}. "
            )

        self.say(
            response
        )

        self.active = False

        return {
            "handled": True,
            "count":
                len(active_tasks),
            "tasks":
                active_tasks,
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    def get_summary(self):

        active = (
            self.get_active_tasks()
        )

        completed = (
            self.get_completed_tasks()
        )

        return {

            "child_id":
                self.child_id,

            "child_name":
                self.child_name,

            "total":
                len(
                    self.tasks
                ),

            "active":
                len(
                    active
                ),

            "completed":
                len(
                    completed
                ),
        }

    # =====================================================
    # STATE
    # =====================================================

    def is_active(self):

        return bool(
            self.active
        )

    def get_state(self):

        summary = self.get_summary()

        return {
            "started":
                self.started,

            "active":
                self.active,

            "child_id":
                self.child_id,

            "child_name":
                self.child_name,

            "total":
                summary["total"],

            "active_count":
                summary["active"],

            "completed_count":
                summary["completed"],

            "tasks":
                [
                    dict(task)
                    for task in self.tasks
                ],
        }

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.active = False

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.clear_session()

        self.started = False

        print(
            "✅ Task Module closed."
        )


# =========================================================
# STANDALONE TEST
# =========================================================

def test_task_module():

    task_module = (
        TaskModule(
            voice_module=None
        )
    )

    task_module.start_module()

    # Fake child session for local test
    fake_session = {

        "child": {

            "child_id":
                "test_child_001",

            "name":
                "Sara",
        },

        "tasks": [

            {
                "task_id":
                    "task_001",

                "title":
                    "مراجعة سورة الفلق",

                "status":
                    "pending",

                "category":
                    "quran",
            },

            {
                "task_id":
                    "task_002",

                "title":
                    "حل واجب الرياضيات",

                "status":
                    "completed",

                "category":
                    "study",
            },
        ],
    }

    task_module.set_session(
        fake_session
    )

    result = (
        task_module.start(
            "شو مهامي اليوم"
        )
    )

    print()
    print(
        "📊 Result:"
    )

    print(
        result
    )

    print()
    print(
        "📊 Summary:"
    )

    print(
        task_module.get_summary()
    )

    task_module.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    test_task_module()