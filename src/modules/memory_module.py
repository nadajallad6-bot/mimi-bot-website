from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid

from pathlib import Path


# =========================================================
# Mimi Bot Memory Module
# =========================================================
#
# Architecture inspired by:
# Pollen Robotics - Reachy Mini Conversation App
#
# Rewritten and adapted specifically for Mimi Bot.
#
# Memory is LOCAL and separated by child_id.
# =========================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MEMORY_ROOT = (
    PROJECT_ROOT
    / "data"
    / "private"
    / "memory"
)


MAX_FACTS_PER_CHILD = 60

MAX_FACT_LENGTH = 280


# Thread-safe file operations
_MEMORY_LOCK = threading.Lock()


# =========================================================
# Helpers
# =========================================================

def normalize_text(
    text: str,
) -> str:
    """
    تنظيف المعلومة قبل تخزينها.
    """

    if text is None:
        return ""

    text = str(
        text
    ).strip()

    # إزالة المسافات الزائدة
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    if len(text) > MAX_FACT_LENGTH:

        text = (
            text[
                : MAX_FACT_LENGTH - 3
            ]
            + "..."
        )

    return text


# =========================================================
# Current Time
# =========================================================

def current_time_ms() -> int:

    return int(
        time.time()
        * 1000
    )


# =========================================================
# Generate ID
# =========================================================

def generate_memory_id() -> str:

    short_id = (
        uuid.uuid4()
        .hex[:8]
    )

    timestamp = (
        current_time_ms()
    )

    return (
        f"mem_{timestamp}_{short_id}"
    )


# =========================================================
# Memory Module
# =========================================================

class MemoryModule:
    """
    Long-term memory for Mimi Bot.

    مثال:

        memory.remember(
            child_id="test_child_001",
            text="سارة بتحب اللون البنفسجي"
        )

        memory.list_memories(
            "test_child_001"
        )

        memory.forget(
            child_id="test_child_001",
            query="بنفسجي"
        )

    كل طفل له ملف ذاكرة مستقل.
    """

    def __init__(
        self,
        memory_root=None,
    ):

        if memory_root is None:

            self.memory_root = (
                MEMORY_ROOT
            )

        else:

            self.memory_root = Path(
                memory_root
            )

        self.memory_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        print()
        print("=" * 60)
        print("🧠 MEMORY MODULE")
        print("=" * 60)

        print(
            f"📁 Memory path: "
            f"{self.memory_root}"
        )

        print(
            "✅ Memory Module ready."
        )

        print("=" * 60)

    # =====================================================
    # Child Memory File
    # =====================================================

    def _get_child_file(
        self,
        child_id: str,
    ) -> Path:

        child_id = str(
            child_id
        ).strip()

        # منع أحرف ممكن تسبب مشاكل بالمسار
        safe_child_id = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            child_id,
        )

        return (
            self.memory_root
            / f"{safe_child_id}.json"
        )

    # =====================================================
    # Empty Memory
    # =====================================================

    def _empty_memory(
        self,
        child_id,
    ):

        return {
            "version": 1,

            "child_id":
                child_id,

            "facts": [],
        }

    # =====================================================
    # Read File
    # =====================================================

    def _read(
        self,
        child_id,
    ):

        path = (
            self._get_child_file(
                child_id
            )
        )

        if not path.exists():

            return (
                self._empty_memory(
                    child_id
                )
            )

        try:

            text = (
                path.read_text(
                    encoding="utf-8"
                )
            )

            data = json.loads(
                text
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:

            print()
            print(
                "⚠️ Memory read error:"
            )

            print(
                error
            )

            return (
                self._empty_memory(
                    child_id
                )
            )

        # -------------------------------------------------
        # Validate
        # -------------------------------------------------

        if not isinstance(
            data,
            dict,
        ):

            return (
                self._empty_memory(
                    child_id
                )
            )

        facts = data.get(
            "facts",
            [],
        )

        if not isinstance(
            facts,
            list,
        ):

            facts = []

        data["facts"] = (
            facts[
                :MAX_FACTS_PER_CHILD
            ]
        )

        return data

    # =====================================================
    # Atomic Write
    # =====================================================

    def _write(
        self,
        child_id,
        data,
    ):

        path = (
            self._get_child_file(
                child_id
            )
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            path.with_suffix(
                ".tmp"
            )
        )

        payload = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )

        try:

            temporary_path.write_text(
                payload,
                encoding="utf-8",
            )

            # Atomic-ish replacement
            os.replace(
                temporary_path,
                path,
            )

        finally:

            try:

                temporary_path.unlink(
                    missing_ok=True
                )

            except OSError:

                pass

    # =====================================================
    # Remember
    # =====================================================

    def remember(
        self,
        child_id: str,
        text: str,
    ):
        """
        تخزين معلومة طويلة المدى عن الطفل.

        لا يخزن نفس المعلومة مرتين.
        """

        normalized = (
            normalize_text(
                text
            )
        )

        if not normalized:

            return {
                "saved": False,
                "reason": "empty",
            }

        with _MEMORY_LOCK:

            data = (
                self._read(
                    child_id
                )
            )

            facts = data.get(
                "facts",
                [],
            )

            # ---------------------------------------------
            # Duplicate Check
            # ---------------------------------------------

            for fact in facts:

                old_text = (
                    normalize_text(
                        fact.get(
                            "text",
                            "",
                        )
                    )
                )

                if (
                    old_text.lower()
                    == normalized.lower()
                ):

                    print(
                        "🧠 Memory already exists."
                    )

                    return {
                        "saved": False,
                        "reason": "duplicate",
                        "memory": fact,
                    }

            # ---------------------------------------------
            # Create memory
            # ---------------------------------------------

            memory = {
                "memory_id":
                    generate_memory_id(),

                "text":
                    normalized,

                "created_at":
                    current_time_ms(),
            }

            # Newest first
            facts.insert(
                0,
                memory,
            )

            facts = (
                facts[
                    :MAX_FACTS_PER_CHILD
                ]
            )

            data["facts"] = (
                facts
            )

            data["child_id"] = (
                child_id
            )

            self._write(
                child_id,
                data,
            )

        print()
        print(
            f"🧠 Remembered: "
            f"{normalized}"
        )

        return {
            "saved": True,
            "memory": memory,
        }

    # =====================================================
    # List Memories
    # =====================================================

    def list_memories(
        self,
        child_id: str,
    ):

        with _MEMORY_LOCK:

            data = (
                self._read(
                    child_id
                )
            )

        return list(
            data.get(
                "facts",
                [],
            )
        )

    # =====================================================
    # Count Memories
    # =====================================================

    def count(
        self,
        child_id: str,
    ) -> int:

        return len(
            self.list_memories(
                child_id
            )
        )

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        child_id: str,
        query: str,
    ):

        query = (
            normalize_text(
                query
            ).lower()
        )

        if not query:

            return []

        results = []

        memories = (
            self.list_memories(
                child_id
            )
        )

        for memory in memories:

            text = str(
                memory.get(
                    "text",
                    "",
                )
            )

            if (
                query
                in text.lower()
            ):

                results.append(
                    memory
                )

        return results

    # =====================================================
    # Forget
    # =====================================================

    def forget(
        self,
        child_id: str,
        query: str,
    ):
        """
        حذف أول معلومة تطابق البحث.
        """

        query = (
            normalize_text(
                query
            ).lower()
        )

        if not query:

            return {
                "removed": False,
                "reason": "empty_query",
            }

        with _MEMORY_LOCK:

            data = (
                self._read(
                    child_id
                )
            )

            facts = data.get(
                "facts",
                [],
            )

            matched = []

            for memory in facts:

                text = str(
                    memory.get(
                        "text",
                        "",
                    )
                ).lower()

                if query in text:

                    matched.append(
                        memory
                    )

            if not matched:

                return {
                    "removed": False,
                    "reason": "not_found",
                }

            memory_to_remove = (
                matched[0]
            )

            memory_id = (
                memory_to_remove.get(
                    "memory_id"
                )
            )

            data["facts"] = [
                memory
                for memory in facts
                if memory.get(
                    "memory_id"
                )
                != memory_id
            ]

            self._write(
                child_id,
                data,
            )

        print()
        print(
            "🧠 Forgot memory:"
        )

        print(
            memory_to_remove.get(
                "text"
            )
        )

        return {
            "removed": True,

            "memory":
                memory_to_remove,

            "matches":
                matched,
        }

    # =====================================================
    # Clear Child Memory
    # =====================================================

    def clear(
        self,
        child_id: str,
    ):

        with _MEMORY_LOCK:

            data = (
                self._empty_memory(
                    child_id
                )
            )

            self._write(
                child_id,
                data,
            )

        print()
        print(
            f"🧠 Cleared memory "
            f"for {child_id}"
        )

    # =====================================================
    # Context For AI
    # =====================================================

    def get_context(
        self,
        child_id: str,
        limit=15,
    ) -> str:
        """
        هذا الجزء مهم جدًا لاحقًا.

        يعطي الـAI معلومات الطفل
        بدون ما يقرأ ملفات أو يعرف MongoDB.
        """

        memories = (
            self.list_memories(
                child_id
            )
        )

        memories = (
            memories[:limit]
        )

        if not memories:

            return ""

        lines = []

        for memory in memories:

            text = (
                memory.get(
                    "text",
                    ""
                )
            )

            if text:

                lines.append(
                    f"- {text}"
                )

        if not lines:

            return ""

        return (
            "معلومات تتذكرها ميمي "
            "عن الطفل:\n"
            + "\n".join(
                lines
            )
        )

    # =====================================================
    # Close
    # =====================================================

    def close(self):

        print(
            "✅ Memory Module closed."
        )


# =========================================================
# Standalone Test
# =========================================================

def test_memory_module():

    memory = (
        MemoryModule()
    )

    child_id = (
        "test_child_001"
    )

    print()
    print("=" * 60)
    print("🧠 MIMI MEMORY TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # Add
    # -----------------------------------------------------

    result = memory.remember(
        child_id,
        "سارة بتحب اللون البنفسجي",
    )

    print()
    print(
        "Remember result:"
    )

    print(
        result
    )

    # -----------------------------------------------------
    # Another memory
    # -----------------------------------------------------

    memory.remember(
        child_id,
        "سارة بتحب قصص الحيوانات",
    )

    # -----------------------------------------------------
    # Duplicate test
    # -----------------------------------------------------

    memory.remember(
        child_id,
        "سارة بتحب قصص الحيوانات",
    )

    # -----------------------------------------------------
    # List
    # -----------------------------------------------------

    print()
    print("All memories:")

    for item in (
        memory.list_memories(
            child_id
        )
    ):

        print(
            "•",
            item["text"],
        )

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    print()
    print(
        "Search for قصص:"
    )

    results = (
        memory.search(
            child_id,
            "قصص",
        )
    )

    for item in results:

        print(
            "🔎",
            item["text"],
        )

    # -----------------------------------------------------
    # AI Context
    # -----------------------------------------------------

    print()
    print(
        "Context:"
    )

    print(
        memory.get_context(
            child_id
        )
    )

    print()
    print(
        f"🧠 Total memories: "
        f"{memory.count(child_id)}"
    )


# =========================================================
# RUN TEST
# =========================================================

if __name__ == "__main__":

    test_memory_module()
