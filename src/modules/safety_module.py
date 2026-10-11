import re
import time
import unicodedata
from collections import deque

from src.database.safety_events import (
    create_safety_event,
    resolve_safety_event,
)


# =========================================================
# SETTINGS
# =========================================================

# Loud-sound protection:
# one single spike should NOT immediately trigger an alert.
LOUD_CONFIRM_HITS = 3
LOUD_CONFIRM_WINDOW = 4.0

# Cry detection:
# two positive detections close together are enough.
CRY_CONFIRM_HITS = 2
CRY_CONFIRM_WINDOW = 6.0

# Prevent repeated identical alerts right after clearing.
ALERT_COOLDOWN = 15.0


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_arabic(text):

    if text is None:
        return ""

    text = str(text).strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    for char in (
        "أ",
        "إ",
        "آ",
        "ٱ",
    ):
        text = text.replace(
            char,
            "ا",
        )

    text = text.replace(
        "ى",
        "ي",
    )

    text = text.replace(
        "ـ",
        "",
    )

    text = re.sub(
        r"[^\u0600-\u06FF0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# SAFETY MODULE
# =========================================================

class SafetyModule:

    def __init__(
        self,
        voice_module=None,
        alert_callback=None,
    ):

        self.voice = voice_module

        # Optional callback used later by MimiBot to immediately
        # stop Story/Quran/Learning/Adhkar when Safety triggers.
        self.alert_callback = alert_callback

        self.started = False

        self.child_id = None

        self.active = False

        self.current_event_id = None

        self.last_trigger_type = None

        self.last_trigger_time = 0.0

        # -------------------------------------------------
        # Emergency phrases
        #
        # Keep these short and direct so phrases such as
        # "ساعدني بالواجب" do NOT trigger an emergency.
        # -------------------------------------------------

        self.emergency_phrases = {
            "ساعدني",
            "ساعديني",
            "الحقني",
            "الحقوني",
            "ساعدوني",
            "نجده",
            "النجده",
            "مساعده بسرعه",
            "مساعدة بسرعة",
        }

        self.cancel_phrases = {
            "انا بخير",
            "انا منيح",
            "خلص انا بخير",
            "الغاء المساعده",
            "الغاء المساعدة",
            "الغي المساعده",
            "الغي المساعدة",
            "وقف المساعده",
            "وقف المساعدة",
        }

        # -------------------------------------------------
        # False-alarm protection
        # -------------------------------------------------

        self.loud_hits = deque()
        self.cry_hits = deque()

        # Real loud-sound detector is wired to the existing
        # Voice Listener microphone stream.
        self.audio_detector_wired = False

    # =====================================================
    # AUDIO DETECTOR WIRING
    # =====================================================

    def wire_audio_detector(self):

        if self.audio_detector_wired:
            return True

        try:

            from src.voice.listener import (
                set_audio_event_callback,
                set_loud_detection_enabled,
            )

            set_audio_event_callback(
                self.handle_audio_event
            )

            set_loud_detection_enabled(
                True
            )

            self.audio_detector_wired = True

            print(
                "✅ Real loud-sound detector wired "
                "to Voice Listener."
            )

            return True

        except Exception as error:

            print(
                "⚠️ Could not wire real "
                "loud-sound detector:",
                error,
            )

            self.audio_detector_wired = False

            return False

    def unwire_audio_detector(self):

        if not self.audio_detector_wired:
            return

        try:

            from src.voice.listener import (
                set_audio_event_callback,
            )

            set_audio_event_callback(
                None
            )

        except Exception:
            pass

        self.audio_detector_wired = False

    # =====================================================
    # INTEGRATION HELPERS
    # =====================================================

    def set_voice(
        self,
        voice_module,
    ):

        self.voice = voice_module

    def set_alert_callback(
        self,
        callback=None,
    ):
        """
        MimiBot can register a callback here later.

        The callback receives one dictionary describing the alert.
        It is intended to stop any currently running activity/audio
        before Safety speaks.
        """

        self.alert_callback = callback

    def _interrupt_mimi_output(self):
        """
        Stop Mimi TTS immediately if it is currently speaking.

        This does NOT close the microphone.
        """

        if self.voice is None:
            return False

        try:

            stop_speaking = getattr(
                self.voice,
                "stop_speaking",
                None,
            )

            if callable(stop_speaking):
                return bool(
                    stop_speaking()
                )

        except Exception as error:

            print(
                "⚠️ Safety could not interrupt Mimi output:",
                error,
            )

        return False

    def _call_alert_callback(
        self,
        payload,
    ):

        callback = self.alert_callback

        if not callable(callback):
            return False

        try:

            callback(
                dict(payload)
            )

            return True

        except Exception as error:

            print(
                "⚠️ Safety alert callback error:",
                error,
            )

            return False

    def handle_priority_voice(
        self,
        text,
    ):
        """
        Priority voice entry-point for the final MimiBot router.

        MimiBot should call Safety before normal intents so an exact
        emergency phrase has priority over Story/Quran/etc.
        """

        return self.handle_voice(
            text
        )

    # =====================================================
    # START
    # =====================================================

    def start_module(self):

        if self.started:
            return

        print()
        print("=" * 60)
        print("🚨 STARTING SAFETY MODULE")
        print("=" * 60)

        self.started = True

        detector_ok = self.wire_audio_detector()

        if self.voice is not None:

            try:
                self.voice.enable()
            except Exception:
                pass

        print(
            "✅ Voice emergency phrase ready."
        )

        if detector_ok:
            print(
                "✅ Real loud detector is using the same microphone stream."
            )
        else:
            print(
                "⚠️ Real loud detector is not connected yet."
            )

        print(
            "✅ Loud sound confirmation ready."
        )

        print(
            "✅ Cry confirmation interface ready."
        )

        print("=" * 60)

    # =====================================================
    # CHILD
    # =====================================================

    def set_child(
        self,
        child_id,
    ):

        self.child_id = (
            str(child_id)
            if child_id
            else None
        )

        print()
        print(
            f"🚨 Safety child: "
            f"{self.child_id or 'Guest'}"
        )

    def clear_child(self):

        if self.active:

            self.clear_alert(
                reason="person_left"
            )

        self.child_id = None

        self.reset_detection_buffers()

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

        if self.voice is None:

            print(
                f"🤖 Mimi: {text}"
            )

            return True

        try:

            # The new VoiceModule keeps the microphone ON while
            # Mimi speaks. We intentionally do not disable it here.
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

            try:
                result = self.voice.say(text)
                return True if result is None else bool(result)
            except Exception as error:
                print(
                    "⚠️ Safety voice error:",
                    error,
                )
                return False

        except Exception as error:

            print(
                "⚠️ Safety voice error:",
                error,
            )

            return False

    # =====================================================
    # CLEAN WAKE WORD
    # =====================================================

    def clean_voice_text(
        self,
        text,
    ):

        text = normalize_arabic(
            text
        )

        # Remove Mimi wake word.
        for word in (
            "ميمي",
            "ميمى",
        ):

            if text == word:
                return ""

            if text.startswith(
                word + " "
            ):

                text = text[
                    len(word):
                ].strip()

        return text

    # =====================================================
    # DETECT EMERGENCY PHRASE
    # =====================================================

    def is_emergency_phrase(
        self,
        text,
    ):

        text = (
            self.clean_voice_text(
                text
            )
        )

        return (
            text
            in self.emergency_phrases
        )

    # =====================================================
    # DETECT CANCEL
    # =====================================================

    def is_cancel_phrase(
        self,
        text,
    ):

        text = (
            self.clean_voice_text(
                text
            )
        )

        return (
            text
            in self.cancel_phrases
        )

    # =====================================================
    # COOLDOWN
    # =====================================================

    def _cooldown_active(
        self,
        trigger_type,
    ):

        if (
            self.last_trigger_type
            != trigger_type
        ):
            return False

        elapsed = (
            time.monotonic()
            -
            self.last_trigger_time
        )

        return (
            elapsed
            <
            ALERT_COOLDOWN
        )

    # =====================================================
    # TRIGGER ALERT
    # =====================================================

    def trigger(
        self,
        trigger_type,
        trigger_text=None,
        details=None,
        severity="high",
    ):

        if self.active:

            return {
                "handled": True,
                "triggered": False,
                "already_active": True,
                "event_id":
                    self.current_event_id,
            }

        if self._cooldown_active(
            trigger_type
        ):

            return {
                "handled": True,
                "triggered": False,
                "cooldown": True,
            }

        print()
        print("=" * 60)
        print("🚨🚨🚨 SAFETY ALERT 🚨🚨🚨")
        print("=" * 60)

        print(
            f"Trigger: {trigger_type}"
        )

        if trigger_text:

            print(
                f"Text: {trigger_text}"
            )

        self.active = True

        self.last_trigger_type = (
            trigger_type
        )

        self.last_trigger_time = (
            time.monotonic()
        )

        # -------------------------------------------------
        # Registered child -> MongoDB
        # -------------------------------------------------

        if self.child_id:

            try:

                self.current_event_id = (
                    create_safety_event(
                        child_id=
                            self.child_id,

                        trigger_type=
                            trigger_type,

                        trigger_text=
                            trigger_text,

                        severity=
                            severity,

                        details=
                            details or {},
                    )
                )

            except Exception as error:

                print()
                print(
                    "⚠️ Could not save "
                    "safety event:"
                )

                print(
                    error
                )

                self.current_event_id = None

        else:

            print()
            print(
                "👤 Guest safety alert: "
                "not saved to child database."
            )

        # -------------------------------------------------
        # Important:
        # We intentionally do NOT claim that a parent was
        # notified unless a notification service is wired.
        # -------------------------------------------------

        alert_payload = {
            "trigger_type":
                trigger_type,
            "trigger_text":
                trigger_text,
            "severity":
                severity,
            "details":
                details or {},
            "event_id":
                self.current_event_id,
            "child_id":
                self.child_id,
        }

        # Safety has priority over Mimi's current TTS.
        # The microphone remains enabled.
        self._interrupt_mimi_output()

        # MimiBot will use this later to stop any activity MP3 too.
        self._call_alert_callback(
            alert_payload
        )

        self.say(
            "أنا معك. "
            "تم تشغيل وضع المساعدة. "
            "إذا في خطر، نادي شخص بالغ "
            "قريب منك فورًا."
        )

        return {
            "handled": True,
            "triggered": True,
            "trigger_type":
                trigger_type,
            "event_id":
                self.current_event_id,
            "parent_notified":
                False,
        }

    # =====================================================
    # VOICE INPUT
    # =====================================================

    def handle_voice(
        self,
        text,
    ):

        # -------------------------------------------------
        # Alert already active
        # -------------------------------------------------

        if self.active:

            if self.is_cancel_phrase(
                text
            ):

                self.clear_alert(
                    reason=
                        "child_said_safe"
                )

                self.say(
                    "تمام. "
                    "تم إلغاء وضع المساعدة."
                )

                return {
                    "handled": True,
                    "cleared": True,
                }

            return {
                "handled": True,
                "alert_active": True,
            }

        # -------------------------------------------------
        # New emergency phrase
        # -------------------------------------------------

        if self.is_emergency_phrase(
            text
        ):

            return self.trigger(
                trigger_type=
                    "voice_phrase",

                trigger_text=
                    text,

                severity=
                    "critical",
            )

        return {
            "handled": False,
        }

    # =====================================================
    # DETECTION BUFFERS
    # =====================================================

    def _register_hit(
        self,
        buffer,
        window_seconds,
    ):

        now = time.monotonic()

        buffer.append(
            now
        )

        while (
            buffer
            and
            now - buffer[0]
            >
            window_seconds
        ):

            buffer.popleft()

        return len(
            buffer
        )

    def reset_detection_buffers(self):

        self.loud_hits.clear()
        self.cry_hits.clear()

    # =====================================================
    # LOUD SOUND
    # =====================================================

    def register_loud_sound(
        self,
        sound_level=None,
        duration_ms=None,
    ):
        """
        Call this when the sound detector decides that one
        suspicious loud-sound event happened.

        We require multiple hits within a short time window
        to reduce false alarms from one clap / object drop.
        """

        if self.active:

            return {
                "handled": True,
                "alert_active": True,
            }

        hits = self._register_hit(
            self.loud_hits,
            LOUD_CONFIRM_WINDOW,
        )

        print(
            f"🔊 Loud sound hit "
            f"{hits}/{LOUD_CONFIRM_HITS}"
        )

        if hits < LOUD_CONFIRM_HITS:

            return {
                "handled": True,
                "triggered": False,
                "pending_confirmation":
                    True,
                "hits":
                    hits,
            }

        details = {
            "confirmed_hits":
                hits,
        }

        if sound_level is not None:

            details[
                "sound_level"
            ] = sound_level

        if duration_ms is not None:

            details[
                "duration_ms"
            ] = duration_ms

        self.loud_hits.clear()

        return self.trigger(
            trigger_type=
                "loud_sound",

            details=
                details,

            severity=
                "high",
        )

    def trigger_loud_sound(
        self,
        sound_level=None,
    ):
        """
        Backward-compatible manual/forced trigger.
        Existing MimiBot code can keep using this API.
        """

        details = {}

        if sound_level is not None:

            details[
                "sound_level"
            ] = sound_level

        return self.trigger(
            trigger_type=
                "loud_sound",

            details=
                details,

            severity=
                "high",
        )

    # =====================================================
    # CRY DETECTION
    # =====================================================

    def register_cry(
        self,
        confidence=None,
        duration_ms=None,
    ):
        """
        Call this whenever the cry detector/model reports a
        positive child-cry candidate.

        Two close detections are required by default so one
        mistaken frame/chunk does not trigger safety mode.
        """

        if self.active:

            return {
                "handled": True,
                "alert_active": True,
            }

        hits = self._register_hit(
            self.cry_hits,
            CRY_CONFIRM_WINDOW,
        )

        print(
            f"😢 Cry hit "
            f"{hits}/{CRY_CONFIRM_HITS}"
        )

        if hits < CRY_CONFIRM_HITS:

            return {
                "handled": True,
                "triggered": False,
                "pending_confirmation":
                    True,
                "hits":
                    hits,
            }

        details = {
            "confirmed_hits":
                hits,
        }

        if confidence is not None:

            details[
                "confidence"
            ] = confidence

        if duration_ms is not None:

            details[
                "duration_ms"
            ] = duration_ms

        self.cry_hits.clear()

        return self.trigger(
            trigger_type=
                "child_cry",

            details=
                details,

            severity=
                "high",
        )

    # =====================================================
    # GENERIC AUDIO EVENT
    # =====================================================

    def handle_audio_event(
        self,
        event_type,
        sound_level=None,
        confidence=None,
        duration_ms=None,
    ):

        event_type = str(
            event_type or ""
        ).strip().lower()

        if event_type in {
            "cry",
            "child_cry",
            "crying",
        }:

            return self.register_cry(
                confidence=
                    confidence,
                duration_ms=
                    duration_ms,
            )

        if event_type in {
            "loud",
            "loud_sound",
            "bang",
        }:

            return self.register_loud_sound(
                sound_level=
                    sound_level,
                duration_ms=
                    duration_ms,
            )

        return {
            "handled": False,
        }

    # =====================================================
    # CLEAR ALERT
    # =====================================================

    def clear_alert(
        self,
        reason="manual_clear",
    ):

        event_id = (
            self.current_event_id
        )

        if event_id:

            try:

                resolve_safety_event(
                    event_id=
                        event_id,

                    resolution=
                        reason,
                )

            except Exception as error:

                print(
                    "⚠️ Could not resolve "
                    "safety event:",
                    error,
                )

        self.active = False

        self.current_event_id = None

        # Keep last_trigger_type/time for cooldown.
        self.reset_detection_buffers()

        print()
        print(
            "✅ Safety alert cleared."
        )

    # =====================================================
    # STATE
    # =====================================================

    def is_active(self):

        return self.active

    def get_state(self):

        return {
            "active":
                self.active,

            "event_id":
                self.current_event_id,

            "trigger_type":
                self.last_trigger_type,

            "child_id":
                self.child_id,

            "loud_hits":
                len(
                    self.loud_hits
                ),

            "cry_hits":
                len(
                    self.cry_hits
                ),

            "audio_detector_wired":
                self.audio_detector_wired,

            "parent_notification_connected":
                False,
        }

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.unwire_audio_detector()

        if self.active:

            self.clear_alert(
                reason=
                    "application_closed"
            )

        self.child_id = None

        self.started = False

        self.reset_detection_buffers()

        print(
            "✅ Safety Module closed."
        )


# =========================================================
# SIMPLE TEST
# =========================================================

def test_safety():

    safety = SafetyModule(
        voice_module=None
    )

    safety.start_module()

    safety.set_child(
        None
    )

    print()
    print("1) Normal sentence:")
    print(
        safety.handle_voice(
            "ميمي ساعدني بالواجب"
        )
    )

    print()
    print("2) Emergency phrase:")
    print(
        safety.handle_voice(
            "ميمي ساعدني"
        )
    )

    print()
    print("3) Cancel:")
    print(
        safety.handle_voice(
            "أنا بخير"
        )
    )

    safety.close()


if __name__ == "__main__":

    test_safety()