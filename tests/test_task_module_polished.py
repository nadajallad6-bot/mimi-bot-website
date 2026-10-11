import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.modules.task_module import TaskModule


def main():

    tasks = TaskModule(
        voice_module=None
    )

    tasks.start_module()

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

    tasks.set_session(
        fake_session
    )

    print()
    print("=" * 60)
    print("📋 TASK MODULE TEST")
    print("=" * 60)

    result = tasks.start(
        "شو مهامي اليوم"
    )

    print()
    print(
        "Result:",
        result,
    )

    print()
    print(
        "Task #1:",
        tasks.get_task_by_number(
            1
        ),
    )

    print()
    print(
        "By ID:",
        tasks.get_task_by_id(
            "task_001"
        ),
    )

    print()
    print(
        "State:",
        tasks.get_state(),
    )

    assert result["count"] == 1
    assert (
        tasks.get_task_by_number(
            1
        )["task_id"]
        ==
        "task_001"
    )
    assert (
        tasks.get_summary()[
            "completed"
        ]
        ==
        1
    )

    tasks.close()

    print()
    print(
        "✅ Task Module test passed."
    )


if __name__ == "__main__":
    main()