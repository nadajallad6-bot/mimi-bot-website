import json
import random
import re
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RIDDLES_FILE = PROJECT_ROOT / "data" / "riddles" / "riddles.json"

def normalize_arabic(text):
    text = str(text or "").strip().lower()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    for old, new in {"أ":"ا","إ":"ا","آ":"ا","ى":"ي","ة":"ه","ؤ":"و","ئ":"ي"}.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return " ".join(text.split())

class RiddleModule:
    """جلسة ألغاز قصيرة وطفولية: 3 ألغاز، تلميحات، مستويات، ومنع تكرار."""

    def __init__(self, voice_module=None):
        self.voice = voice_module
        self.started = False
        self.riddles = []
        self.settings = {}
        self.active = False
        self.current_riddle = None
        self.attempts = 0
        self.round_number = 0
        self.round_correct = 0
        self.round_points = 0
        self.level = "easy"
        self.recent_ids = deque(maxlen=5)
        self.load_riddles()

    def load_riddles(self):
        with open(RIDDLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.settings = data.get("settings", {})
        self.riddles = data.get("riddles", [])
        self.recent_ids = deque(maxlen=int(self.settings.get("recent_memory", 5)))
        self.level = self.settings.get("start_level", "easy")
        print(f"🧩 Loaded {len(self.riddles)} friendly riddles.")

    def start_module(self):
        if self.started:
            return
        self.started = True
        print("✅ Friendly Riddle Module ready.")

    def set_voice(self, voice_module):
        self.voice = voice_module

    def say(self, text, resume_listening=True):
        text = str(text or "").strip()
        if not text:
            return False
        print(f"\n🤖 Mimi Riddle: {text}")
        if self.voice is None:
            return True
        try:
            result = self.voice.say(text, resume_listening=resume_listening)
            return True if result is None else bool(result)
        except TypeError:
            self.voice.say(text)
            return True

    def _round_size(self):
        return max(1, int(self.settings.get("round_size", 3)))

    def _pick_riddle(self):
        # نبدأ بالسهل. إذا الطفل ممتاز نسمح بالـmedium.
        allowed_levels = ["easy"] if self.level == "easy" else ["easy", "medium"]
        choices = [
            r for r in self.riddles
            if r.get("level", "easy") in allowed_levels
            and r.get("id") not in self.recent_ids
        ]
        if not choices:
            choices = [r for r in self.riddles if r.get("level", "easy") in allowed_levels]
        return random.choice(choices) if choices else None

    def _question_intro(self):
        if self.round_number == 0:
            return random.choice([
                "يلااا! نلعب ثلاث ألغاز صغار! جاهز؟ ",
                "عندي تحدي لطيف إلك! ثلاث ألغاز وبنشوف كم نجمة بتجمع! ",
                "أوووه! وقت الألغاز! ركّز معي يا شاطر! ",
            ])
        return random.choice([
            "حلووو! اسمع اللي بعده. ",
            "طيب طيب، هاد بده شوية تركيز! ",
            "جاهز لواحد كمان؟ يلا! ",
            "هسا دوري أحاول أحيّرك شوي! ",
        ])

    def _ask_new(self):
        riddle = self._pick_riddle()
        if not riddle:
            self.active = False
            return {"finished": True, "correct": False, "points": self.round_points}
        self.current_riddle = riddle
        self.attempts = 0
        self.recent_ids.append(riddle.get("id"))
        self.say(self._question_intro() + riddle.get("question", ""), resume_listening=True)
        return {"started": True, "finished": False, "question": riddle.get("question", "")}

    def start(self):
        if not self.started:
            self.start_module()
        if self.active:
            return False
        self.active = True
        self.round_number = 0
        self.round_correct = 0
        self.round_points = 0
        self.level = self.settings.get("start_level", "easy")
        return self._ask_new()

    def _matches(self, child_answer):
        child = normalize_arabic(child_answer)
        for ans in self.current_riddle.get("answers", []):
            a = normalize_arabic(ans)
            if a and (child == a or a in child):
                return True
        return False

    def _finish_or_next(self, was_correct):
        self.round_number += 1

        # بعد إجابتين صح، نعطي الطفل تحدي أصعب بدون وصفه بأنه "مستوى".
        if self.round_correct >= 2:
            self.level = "medium"

        if self.round_number >= self._round_size():
            stars = self.round_correct
            if stars == 3:
                closing = "واااو! ثلاث من ثلاث! إنت بطل الألغاز! ثلاث نجمات إلك!"
            elif stars == 2:
                closing = "ييي ممتاز! جمعت نجمتين! لعبك كان حلو كتير!"
            elif stars == 1:
                closing = "حلووو! جمعت نجمة! المرة الجاية منجمع أكتر!"
            else:
                closing = "خلصت الجولة! أهم إشي إننا لعبنا وتعلمنا. المرة الجاية رح نكسر الدنيا!"
            self.say(closing, resume_listening=False)
            points = self.round_points
            self.active = False
            self.current_riddle = None
            return {
                "handled": True, "correct": was_correct, "points": points,
                "finished": True, "round_correct": self.round_correct
            }

        self.say(random.choice([
            "يلا نروح عاللغز اللي بعده!",
            "مستعد لواحد كمان؟",
            "حلو! لسا عندي لغز إلك!",
        ]), resume_listening=False)
        result = self._ask_new()
        result.update({"handled": True, "correct": was_correct, "points": 0})
        return result

    def answer(self, child_answer):
        if not self.active or self.current_riddle is None:
            return {"handled": False, "correct": False, "points": 0, "finished": True}

        child_answer = str(child_answer or "").strip()
        if not child_answer:
            self.say("هممم، ما سمعتك منيح. احكيلي جوابك كمان مرة.", resume_listening=True)
            return {"handled": True, "correct": False, "points": 0, "finished": False}

        self.attempts += 1

        if self._matches(child_answer):
            self.round_correct += 1
            gained = int(self.current_riddle.get("points", 5) or 5)
            self.round_points += gained
            self.say(random.choice(self.current_riddle.get("success", ["ييي شاطر!"])),
                     resume_listening=False)
            return self._finish_or_next(True)

        if self.attempts == 1:
            hints = self.current_riddle.get("hints", [])
            hint = random.choice(hints) if hints else "فكر شوي كمان!"
            self.say(random.choice([
                "هممم... قريبة! بدي أعطيك سر صغير. ",
                "أوووه، محاولة حلوة! اسمع هالتلميح. ",
                "مش رح أحكيلك الجواب! بعطيك تلميح صغير. ",
            ]) + hint, resume_listening=True)
            return {
                "handled": True, "correct": False, "points": 0,
                "finished": False, "retry": True
            }

        self.say(self.current_riddle.get(
            "reveal", "ولا يهمك! هسا عرفنا الجواب."
        ), resume_listening=False)
        return self._finish_or_next(False)

    def is_active(self):
        return bool(self.active)

    def get_state(self):
        return {
            "active": self.active, "round_number": self.round_number,
            "round_correct": self.round_correct, "round_points": self.round_points,
            "level": self.level,
            "riddle_id": self.current_riddle.get("id") if self.current_riddle else None,
        }

    def reset(self):
        self.active = False
        self.current_riddle = None
        self.attempts = 0
        self.round_number = 0
        self.round_correct = 0
        self.round_points = 0

    def close(self):
        self.reset()
        self.started = False
