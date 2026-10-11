from src.database.mongodb import (
    get_database,
    close_connection,
)


def main():

    db = get_database()

    children = db["children"]

    child_id = "test_child_001"

    # Sara = girl
    gender = "girl"

    result = children.update_one(
        {
            "child_id": child_id
        },
        {
            "$set": {
                "gender": gender
            }
        }
    )

    print()
    print("=" * 50)
    print("👧 CHILD GENDER UPDATE")
    print("=" * 50)

    print(
        f"Matched: {result.matched_count}"
    )

    print(
        f"Modified: {result.modified_count}"
    )

    child = children.find_one(
        {
            "child_id": child_id
        },
        {
            "_id": 0,
            "child_id": 1,
            "name": 1,
            "gender": 1,
        }
    )

    print()
    print("Child:")
    print(child)

    print("=" * 50)


if __name__ == "__main__":

    try:
        main()

    finally:
        close_connection()
