import queue
import threading
import time

from src.voice.listener import (
    listen_once,
    reset_audio_cache,
    set_listening_profile as set_vad_profile,
)


# =========================================================
# SETTINGS
# =========================================================

POST_COMMAND_DELAY = 0.75
IDLE_RETRY_DELAY = 0.10


# =========================================================
# MIMI VOICE LISTENER
# =========================================================


class VoiceListener:

    def __init__(self):

        self.commands = queue.Queue()

        self.running = False
        self.enabled = False
        self.listening = False

        self.thread = None

        self.state_lock = threading.Lock()

        self.last_command_time = 0.0

        # ---------------------------------------------
        # Current Listening Profile
        # ---------------------------------------------

        self.current_profile = "short"

        self.profile_values = {
            "start_timeout": 8.0,
            "end_silence": 0.8,
            "max_speech": 8.0,
        }

        set_vad_profile(
            self.current_profile,
            self.profile_values,
        )

    # =====================================================
    # LISTENING PROFILE
    # =====================================================

    def set_listening_profile(
        self,
        profile,
        values=None,
    ):

        if not profile:
            profile = "short"

        if values is None:
            values = {}

        self.current_profile = str(
            profile
        )

        self.profile_values = dict(
            values
        )

        set_vad_profile(
            self.current_profile,
            self.profile_values,
        )

        print(
            f"🎧 VoiceLoop profile → "
            f"{self.current_profile}"
        )

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True,
        )

        self.thread.start()

        print(
            "🎤 Voice Listener started."
        )

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        self.enabled = False
        self.running = False

        if (
            self.thread is not None
            and
            self.thread.is_alive()
            and
            threading.current_thread()
            is not
            self.thread
        ):

            self.thread.join(
                timeout=1.5
            )

        print(
            "🎤 Voice Listener stopped."
        )

    # =====================================================
    # ENABLE
    # =====================================================

    def enable(self):

        # قبل كل استماع نضمن أن
        # الـVAD يستخدم آخر profile مختار.
        set_vad_profile(
            self.current_profile,
            self.profile_values,
        )

        self.enabled = True

    # =====================================================
    # DISABLE
    # =====================================================

    def disable(self):

        self.enabled = False

    # =====================================================
    # SHOULD CANCEL CURRENT LISTEN
    # =====================================================

    def _should_cancel_listen(self):

        return (
            not self.running
            or
            not self.enabled
        )

    # =====================================================
    # SAFE PAUSE
    # =====================================================

    def pause_and_wait(
        self,
        timeout=3.0,
    ):

        self.enabled = False

        start = time.monotonic()

        while True:

            with self.state_lock:

                currently_listening = (
                    self.listening
                )

            if not currently_listening:
                return True

            if (
                time.monotonic()
                -
                start
                >=
                timeout
            ):

                print(
                    "⚠️ Voice listener "
                    "pause timeout."
                )

                return False

            time.sleep(
                0.03
            )

    # =====================================================
    # QUEUE
    # =====================================================

    def has_command(self):

        return (
            not self.commands.empty()
        )

    def get_command(self):

        try:

            return (
                self.commands.get_nowait()
            )

        except queue.Empty:

            return None

    def clear_commands(self):

        while True:

            try:

                self.commands.get_nowait()

            except queue.Empty:

                break

    # =====================================================
    # RESET MICROPHONE
    # =====================================================

    def reset_microphone(self):

        reset_audio_cache()

        print(
            "🎤 Microphone cache reset."
        )

    # =====================================================
    # WAIT AFTER COMMAND
    # =====================================================

    def _wait_after_command(self):

        started = time.monotonic()

        while self.running:

            if not self.enabled:
                return

            elapsed = (
                time.monotonic()
                -
                started
            )

            if (
                elapsed
                >=
                POST_COMMAND_DELAY
            ):

                return

            time.sleep(
                0.03
            )

    # =====================================================
    # WORKER
    # =====================================================

    def _worker(self):

        while self.running:

            # =================================================
            # LISTENER DISABLED
            # =================================================

            if not self.enabled:

                time.sleep(
                    0.05
                )

                continue

            # =================================================
            # OLD COMMAND WAITING
            # =================================================

            if not self.commands.empty():

                time.sleep(
                    0.05
                )

                continue

            # =================================================
            # APPLY CURRENT PROFILE
            # =================================================

            set_vad_profile(
                self.current_profile,
                self.profile_values,
            )

            print(
                f"🎧 Active listening: "
                f"{self.current_profile}"
            )

            # =================================================
            # START LISTENING
            # =================================================

            with self.state_lock:

                self.listening = True

            try:

                text = listen_once(
                    cancel_check=
                        self._should_cancel_listen
                )

            except Exception as error:

                print()
                print(
                    "❌ Voice listener error:"
                )

                print(
                    error
                )

                text = None

            finally:

                with self.state_lock:

                    self.listening = False

            # =================================================
            # DISABLED WHILE RECORDING?
            # =================================================

            if (
                not self.running
                or
                not self.enabled
            ):

                time.sleep(
                    0.05
                )

                continue

            # =================================================
            # REAL COMMAND
            # =================================================

            if text:

                print()
                print(
                    "📥 Voice command queued."
                )

                self.commands.put(
                    text
                )

                self.last_command_time = (
                    time.monotonic()
                )

                self._wait_after_command()

                continue

            # =================================================
            # NOTHING RECOGNIZED
            # =================================================

            time.sleep(
                IDLE_RETRY_DELAY
            )