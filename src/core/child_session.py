from typing import Any

from src.database.mongodb import (
    close_connection,
    get_database,
)


def get_child_by_face(
    face_id: str,
) -> dict[str, Any] | None:

    database = get_database()

    return database.children.find_one(
        {
            "face_id":
                face_id.strip().lower()
        },
        {
            "_id": 0
        },
    )


def get_active_tasks(
    child_id: str,
) -> list[dict[str, Any]]:

    database = get_database()

    tasks = list(
        database.tasks.find(
            {
                "child_id": child_id,
                "status": {
                    "$in": [
                        "repeat",
                        "pending",
                        "in_progress",
                    ]
                },
            },
            {
                "_id": 0
            },
        )
    )

    priority = {
        "repeat": 0,
        "in_progress": 1,
        "pending": 2,
    }

    tasks.sort(
        key=lambda task:
            priority.get(
                task.get(
                    "status",
                    "pending",
                ),
                99,
            )
    )

    return tasks


def get_quran_progress(
    child_id: str,
) -> list[dict[str, Any]]:

    database = get_database()

    return list(
        database.quran_progress.find(
            {
                "child_id":
                    child_id
            },
            {
                "_id": 0
            },
        ).sort(
            [
                (
                    "surah_number",
                    1,
                ),
                (
                    "ayah_number",
                    1,
                ),
            ]
        )
    )


def normalize_gender(
    gender,
) -> str:

    value = str(
        gender or ""
    ).strip().lower()

    if value in {
        "girl",
        "female",
        "بنت",
        "انثى",
        "أنثى",
    }:
        return "girl"

    if value in {
        "boy",
        "male",
        "ولد",
        "ذكر",
    }:
        return "boy"

    return "unknown"


def create_child_session(
    face_id: str,
) -> dict[str, Any] | None:

    child = get_child_by_face(
        face_id
    )

    if child is None:

        print(
            f"👤 Unknown face: "
            f"{face_id}"
        )

        return None

    child_id = child[
        "child_id"
    ]

    # توحيد قيمة gender حتى Mimi
    # تتعامل معها دائمًا بنفس الشكل.
    child["gender"] = normalize_gender(
        child.get(
            "gender"
        )
    )

    session = {
        "child": child,
        "tasks":
            get_active_tasks(
                child_id
            ),
        "quran_progress":
            get_quran_progress(
                child_id
            ),
    }

    return session


def show_session(
    session: dict[str, Any],
) -> None:

    child = session[
        "child"
    ]

    tasks = session[
        "tasks"
    ]

    quran = session[
        "quran_progress"
    ]

    name = child.get(
        "name",
        "صديقي",
    )

    gender = normalize_gender(
        child.get(
            "gender"
        )
    )

    age = child.get(
        "age"
    )

    print()
    print("=" * 55)

    print(
        f"👋 Mimi recognized: "
        f"{name}"
    )

    print(
        f"🆔 Child ID: "
        f"{child['child_id']}"
    )

    if gender == "girl":

        print(
            "🚻 Gender: girl 👧"
        )

    elif gender == "boy":

        print(
            "🚻 Gender: boy 👦"
        )

    else:

        print(
            "🚻 Gender: unknown"
        )

    if age is not None:

        print(
            f"🎂 Age: {age}"
        )

    print("=" * 55)

    if not tasks:

        print(
            "✅ No active tasks."
        )

    else:

        print(
            f"📋 Active tasks: "
            f"{len(tasks)}"
        )

        for (
            number,
            task,
        ) in enumerate(
            tasks,
            start=1,
        ):

            status = task.get(
                "status",
                "pending",
            )

            title = task.get(
                "title",
                "Task",
            )

            if status == "repeat":

                icon = "🔁"

            elif (
                status
                ==
                "in_progress"
            ):

                icon = "▶️"

            else:

                icon = "⏳"

            print(
                f"{number}. "
                f"{icon} "
                f"{title} "
                f"[{status}]"
            )

    print(
        f"📖 Quran records: "
        f"{len(quran)}"
    )

    print("=" * 55)


def get_session_gender(
    session: dict[str, Any] | None,
) -> str:

    """
    ترجع:
        girl
        boy
        unknown
    """

    if not session:

        return "unknown"

    child = session.get(
        "child",
        {},
    )

    return normalize_gender(
        child.get(
            "gender"
        )
    )


if __name__ == "__main__":

    try:

        # للاختبار فقط.
        session = (
            create_child_session(
                "saraf"
            )
        )

        if session:

            show_session(
                session
            )

            print()

            print(
                "Gender from session:",
                get_session_gender(
                    session
                ),
            )

    finally:

        close_connection()