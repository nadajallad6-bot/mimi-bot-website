import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError


# المسار الرئيسي لمشروع Mimi Bot
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# تحميل البيانات السرية من ملف .env
load_dotenv(PROJECT_ROOT / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mimi_bot")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """إنشاء وإرجاع اتصال MongoDB واحد."""

    global _client

    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is missing from the .env file")

    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=15000,
        )

    return _client


def get_database() -> Database:
    """إرجاع قاعدة بيانات Mimi Bot."""

    return get_client()[MONGODB_DB_NAME]


def test_connection() -> bool:
    """اختبار الاتصال مع MongoDB Atlas."""

    try:
        result = get_client().admin.command("ping")

        if result.get("ok") == 1:
            print("✅ Mimi Bot connected successfully to MongoDB Atlas")
            print(f"✅ Database name: {MONGODB_DB_NAME}")
            return True

        print("❌ MongoDB returned an unexpected response")
        return False

    except PyMongoError as error:
        print("❌ MongoDB connection failed:")
        print(error)
        return False


def close_connection() -> None:
    """إغلاق الاتصال عند انتهاء البرنامج."""

    global _client

    if _client is not None:
        _client.close()
        _client = None


if __name__ == "__main__":
    test_connection()
    close_connection()
