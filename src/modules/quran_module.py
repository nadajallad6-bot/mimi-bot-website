import re
from pathlib import Path

from src.modules.quran_audio_player import QuranAudioPlayer
from src.modules.quran_evaluator import (
    QuranEvaluator,
    compare_words,
    normalize_arabic,
    remove_leading_basmala_words,
)

try:
    from src.voice import listener as voice_listener
except Exception:
    voice_listener = None

from src.database.quran_catalog import (
    get_surah as get_catalog_surah,
)

from src.database.quran_progress_store import (
    save_mastered_ayah,
    get_next_ayah,
    get_surah_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

QURAN_AUDIO_DIR = (
    PROJECT_ROOT
    / "data"
    / "quran"
    / "audio"
)


# =========================================================
# Memorization Strategy
# =========================================================

DEFAULT_RECITER_REPEATS = 3
CHILD_SUCCESS_TARGET = 1

SMALL_SURAH_MAX_AYAHS = 10

MEDIUM_SURAH_MAX_AYAHS = 40
MEDIUM_SECTION_MAX_AYAHS = 3
MEDIUM_SECTION_MAX_WORDS = 30

LARGE_SECTION_MAX_AYAHS = 2
LARGE_SECTION_MAX_WORDS = 24


# =========================================================
# Quran Surah Names - 114 Surahs
# =========================================================

SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة",
    "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل",
    "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج",
    "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل",
    "القصص", "العنكبوت", "الروم", "لقمان", "السجدة",
    "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص",
    "الزمر", "غافر", "فصلت", "الشورى", "الزخرف", "الدخان",
    "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن",
    "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق",
    "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان",
    "المرسلات", "النبأ", "النازعات", "عبس", "التكوير",
    "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق",
    "الأعلى", "الغاشية", "الفجر", "البلد", "الشمس", "الليل",
    "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة",
    "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر",
    "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر",
    "الكافرون", "النصر", "المسد", "الإخلاص", "الفلق", "الناس",
]


_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)


def normalize_surah_request(text):

    text = str(text or "").strip().lower()
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")

    text = text.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ة": "ه",
                "ؤ": "و",
                "ئ": "ي",
            }
        )
    )

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


SURAH_NAME_INDEX = {
    normalize_surah_request(name): number
    for number, name in enumerate(
        SURAH_NAMES,
        start=1,
    )
}

SURAH_NAME_INDEX.update(
    {
        normalize_surah_request("بني إسرائيل"): 17,
        normalize_surah_request("المؤمن"): 40,
        normalize_surah_request("حم المؤمن"): 40,
        normalize_surah_request("ألم نشرح"): 94,
        normalize_surah_request("التوحيد"): 112,
        normalize_surah_request("تبت"): 111,
    }
)


# =========================================================
# Quran Barge-In Commands
# =========================================================

QURAN_BARGE_PROFILE = {
    "start_timeout": 8.0,
    "end_silence": 0.45,
    "max_speech": 3.5,
}

QURAN_STOP_COMMANDS = {
    normalize_surah_request("وقف"),
    normalize_surah_request("وقفي"),
    normalize_surah_request("توقف"),
    normalize_surah_request("توقفي"),
    normalize_surah_request("اسكت"),
    normalize_surah_request("اسكتي"),
    normalize_surah_request("خلص"),
    normalize_surah_request("بس"),
    normalize_surah_request("ميمي وقف"),
    normalize_surah_request("ميمي وقفي"),
    normalize_surah_request("ميمي توقفي"),
    normalize_surah_request("ميمي اسكتي"),
}

QURAN_VOLUME_DOWN_COMMANDS = {
    normalize_surah_request("وطي الصوت"),
    normalize_surah_request("وطي صوتك"),
    normalize_surah_request("وطي شوي"),
    normalize_surah_request("خفض الصوت"),
    normalize_surah_request("خفضي الصوت"),
    normalize_surah_request("قلل الصوت"),
    normalize_surah_request("قللي الصوت"),
    normalize_surah_request("نزل الصوت"),
    normalize_surah_request("نزلي الصوت"),
    normalize_surah_request("ميمي وطي الصوت"),
    normalize_surah_request("ميمي وطي صوتك"),
}

QURAN_VOLUME_UP_COMMANDS = {
    normalize_surah_request("علي الصوت"),
    normalize_surah_request("علي صوتك"),
    normalize_surah_request("علي شوي"),
    normalize_surah_request("ارفع الصوت"),
    normalize_surah_request("ارفعي الصوت"),
    normalize_surah_request("زيد الصوت"),
    normalize_surah_request("زيدي الصوت"),
    normalize_surah_request("ميمي علي الصوت"),
    normalize_surah_request("ميمي علي صوتك"),
}


class QuranModule:
    """
    Reading mode:
        Each ayah is played once.

    Memorization mode:
        Current ayah -> reciter x3 -> child recites once.
        If child score < threshold -> same ayah x3 again.

    Section review:
        Small surahs: review two ayahs together.
        Medium/large surahs: adaptive short sections.
        Section -> reciter x3 -> child recites section once.

    Progress is saved after the section review passes.
    """

    def __init__(
        self,
        voice_module=None,
        child_id=None,
        reader="alafasy",
        repeat_target=DEFAULT_RECITER_REPEATS,
        pass_threshold=85.0,
    ):

        self.voice = voice_module
        self.child_id = child_id

        self.reader = "alafasy"

        if str(reader).strip().lower() != "alafasy":
            print()
            print(
                "⚠️ Current on-demand Quran cache supports "
                "Alafasy only. Using alafasy."
            )

        self.player = QuranAudioPlayer(
            volume=60
        )

        self.evaluator = QuranEvaluator(
            pass_threshold=pass_threshold
        )

        self.repeat_target = max(
            1,
            int(repeat_target),
        )

        self.child_success_target = (
            CHILD_SUCCESS_TARGET
        )

        self.started = False
        self.mode = None
        self.surah_number = None
        self.surah_name = None

        self.waiting_for_surah = False
        self.waiting_for_child = False

        self.current_ayah = 1
        self.current_repeat = 0
        self.current_attempts = 0
        self.last_score = 0.0

        self.memorization_stage = None
        self.sections = []
        self.section_index = 0
        self.section_learn_ayahs = []
        self.section_review_start = None
        self.section_review_end = None
        self.section_position = 0
        self.review_attempts = 0

        self.pending_progress = {}

        self.quran_stop_requested = False
        self.last_control_command = None
        self._saved_audio_listener_profile = None
        self._saved_audio_listener_values = None

    # =====================================================
    # Start
    # =====================================================

    def start_module(self):

        if self.started:
            return

        print()
        print("=" * 60)
        print("📖 STARTING QURAN MODULE")
        print("=" * 60)

        QURAN_AUDIO_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.player.detect_speaker()
        self.evaluator.start()

        self.started = True

        print(
            f"🎙️ Reader: {self.reader}"
        )
        print(
            f"🔁 Memorization reciter repeats: "
            f"{self.repeat_target}"
        )
        print(
            f"👦 Correct child recitations required: "
            f"{self.child_success_target}"
        )
        print(
            f"🎯 Pass threshold: "
            f"{self.evaluator.pass_threshold:.0f}%"
        )
        print(
            "✅ Quran Module ready for 114 Surahs."
        )
        print("=" * 60)

    # =====================================================
    # Child / Voice
    # =====================================================

    def set_voice(self, voice_module):
        self.voice = voice_module

    def set_child(self, child_id):

        if child_id is None:
            self.child_id = None
            print()
            print("👤 Quran Module: Guest mode")
            return

        child_id = str(child_id).strip()

        if not child_id:
            self.child_id = None
            return

        self.child_id = child_id

        print()
        print(
            f"👧 Quran child: {self.child_id}"
        )

    def clear_child(self):

        self.child_id = None
        self.reset()

        print()
        print("👤 Quran child cleared.")

    def say(
        self,
        text,
        resume_listening=True,
    ):

        text = str(text or "").strip()

        if not text:
            return False

        if self.voice is not None:
            try:
                result = self.voice.say(
                    text,
                    resume_listening=resume_listening,
                )
            except TypeError:
                result = self.voice.say(text)

            if getattr(
                self.voice,
                "last_barge_command",
                None,
            ) == "stop":
                self.quran_stop_requested = True
                self.last_control_command = "stop"

            return (
                True
                if result is None
                else bool(result)
            )

        print()
        print(
            f"🤖 Mimi: {text}"
        )

        return True

    def stop_microphone(self):

        if self.voice is None:
            return

        try:
            self.voice.pause_and_wait()
        except Exception:
            try:
                self.voice.disable()
            except Exception:
                pass

        try:
            self.voice.clear_commands()
        except Exception:
            pass

    def resume_microphone(self):

        if self.voice is None:
            return

        try:
            self.voice.clear_commands()
        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception as error:
            print(
                "⚠️ Microphone resume error:",
                error,
            )

    # =====================================================
    # Quran Audio Barge-In
    # =====================================================

    def _save_audio_listener_profile(self):

        if self.voice is None:
            return

        listener = getattr(
            self.voice,
            "listener",
            None,
        )

        if listener is None:
            return

        self._saved_audio_listener_profile = getattr(
            listener,
            "current_profile",
            None,
        )

        values = getattr(
            listener,
            "profile_values",
            None,
        )

        self._saved_audio_listener_values = (
            dict(values)
            if isinstance(values, dict)
            else None
        )

    def _enable_quran_audio_barge_in(self):

        if self.voice is None:
            return

        self._save_audio_listener_profile()

        try:
            self.voice.clear_commands()
        except Exception:
            pass

        try:
            setter = getattr(
                self.voice,
                "set_listening_profile",
                None,
            )

            if callable(setter):
                setter(
                    "quran_barge_in",
                    dict(
                        QURAN_BARGE_PROFILE
                    ),
                )
        except Exception:
            pass

        try:
            self.voice.enable()
        except Exception as error:
            print(
                "⚠️ Quran microphone enable error:",
                error,
            )

    def _restore_quran_audio_profile(self):

        if self.voice is None:
            return

        if self._saved_audio_listener_profile:
            try:
                setter = getattr(
                    self.voice,
                    "set_listening_profile",
                    None,
                )

                if callable(setter):
                    setter(
                        self._saved_audio_listener_profile,
                        self._saved_audio_listener_values or {},
                    )
            except Exception:
                pass

        self._saved_audio_listener_profile = None
        self._saved_audio_listener_values = None

    def _poll_quran_control(self):

        if self.voice is None:
            return None

        try:
            text = self.voice.get_command()
        except Exception:
            text = None

        if not text:
            return None

        normalized = normalize_surah_request(
            text
        )

        if normalized in QURAN_STOP_COMMANDS:

            self.quran_stop_requested = True
            self.last_control_command = "stop"

            print()
            print(
                f"🛑 Quran command: {text}"
            )

            return "stop"

        if normalized in QURAN_VOLUME_DOWN_COMMANDS:

            self.last_control_command = "volume_down"

            print()
            print(
                f"🔉 Quran command: {text}"
            )

            try:
                self.player.lower_volume(
                    step=15
                )
            except Exception:
                pass

            try:
                lower = getattr(
                    self.voice,
                    "lower_volume",
                    None,
                )

                if callable(lower):
                    lower(
                        step=15
                    )
            except Exception:
                pass

            return None

        if normalized in QURAN_VOLUME_UP_COMMANDS:

            self.last_control_command = "volume_up"

            print()
            print(
                f"🔊 Quran command: {text}"
            )

            try:
                self.player.raise_volume(
                    step=15
                )
            except Exception:
                pass

            try:
                raise_volume = getattr(
                    self.voice,
                    "raise_volume",
                    None,
                )

                if callable(
                    raise_volume
                ):
                    raise_volume(
                        step=15
                    )
            except Exception:
                pass

            return None

        # Ignore ordinary speech during reciter playback for now.
        return None

    def _finish_quran_stop(self):

        stopped_surah = self.surah_name

        try:
            self.player.stop()
        except Exception:
            pass

        self.reset()

        self.quran_stop_requested = True
        self.last_control_command = "stop"

        self.resume_microphone()

        print()
        print(
            "🛑 Quran session stopped by child."
        )

        return {
            "handled": True,
            "started": False,
            "stopped": True,
            "surah_name":
                stopped_surah,
        }

    # =====================================================
    # Quran Adaptive Listening Time
    # =====================================================

    def set_quran_listening_time(
        self,
        start_ayah,
        end_ayah=None,
    ):
        """
        يوسّع وقت التسجيل تلقائيًا حسب كمية التسميع.

        آية واحدة:
            الوقت يعتمد على عدد كلمات الآية.

        ربط أكثر من آية:
            2 آيات  -> حتى 20 ثانية
            3 آيات  -> حتى 30 ثانية
            4 آيات  -> حتى 40 ثانية
            5+ آيات -> حتى 55 ثانية

        كما نزيد end_silence قليلًا حتى يستطيع الطفل
        أن يأخذ نفسًا قصيرًا بين الآيات بدون أن ينتهي التسجيل.
        """

        if voice_listener is None:
            return

        try:
            start_ayah = int(start_ayah)
            end_ayah = int(
                end_ayah
                if end_ayah is not None
                else start_ayah
            )
        except Exception:
            return

        ayah_count = max(
            1,
            end_ayah - start_ayah + 1,
        )

        total_words = 0

        for ayah_number in range(
            start_ayah,
            end_ayah + 1,
        ):
            try:
                total_words += self.get_ayah_word_count(
                    self.surah_number,
                    ayah_number,
                )
            except Exception:
                pass

        # آية واحدة: يعتمد الوقت على طول الآية نفسها.
        if ayah_count == 1:

            if total_words <= 8:
                profile_name = "quran_1_ayah"
                values = {
                    "start_timeout": 8.0,
                    "end_silence": 1.20,
                    "max_speech": 16.0,
                }

            elif total_words <= 18:
                profile_name = "quran_1_ayah_medium"
                values = {
                    "start_timeout": 10.0,
                    "end_silence": 1.35,
                    "max_speech": 28.0,
                }

            else:
                profile_name = "quran_1_ayah_long"
                values = {
                    "start_timeout": 12.0,
                    "end_silence": 1.60,
                    "max_speech": 50.0,
                }

        # ربط آيتين.
        elif ayah_count == 2:
            profile_name = "quran_2_ayahs"
            values = {
                "start_timeout": 10.0,
                "end_silence": 1.50,
                "max_speech": 20.0,
            }

        # ربط 3 آيات.
        elif ayah_count == 3:
            profile_name = "quran_3_ayahs"
            values = {
                "start_timeout": 11.0,
                "end_silence": 1.60,
                "max_speech": 30.0,
            }

        # ربط 4 آيات.
        elif ayah_count == 4:
            profile_name = "quran_4_ayahs"
            values = {
                "start_timeout": 12.0,
                "end_silence": 1.70,
                "max_speech": 40.0,
            }

        # أي مقطع أكبر.
        else:
            profile_name = (
                f"quran_{ayah_count}_ayahs"
            )
            values = {
                "start_timeout": 12.0,
                "end_silence": 1.80,
                "max_speech": min(
                    55.0,
                    10.0
                    + ayah_count * 9.0,
                ),
            }

        # حماية إضافية للآيات الطويلة جدًا داخل المقطع.
        estimated_from_words = (
            8.0
            + total_words * 1.6
        )

        values["max_speech"] = min(
            60.0,
            max(
                values["max_speech"],
                estimated_from_words,
            ),
        )

        try:
            applied = False

            # IMPORTANT:
            # VoiceLoop stores its own current_profile/profile_values.
            # We must update THAT object, otherwise enable() / _worker()
            # will re-apply its old default "short" profile.
            if (
                self.voice is not None
                and
                hasattr(self.voice, "listener")
                and
                hasattr(
                    self.voice.listener,
                    "set_listening_profile",
                )
            ):
                self.voice.listener.set_listening_profile(
                    profile_name,
                    values,
                )
                applied = True

            # Fallback for older voice implementations.
            elif voice_listener is not None:
                voice_listener.set_listening_profile(
                    profile_name,
                    values,
                )
                applied = True

            if applied:
                print()
                print(
                    f"🎤 Quran listening: "
                    f"{ayah_count} ayah(s), "
                    f"{total_words} words -> "
                    f"max {values['max_speech']:.1f}s"
                )

        except Exception as error:
            print(
                "⚠️ Quran listening profile error:",
                error,
            )

    # =====================================================
    # Reader / Surah
    # =====================================================

    def set_reader(self, reader):

        reader = str(reader).strip().lower()

        if not reader:
            return False

        if reader != "alafasy":
            print()
            print(
                "⚠️ Reader not available in the current "
                "on-demand cache yet."
            )
            return False

        self.reader = "alafasy"

        print(
            "🎙️ Quran reader: alafasy"
        )

        return True

    def detect_surah(self, text):

        normalized = normalize_surah_request(
            text
        )

        if not normalized:
            return None

        for item in re.findall(
            r"\d{1,3}",
            normalized,
        ):

            try:
                number = int(item)
            except Exception:
                continue

            if 1 <= number <= 114:
                return number

        exact = normalized

        if exact.startswith("سوره "):
            exact = exact[5:].strip()

        if exact == "ص":
            return 38

        if exact == "ق":
            return 50

        padded = f" {normalized} "

        ordered_names = sorted(
            SURAH_NAME_INDEX.items(),
            key=lambda item: len(
                item[0]
            ),
            reverse=True,
        )

        for normalized_name, number in ordered_names:

            if normalized_name in {
                "ص",
                "ق",
            }:
                continue

            if (
                f" {normalized_name} "
                in padded
            ):
                return number

        return None

    def get_surah(self, surah_number):

        try:
            surah_number = int(
                surah_number
            )
        except Exception:
            return None

        if not 1 <= surah_number <= 114:
            return None

        try:
            catalog = get_catalog_surah(
                surah_number
            )
        except Exception as error:
            print()
            print("⚠️ Quran catalog error:")
            print(error)
            return None

        if catalog is None:
            return None

        try:
            ayah_count = int(
                catalog.get(
                    "ayah_count",
                    0,
                )
                or 0
            )
        except Exception:
            ayah_count = 0

        if ayah_count <= 0:
            return None

        canonical_name = (
            SURAH_NAMES[
                surah_number - 1
            ]
        )

        return {
            "number": surah_number,
            "name":
                f"سورة {canonical_name}",
            "short_name":
                canonical_name,
            "ayah_count":
                ayah_count,
            "catalog":
                catalog,
        }

    # =====================================================
    # Audio
    # =====================================================

    def get_surah_folder(
        self,
        surah_number,
    ):

        return (
            QURAN_AUDIO_DIR
            / self.reader
            / f"{int(surah_number):03d}"
        )

    def get_ayah_audio_path(
        self,
        surah_number,
        ayah_number,
    ):

        return (
            self.get_surah_folder(
                surah_number
            )
            / f"{int(ayah_number):03d}.mp3"
        )

    def get_basmala_path(
        self,
        surah_number,
    ):

        return (
            self.get_surah_folder(
                surah_number
            )
            / "000.mp3"
        )

    def play_audio(
        self,
        audio_path,
        resume_after=False,
    ):

        self._enable_quran_audio_barge_in()
        success = False

        try:
            success = self.player.play(
                audio_path,
                control_callback=
                    self._poll_quran_control,
            )
        finally:
            self._restore_quran_audio_profile()

            if resume_after:
                self.resume_microphone()

        return success

    def play_ayah_audio(
        self,
        surah_number,
        ayah_number,
        resume_after=False,
        prefetch=True,
    ):

        self._enable_quran_audio_barge_in()
        success = False

        try:
            success = self.player.play_ayah(
                surah_number,
                ayah_number,
                prefetch=prefetch,
                control_callback=
                    self._poll_quran_control,
            )
        finally:
            self._restore_quran_audio_profile()

            if resume_after:
                self.resume_microphone()

        return success

    def check_surah_audio(
        self,
        surah_number,
    ):

        surah = self.get_surah(
            surah_number
        )

        if surah is None:
            return False, []

        missing = []

        for ayah_number in range(
            1,
            surah["ayah_count"] + 1,
        ):

            path = self.get_ayah_audio_path(
                surah_number,
                ayah_number,
            )

            if not path.exists():
                missing.append(
                    str(path)
                )

        return (
            len(missing) == 0,
            missing,
        )

    # =====================================================
    # Quran Text / Passage
    # =====================================================

    def get_ayah_text(
        self,
        surah_number,
        ayah_number,
    ):

        return self.evaluator.get_ayah_text(
            surah_number,
            ayah_number,
        )

    def get_ayah_word_count(
        self,
        surah_number,
        ayah_number,
    ):

        text = self.get_ayah_text(
            surah_number,
            ayah_number,
        )

        return len(
            normalize_arabic(
                text or ""
            ).split()
        )

    def get_passage_text(
        self,
        surah_number,
        start_ayah,
        end_ayah,
    ):

        parts = []

        for ayah_number in range(
            int(start_ayah),
            int(end_ayah) + 1,
        ):

            text = self.get_ayah_text(
                surah_number,
                ayah_number,
            )

            if text is None:
                return None

            parts.append(text)

        return " ".join(parts)

    def evaluate_passage(
        self,
        start_ayah,
        end_ayah,
        child_text,
    ):

        expected_text = self.get_passage_text(
            self.surah_number,
            start_ayah,
            end_ayah,
        )

        if expected_text is None:
            return {
                "handled": False,
                "error":
                    "passage_not_found",
            }

        expected_normalized = normalize_arabic(
            expected_text
        )

        child_normalized = normalize_arabic(
            child_text
        )

        expected_words = (
            expected_normalized.split()
        )

        child_words = (
            child_normalized.split()
        )

        # -------------------------------------------------
        # Optional Basmala for linked/reviewed passages
        # -------------------------------------------------
        #
        # If a review starts from Ayah 1, the Basmala is
        # OPTIONAL for the child:
        #
        # - says it      -> ignored for scoring
        # - does not say -> no penalty
        #
        # Al-Fatiha is excluded because its first ayah is
        # treated normally. At-Tawbah has no opening Basmala.
        # -------------------------------------------------

        basmala_removed_expected = False
        basmala_removed_child = False

        try:
            surah_number_int = int(
                self.surah_number
            )
            start_ayah_int = int(
                start_ayah
            )
        except Exception:
            surah_number_int = 0
            start_ayah_int = 0

        if (
            start_ayah_int == 1
            and
            surah_number_int not in {
                1,
                9,
            }
        ):

            (
                expected_words,
                basmala_removed_expected,
            ) = remove_leading_basmala_words(
                expected_words
            )

            (
                child_words,
                basmala_removed_child,
            ) = remove_leading_basmala_words(
                child_words
            )

        basmala_ignored = (
            basmala_removed_expected
            or
            basmala_removed_child
        )

        if not child_words:
            return {
                "handled": True,
                "passed": False,
                "score": 0.0,
                "threshold":
                    self.evaluator.pass_threshold,
                "expected":
                    expected_text,
                "expected_normalized":
                    expected_normalized,
                "heard":
                    child_text,
                "heard_normalized":
                    child_normalized,
                "missing":
                    expected_words,
                "extra": [],
                "substitutions": [],
                "near_matches": [],
                "start_ayah":
                    start_ayah,
                "end_ayah":
                    end_ayah,
                "basmala_ignored":
                    basmala_ignored,
            }

        comparison = compare_words(
            expected_words,
            child_words,
        )

        reference_length = max(
            len(expected_words),
            1,
        )

        score = (
            1.0
            -
            (
                comparison["distance"]
                /
                reference_length
            )
        )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        score_percent = (
            score * 100.0
        )

        return {
            "handled": True,
            "passed":
                score_percent
                >=
                self.evaluator.pass_threshold,
            "score":
                round(
                    score_percent,
                    2,
                ),
            "threshold":
                self.evaluator.pass_threshold,
            "surah_number":
                self.surah_number,
            "start_ayah":
                start_ayah,
            "end_ayah":
                end_ayah,
            "expected":
                expected_text,
            "expected_normalized":
                expected_normalized,
            "heard":
                child_text,
            "heard_normalized":
                child_normalized,
            "missing":
                comparison["missing"],
            "extra":
                comparison["extra"],
            "substitutions":
                comparison[
                    "substitutions"
                ],
            "near_matches":
                comparison.get(
                    "near_matches",
                    [],
                ),
            "basmala_ignored":
                basmala_ignored,
        }

    # =====================================================
    # Progress
    # =====================================================

    def get_resume_ayah(
        self,
        surah_number,
    ):

        surah = self.get_surah(
            surah_number
        )

        if surah is None:
            return 1

        if not self.child_id:
            print()
            print(
                "👤 Guest mode: starting from Ayah 1."
            )
            return 1

        try:
            next_ayah = get_next_ayah(
                child_id=
                    self.child_id,
                surah_number=
                    surah_number,
                ayah_count=
                    surah["ayah_count"],
            )

            print()
            print("📊 Quran progress loaded.")
            print(
                f"➡️ Next Ayah: {next_ayah}"
            )

            return next_ayah

        except Exception as error:
            print()
            print(
                "⚠️ Could not load Quran progress:"
            )
            print(error)
            return 1

    def save_ayah_progress(
        self,
        ayah_number,
        score,
        attempts,
    ):

        if not self.child_id:
            print()
            print(
                "👤 Guest mode: Quran progress not saved."
            )
            return None

        try:
            return save_mastered_ayah(
                child_id=
                    self.child_id,
                surah_number=
                    self.surah_number,
                ayah_number=
                    ayah_number,
                score=
                    score,
                attempts=
                    attempts,
                successful_repetitions=
                    self.child_success_target,
                repeat_target=
                    self.child_success_target,
                pass_threshold=
                    self.evaluator.pass_threshold,
            )

        except Exception as error:
            print()
            print(
                "⚠️ Quran progress could not be saved:"
            )
            print(error)
            return None

    def get_progress_summary(
        self,
        surah_number,
    ):

        if not self.child_id:
            return None

        surah = self.get_surah(
            surah_number
        )

        if surah is None:
            return None

        try:
            return get_surah_summary(
                child_id=
                    self.child_id,
                surah_number=
                    surah_number,
                ayah_count=
                    surah["ayah_count"],
            )

        except Exception as error:
            print(
                "⚠️ Progress summary error:",
                error,
            )
            return None

    # =====================================================
    # Reading Mode
    # =====================================================

    def start_reading(
        self,
        request_text="",
        surah_number=None,
    ):

        if not self.started:
            self.start_module()

        self.quran_stop_requested = False
        self.last_control_command = None

        if surah_number is None:
            surah_number = self.detect_surah(
                request_text
            )

        if surah_number is None:
            self.mode = "read"
            self.waiting_for_surah = True
            self.waiting_for_child = False

            self.say(
                "أكيد. أي سورة بتحب تسمع؟"
            )

            return {
                "started": False,
                "needs_surah": True,
            }

        surah = self.get_surah(
            surah_number
        )

        if surah is None:
            return {
                "started": False,
                "error":
                    "surah_not_found",
            }

        self.mode = "read"
        self.surah_number = surah_number
        self.surah_name = surah["name"]
        self.waiting_for_surah = False
        self.waiting_for_child = False

        self.say(
            f"تمام. رح نسمع "
            f"{self.surah_name} "
            "بصوت القارئ.",
            resume_listening=False,
        )

        if self.quran_stop_requested:
            return self._finish_quran_stop()

        # Reading = each ayah ONCE only.
        for ayah_number in range(
            1,
            surah["ayah_count"] + 1,
        ):

            print()
            print(
                f"📖 Reading Ayah "
                f"{ayah_number}/"
                f"{surah['ayah_count']} "
                "(once)"
            )

            success = self.play_ayah_audio(
                surah_number,
                ayah_number,
                resume_after=False,
                prefetch=True,
            )

            if not success:

                if self.quran_stop_requested:
                    return self._finish_quran_stop()

                self.reset()
                return {
                    "started": False,
                    "error":
                        "playback_failed",
                    "failed_ayah":
                        ayah_number,
                }

        completed_surah = self.surah_name

        self.reset()

        self.say(
            f"خلصت {completed_surah}.",
            resume_listening=True,
        )

        return {
            "started": True,
            "completed": True,
            "surah_number":
                surah_number,
            "surah_name":
                completed_surah,
        }

    # =====================================================
    # Build Memorization Sections
    # =====================================================

    def build_memorization_sections(
        self,
        surah_number,
        start_ayah,
        ayah_count,
    ):

        start_ayah = max(
            1,
            int(start_ayah),
        )

        ayah_count = int(
            ayah_count
        )

        sections = []

        # Small surah -> two ayahs together.
        if ayah_count <= SMALL_SURAH_MAX_AYAHS:

            cursor = start_ayah

            while cursor <= ayah_count:

                learn_start = cursor
                learn_end = min(
                    cursor + 1,
                    ayah_count,
                )

                learn_ayahs = list(
                    range(
                        learn_start,
                        learn_end + 1,
                    )
                )

                review_start = learn_start
                review_end = learn_end

                # Odd final ayah:
                # review previous + final together.
                if (
                    len(learn_ayahs) == 1
                    and
                    learn_start > 1
                ):
                    review_start = (
                        learn_start - 1
                    )

                sections.append(
                    {
                        "learn_ayahs":
                            learn_ayahs,
                        "review_start":
                            review_start,
                        "review_end":
                            review_end,
                        "kind":
                            "small_pair",
                    }
                )

                cursor = learn_end + 1

            return sections

        # Medium / large surah.
        if ayah_count <= MEDIUM_SURAH_MAX_AYAHS:

            max_ayahs = (
                MEDIUM_SECTION_MAX_AYAHS
            )
            max_words = (
                MEDIUM_SECTION_MAX_WORDS
            )
            kind = "medium_section"

        else:

            max_ayahs = (
                LARGE_SECTION_MAX_AYAHS
            )
            max_words = (
                LARGE_SECTION_MAX_WORDS
            )
            kind = "large_section"

        cursor = start_ayah

        while cursor <= ayah_count:

            learn_ayahs = []
            word_total = 0

            while (
                cursor <= ayah_count
                and
                len(learn_ayahs)
                <
                max_ayahs
            ):

                word_count = (
                    self.get_ayah_word_count(
                        surah_number,
                        cursor,
                    )
                )

                if (
                    learn_ayahs
                    and
                    (
                        word_total
                        +
                        word_count
                    )
                    >
                    max_words
                ):
                    break

                learn_ayahs.append(
                    cursor
                )

                word_total += (
                    word_count
                )

                cursor += 1

                if word_total >= max_words:
                    break

            sections.append(
                {
                    "learn_ayahs":
                        learn_ayahs,
                    "review_start":
                        learn_ayahs[0],
                    "review_end":
                        learn_ayahs[-1],
                    "word_count":
                        word_total,
                    "kind":
                        kind,
                }
            )

        return sections

    # =====================================================
    # Start Memorization
    # =====================================================

    def start_memorization(
        self,
        request_text="",
        surah_number=None,
    ):

        if not self.started:
            self.start_module()

        self.quran_stop_requested = False
        self.last_control_command = None

        if surah_number is None:
            surah_number = self.detect_surah(
                request_text
            )

        if surah_number is None:
            self.mode = "memorize"
            self.waiting_for_surah = True
            self.waiting_for_child = False

            self.say(
                "أكيد. أي سورة بدك نحفظ؟"
            )

            return {
                "started": False,
                "needs_surah": True,
            }

        surah = self.get_surah(
            surah_number
        )

        if surah is None:
            return {
                "started": False,
                "error":
                    "surah_not_found",
            }

        resume_ayah = self.get_resume_ayah(
            surah_number
        )

        if resume_ayah is None:

            summary = self.get_progress_summary(
                surah_number
            )

            self.reset()

            self.say(
                f"ما شاء الله. "
                f"إنت خلصت "
                f"{surah['name']} "
                "من قبل."
            )

            return {
                "started": False,
                "completed": True,
                "already_mastered": True,
                "surah_number":
                    surah_number,
                "summary":
                    summary,
            }

        self.mode = "memorize"
        self.surah_number = surah_number
        self.surah_name = surah["name"]

        self.current_ayah = resume_ayah
        self.current_repeat = 0
        self.current_attempts = 0
        self.last_score = 0.0

        self.waiting_for_surah = False
        self.waiting_for_child = False

        self.sections = self.build_memorization_sections(
            surah_number=
                surah_number,
            start_ayah=
                resume_ayah,
            ayah_count=
                surah["ayah_count"],
        )

        self.section_index = 0

        if not self.sections:
            self.reset()
            return {
                "started": False,
                "error":
                    "empty_memorization_plan",
            }

        self.load_current_section()

        self.say(
            f"تمام. خلينا نحفظ "
            f"{self.surah_name}. "
            f"رح أقرأ كل آية "
            f"{self.repeat_target} مرات، "
            "وبعدين إنت بتكررها. "
            "وبعد مجموعة صغيرة "
            "بنراجع الآيات مع بعض.",
            resume_listening=False,
        )

        if self.quran_stop_requested:
            return self._finish_quran_stop()

        first_played = self.play_current_ayah()

        if not first_played:

            if self.quran_stop_requested:
                return self._finish_quran_stop()

            self.reset()
            return {
                "started": False,
                "audio_ready": False,
                "error":
                    "ayah_audio_unavailable",
            }

        return {
            "started": True,
            "mode":
                "memorize",
            "surah_number":
                self.surah_number,
            "surah_name":
                self.surah_name,
            "ayah_number":
                self.current_ayah,
            "reciter_repeat_target":
                self.repeat_target,
            "child_success_target":
                self.child_success_target,
            "pass_threshold":
                self.evaluator.pass_threshold,
            "section_count":
                len(self.sections),
        }

    # =====================================================
    # Section State
    # =====================================================

    def load_current_section(self):

        section = self.sections[
            self.section_index
        ]

        self.section_learn_ayahs = list(
            section["learn_ayahs"]
        )

        self.section_review_start = int(
            section["review_start"]
        )

        self.section_review_end = int(
            section["review_end"]
        )

        self.section_position = 0
        self.current_ayah = (
            self.section_learn_ayahs[0]
        )

        self.current_repeat = 0
        self.current_attempts = 0
        self.last_score = 0.0
        self.review_attempts = 0

        self.memorization_stage = "ayah"
        self.pending_progress = {}

        print()
        print(
            f"📚 Section "
            f"{self.section_index + 1}/"
            f"{len(self.sections)}"
        )
        print(
            "Learn:",
            self.section_learn_ayahs,
        )
        print(
            "Review:",
            f"{self.section_review_start}"
            f"-"
            f"{self.section_review_end}",
        )

    def section_needs_review(self):

        return (
            self.section_review_end
            >
            self.section_review_start
        )

    # =====================================================
    # Play Current Learning Ayah
    # =====================================================

    def play_current_ayah(self):

        if self.mode != "memorize":
            return False

        self.memorization_stage = "ayah"
        self.waiting_for_child = False
        self.stop_microphone()

        self.say(
            f"اسمع الآية رقم "
            f"{self.current_ayah} "
            f"{self.repeat_target} مرات، "
            "وبعدين دورك.",
            resume_listening=False,
        )

        if self.quran_stop_requested:
            self._finish_quran_stop()
            return False

        for repetition in range(
            1,
            self.repeat_target + 1,
        ):

            print()
            print(
                f"📖 Ayah "
                f"{self.current_ayah} "
                f"- play "
                f"{repetition}/"
                f"{self.repeat_target}"
            )

            success = self.play_ayah_audio(
                self.surah_number,
                self.current_ayah,
                resume_after=False,
                prefetch=
                    repetition == 1,
            )

            if not success:

                if self.quran_stop_requested:
                    self._finish_quran_stop()

                return False

        self.set_quran_listening_time(
            self.current_ayah,
            self.current_ayah,
        )

        self.waiting_for_child = True
        self.resume_microphone()

        print()
        print(
            "🎤 Waiting for child..."
        )

        return True

    # =====================================================
    # Play Section Review
    # =====================================================

    def play_current_review(self):

        if self.mode != "memorize":
            return False

        self.memorization_stage = (
            "section_review"
        )

        self.waiting_for_child = False
        self.stop_microphone()

        start_ayah = (
            self.section_review_start
        )

        end_ayah = (
            self.section_review_end
        )

        if end_ayah == start_ayah + 1:

            self.say(
                f"ممتاز. هسا نربط "
                f"الآيتين {start_ayah} "
                f"و{end_ayah} مع بعض. "
                f"رح أقرأهم "
                f"{self.repeat_target} مرات، "
                "وبعدين إنت بتعيدهم مع بعض.",
                resume_listening=False,
            )

        else:

            self.say(
                f"ممتاز. هسا نراجع "
                f"الآيات من {start_ayah} "
                f"إلى {end_ayah} مع بعض. "
                f"رح أقرأ المقطع "
                f"{self.repeat_target} مرات، "
                "وبعدين دورك.",
                resume_listening=False,
            )

        if self.quran_stop_requested:
            self._finish_quran_stop()
            return False

        # One cycle = every ayah in the section once.
        for repetition in range(
            1,
            self.repeat_target + 1,
        ):

            print()
            print(
                f"🧩 Section cycle "
                f"{repetition}/"
                f"{self.repeat_target}"
            )

            for ayah_number in range(
                start_ayah,
                end_ayah + 1,
            ):

                success = self.play_ayah_audio(
                    self.surah_number,
                    ayah_number,
                    resume_after=False,
                    prefetch=True,
                )

                if not success:

                    if self.quran_stop_requested:
                        self._finish_quran_stop()

                    return False

        self.set_quran_listening_time(
            start_ayah,
            end_ayah,
        )

        self.waiting_for_child = True
        self.resume_microphone()

        print()
        print(
            "🎤 Waiting for section recitation..."
        )

        return True

    # =====================================================
    # Child Input
    # =====================================================

    def register_repeat(
        self,
        child_text="",
    ):

        if (
            self.mode != "memorize"
            or
            not self.waiting_for_child
        ):
            return {
                "handled": False,
                "reason":
                    "not_waiting_for_recitation",
            }

        if (
            self.memorization_stage
            ==
            "section_review"
        ):
            return self.register_section_review(
                child_text
            )

        return self.register_ayah_repeat(
            child_text
        )

    def register_ayah_repeat(
        self,
        child_text,
    ):

        self.waiting_for_child = False
        self.stop_microphone()
        self.current_attempts += 1

        evaluation = self.evaluator.evaluate(
            self.surah_number,
            self.current_ayah,
            child_text,
        )

        if not evaluation.get("handled"):

            self.say(
                "صار خطأ أثناء تقييم القراءة. "
                "خلينا نسمع الآية مرة ثانية.",
                resume_listening=False,
            )

            self.play_current_ayah()

            return {
                "handled": True,
                "passed": False,
                "evaluation_error": True,
            }

        score = float(
            evaluation.get(
                "score",
                0.0,
            )
        )

        self.last_score = score
        self.evaluator.show_result(
            evaluation
        )

        # Wrong -> same ayah x3 again.
        if not evaluation.get(
            "passed",
            False,
        ):

            self.say(
                self.make_feedback(
                    evaluation,
                    section=False,
                ),
                resume_listening=False,
            )

            replay_started = (
                self.play_current_ayah()
            )

            return {
                "handled": True,
                "passed": False,
                "score":
                    score,
                "ayah_number":
                    self.current_ayah,
                "attempts":
                    self.current_attempts,
                "replay_started":
                    replay_started,
            }

        completed_ayah = self.current_ayah
        self.current_repeat = 1

        self.pending_progress[
            completed_ayah
        ] = {
            "score":
                score,
            "attempts":
                self.current_attempts,
        }

        # More ayahs in this section.
        if (
            self.section_position + 1
            <
            len(
                self.section_learn_ayahs
            )
        ):

            self.section_position += 1

            self.current_ayah = (
                self.section_learn_ayahs[
                    self.section_position
                ]
            )

            self.current_repeat = 0
            self.current_attempts = 0
            self.last_score = 0.0

            self.say(
                "ممتاز. هسا الآية التالية.",
                resume_listening=False,
            )

            next_started = (
                self.play_current_ayah()
            )

            return {
                "handled": True,
                "passed": True,
                "ayah_completed": True,
                "section_completed":
                    False,
                "completed_ayah":
                    completed_ayah,
                "next_ayah":
                    self.current_ayah,
                "next_started":
                    next_started,
            }

        # Review current section together.
        if self.section_needs_review():

            self.review_attempts = 0

            review_started = (
                self.play_current_review()
            )

            return {
                "handled": True,
                "passed": True,
                "ayah_completed": True,
                "section_review": True,
                "review_start":
                    self.section_review_start,
                "review_end":
                    self.section_review_end,
                "review_started":
                    review_started,
            }

        return self.complete_current_section(
            review_score=
                score,
        )

    def register_section_review(
        self,
        child_text,
    ):

        self.waiting_for_child = False
        self.stop_microphone()
        self.review_attempts += 1

        evaluation = self.evaluate_passage(
            self.section_review_start,
            self.section_review_end,
            child_text,
        )

        if not evaluation.get("handled"):

            self.say(
                "صار خطأ بتقييم المقطع. "
                "خلينا نعيده.",
                resume_listening=False,
            )

            self.play_current_review()

            return {
                "handled": True,
                "passed": False,
                "evaluation_error": True,
            }

        score = float(
            evaluation.get(
                "score",
                0.0,
            )
        )

        self.evaluator.show_result(
            evaluation
        )

        # Wrong section -> whole section x3 again.
        if not evaluation.get(
            "passed",
            False,
        ):

            self.say(
                self.make_feedback(
                    evaluation,
                    section=True,
                ),
                resume_listening=False,
            )

            replay_started = (
                self.play_current_review()
            )

            return {
                "handled": True,
                "passed": False,
                "section_review": True,
                "score":
                    score,
                "review_attempts":
                    self.review_attempts,
                "replay_started":
                    replay_started,
            }

        return self.complete_current_section(
            review_score=
                score,
        )

    def make_feedback(
        self,
        evaluation,
        section=False,
    ):

        missing = evaluation.get(
            "missing",
            [],
        )

        substitutions = evaluation.get(
            "substitutions",
            [],
        )

        extra = evaluation.get(
            "extra",
            [],
        )

        if section:
            base = (
                "خلينا نعيد المقطع "
                "ثلاث مرات وبعدين جرب مرة ثانية."
            )
        else:
            base = (
                "خلينا نعيد الآية "
                "ثلاث مرات وبعدين جرب مرة ثانية."
            )

        if missing:
            return (
                "قريبة. في كلمة ناقصة. "
                +
                base
            )

        if substitutions:
            return (
                "قريبة. في كلمة مش مطابقة. "
                +
                base
            )

        if extra:
            return (
                "قريبة. في كلمة زيادة. "
                +
                base
            )

        return (
            "قريبة. "
            +
            base
        )

    # =====================================================
    # Finish Section
    # =====================================================

    def complete_current_section(
        self,
        review_score=None,
    ):

        completed_section = (
            self.section_index + 1
        )

        saved_progress = []

        # Save only newly learned ayahs.
        for ayah_number in sorted(
            self.pending_progress.keys()
        ):

            item = self.pending_progress[
                ayah_number
            ]

            saved = self.save_ayah_progress(
                ayah_number=
                    ayah_number,
                score=
                    item["score"],
                attempts=
                    item["attempts"],
            )

            saved_progress.append(
                {
                    "ayah_number":
                        ayah_number,
                    "saved":
                        saved,
                }
            )

        # Last section.
        if (
            self.section_index
            >=
            len(self.sections) - 1
        ):

            completed_surah = (
                self.surah_name
            )

            completed_surah_number = (
                self.surah_number
            )

            summary = self.get_progress_summary(
                completed_surah_number
            )

            self.reset()

            self.say(
                "ما شاء الله. "
                f"هيك خلصنا "
                f"{completed_surah}. "
                "تعلمنا الآيات "
                "وربطنا المقاطع مع بعض.",
                resume_listening=True,
            )

            return {
                "handled": True,
                "passed": True,
                "section_completed": True,
                "surah_completed": True,
                "surah_number":
                    completed_surah_number,
                "surah_name":
                    completed_surah,
                "completed_section":
                    completed_section,
                "review_score":
                    review_score,
                "saved_progress":
                    saved_progress,
                "summary":
                    summary,
            }

        # Next section.
        self.section_index += 1
        self.load_current_section()

        self.say(
            "ممتاز. خلصنا هالمقطع. "
            "هسا بناخذ المقطع اللي بعده "
            "شوي شوي.",
            resume_listening=False,
        )

        next_started = (
            self.play_current_ayah()
        )

        return {
            "handled": True,
            "passed": True,
            "section_completed": True,
            "surah_completed": False,
            "completed_section":
                completed_section,
            "review_score":
                review_score,
            "saved_progress":
                saved_progress,
            "next_section":
                self.section_index + 1,
            "next_ayah":
                self.current_ayah,
            "next_started":
                next_started,
        }

    # =====================================================
    # Input / State
    # =====================================================

    def handle_input(
        self,
        text,
    ):

        if self.waiting_for_surah:

            surah_number = self.detect_surah(
                text
            )

            if surah_number is None:

                self.say(
                    "ما عرفت اسم السورة. "
                    "احكيلي اسمها."
                )

                return {
                    "handled": True,
                    "needs_surah": True,
                }

            previous_mode = self.mode
            self.waiting_for_surah = False

            if previous_mode == "read":
                return self.start_reading(
                    surah_number=
                        surah_number
                )

            if previous_mode == "memorize":
                return self.start_memorization(
                    surah_number=
                        surah_number
                )

        if (
            self.mode == "memorize"
            and
            self.waiting_for_child
        ):
            return self.register_repeat(
                child_text=
                    text
            )

        return {
            "handled": False,
        }

    def is_active(self):
        return (
            self.mode is not None
            or
            self.waiting_for_surah
        )

    def is_reading(self):
        return (
            self.mode == "read"
        )

    def is_memorizing(self):
        return (
            self.mode == "memorize"
        )

    def is_waiting_for_child(self):
        return self.waiting_for_child

    def is_waiting_for_surah(self):
        return self.waiting_for_surah

    def get_state(self):

        return {
            "child_id":
                self.child_id,
            "mode":
                self.mode,
            "surah_number":
                self.surah_number,
            "surah_name":
                self.surah_name,
            "current_ayah":
                self.current_ayah,
            "current_repeat":
                self.current_repeat,
            "reciter_repeat_target":
                self.repeat_target,
            "child_success_target":
                self.child_success_target,
            "current_attempts":
                self.current_attempts,
            "last_score":
                self.last_score,
            "pass_threshold":
                self.evaluator.pass_threshold,
            "waiting_for_surah":
                self.waiting_for_surah,
            "waiting_for_child":
                self.waiting_for_child,
            "memorization_stage":
                self.memorization_stage,
            "section_index":
                (
                    self.section_index + 1
                    if self.sections
                    else 0
                ),
            "section_count":
                len(self.sections),
            "section_learn_ayahs":
                list(
                    self.section_learn_ayahs
                ),
            "section_review_start":
                self.section_review_start,
            "section_review_end":
                self.section_review_end,
            "review_attempts":
                self.review_attempts,
            "quran_stop_requested":
                self.quran_stop_requested,
            "last_control_command":
                self.last_control_command,
            "quran_volume":
                getattr(
                    self.player,
                    "volume",
                    None,
                ),
        }

    def reset(self):

        self.mode = None
        self.surah_number = None
        self.surah_name = None

        self.current_ayah = 1
        self.current_repeat = 0
        self.current_attempts = 0
        self.last_score = 0.0

        self.waiting_for_surah = False
        self.waiting_for_child = False

        self.memorization_stage = None
        self.sections = []
        self.section_index = 0
        self.section_learn_ayahs = []
        self.section_review_start = None
        self.section_review_end = None
        self.section_position = 0
        self.review_attempts = 0
        self.pending_progress = {}

    def close(self):

        try:
            self.player.stop()
        except Exception:
            pass

        self.stop_microphone()
        self.reset()
        self.child_id = None
        self.started = False

        print(
            "✅ Quran Module closed."
        )


# =========================================================
# Lightweight Plan Test
# =========================================================

def test_quran_module():

    quran = QuranModule(
        voice_module=None,
        child_id=None,
        repeat_target=3,
        pass_threshold=85.0,
    )

    quran.evaluator.start()

    print()
    print("=" * 70)
    print(
        "📖 MIMI QURAN MEMORIZATION PLAN TEST"
    )
    print("=" * 70)

    tests = [
        112,
        113,
        114,
        67,
        2,
    ]

    for surah_number in tests:

        surah = quran.get_surah(
            surah_number
        )

        print()
        print(
            f"{surah['name']} "
            f"({surah['ayah_count']} ayahs)"
        )

        sections = (
            quran.build_memorization_sections(
                surah_number=
                    surah_number,
                start_ayah=1,
                ayah_count=
                    surah["ayah_count"],
            )
        )

        for index, section in enumerate(
            sections[:8],
            start=1,
        ):

            print(
                f"  Section {index}: "
                f"learn="
                f"{section['learn_ayahs']} "
                f"review="
                f"{section['review_start']}"
                f"-"
                f"{section['review_end']} "
                f"type="
                f"{section['kind']}"
            )

        if len(sections) > 8:
            print(
                f"  ... total sections: "
                f"{len(sections)}"
            )

    print()
    print("=" * 70)


if __name__ == "__main__":

    test_quran_module()