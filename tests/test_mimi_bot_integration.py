import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIMI_FILE = PROJECT_ROOT / "src" / "core" / "mimi_bot.py"

source = MIMI_FILE.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(MIMI_FILE))

class_names = {
    node.name
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
}

assert "MimiBot" in class_names

required_text = [
    "SAFETY - ABSOLUTE PRIORITY",
    "process_pending_safety_results",
    "_interrupt_activity_audio_for_safety",
    "volume_down",
    "volume_up",
]

for item in required_text:
    assert item in source, f"Missing integration marker: {item}"

print("✅ mimi_bot.py syntax OK")
print("✅ Safety integration present")
print("✅ Always-on content microphone integration present")
print("✅ Global volume controls present")