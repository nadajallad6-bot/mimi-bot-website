import threading
import time
from pathlib import Path

import serial
from serial.tools import list_ports


# =========================================================
# SETTINGS
# =========================================================

BAUD_RATE = 115200
READ_TIMEOUT = 0.20
RECONNECT_DELAY = 2.0

# Common Arduino Mega serial ports on Raspberry Pi/Linux.
PREFERRED_PORT_PREFIXES = (
    "/dev/ttyACM",
    "/dev/ttyUSB",
)


# =========================================================
# ARDUINO BRIDGE
# =========================================================

class ArduinoBridge:
    """
    Raspberry Pi <-> Arduino Mega bridge for Mimi Bot.

    Arduino is responsible for real-time hardware safety
    and motor/sensor behavior.

    Raspberry Pi receives high-level events and handles
    speech / AI / application logic.
    """

    def __init__(
        self,
        voice_module=None,
        port=None,
        baud_rate=BAUD_RATE,
    ):
        self.voice = voice_module
        self.port = port
        self.baud_rate = int(
            baud_rate
        )

        self.serial_connection = None

        self.running = False
        self.thread = None

        self.connected = False

        self.last_distance_cm = None
        self.last_shake_strength = None

        self.event_callback = None

        self._speak_lock = threading.Lock()

    # =====================================================
    # PORT DISCOVERY
    # =====================================================

    def find_arduino_port(self):

        ports = list(
            list_ports.comports()
        )

        if not ports:
            return None

        # 1) Prefer ports whose metadata says Arduino.
        for item in ports:

            text = (
                f"{item.description} "
                f"{item.manufacturer or ''} "
                f"{item.product or ''}"
            ).lower()

            if (
                "arduino" in text
                or
                "mega" in text
            ):
                return item.device

        # 2) Prefer normal Linux serial device names.
        for prefix in PREFERRED_PORT_PREFIXES:

            for item in ports:

                if item.device.startswith(
                    prefix
                ):
                    return item.device

        return ports[0].device

    # =====================================================
    # CONNECT
    # =====================================================

    def connect(self):

        if (
            self.serial_connection is not None
            and
            self.serial_connection.is_open
        ):
            return True

        selected_port = (
            self.port
            or
            self.find_arduino_port()
        )

        if not selected_port:

            print(
                "❌ Arduino serial port not found."
            )

            return False

        try:

            self.serial_connection = (
                serial.Serial(
                    port=
                        selected_port,

                    baudrate=
                        self.baud_rate,

                    timeout=
                        READ_TIMEOUT,
                )
            )

            self.port = selected_port

            # Arduino Mega may reset when serial opens.
            time.sleep(
                2.2
            )

            self.connected = True

            print(
                f"✅ Arduino connected: "
                f"{self.port}"
            )

            return True

        except Exception as error:

            self.connected = False

            print(
                "❌ Arduino connection error:",
                error,
            )

            return False

    # =====================================================
    # START / STOP
    # =====================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=
                self._reader_loop,

            daemon=
                True,
        )

        self.thread.start()

        print(
            "🔌 Arduino Bridge started."
        )

    def close(self):

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

        try:

            if (
                self.serial_connection
                is not None
            ):
                self.serial_connection.close()

        except Exception:
            pass

        self.serial_connection = None
        self.connected = False

        print(
            "🔌 Arduino Bridge closed."
        )

    # =====================================================
    # CALLBACK
    # =====================================================

    def set_event_callback(
        self,
        callback,
    ):

        self.event_callback = callback

    # =====================================================
    # SPEAK
    # =====================================================

    def _speak_async(
        self,
        text,
    ):

        def worker():

            # Avoid multiple hardware reactions speaking
            # over each other.
            if not self._speak_lock.acquire(
                blocking=False
            ):
                return

            try:

                if self.voice is None:

                    print(
                        f"🤖 Mimi: {text}"
                    )

                    return

                self.voice.say(
                    text,
                    resume_listening=False,
                )

            except Exception as error:

                print(
                    "⚠️ Hardware voice error:",
                    error,
                )

            finally:

                self._speak_lock.release()

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    # =====================================================
    # EVENT HANDLER
    # =====================================================

    def handle_line(
        self,
        line,
    ):

        line = str(
            line or ""
        ).strip()

        if not line:
            return

        print(
            f"🔹 Arduino: {line}"
        )

        # ---------------------------------------------
        # Telemetry
        # ---------------------------------------------

        if line.startswith(
            "DISTANCE_CM:"
        ):

            try:

                self.last_distance_cm = float(
                    line.split(
                        ":",
                        1,
                    )[1]
                )

            except Exception:
                pass

            return

        if line.startswith(
            "SHAKE_STRENGTH:"
        ):

            try:

                self.last_shake_strength = float(
                    line.split(
                        ":",
                        1,
                    )[1]
                )

            except Exception:
                pass

            return

        # ---------------------------------------------
        # High-level events
        # ---------------------------------------------

        if not line.startswith(
            "EVENT:"
        ):
            return

        event_name = (
            line.split(
                ":",
                1,
            )[1]
            .strip()
        )

        if event_name == "DISTANCE_NEAR":

            # Requested phrase.
            self._speak_async(
                "من هنا"
            )

        elif event_name == "SHAKE":

            self._speak_async(
                "يااا، لقد هززتني!"
            )

        elif event_name == "TOUCH":

            self._speak_async(
                "ويييييي!"
            )

        elif event_name in {
            "IR_FRONT",
            "IR_RIGHT",
            "IR_BACK",
            "IR_LEFT",
        }:

            # IR acts mainly as silent safety.
            # We print it instead of talking every time.
            print(
                f"🛑 Cliff safety: {event_name}"
            )

        elif event_name == "MOVE_FORWARD_BLOCKED":

            print(
                "🛑 Forward movement blocked by IR safety."
            )

        elif event_name == "SPIN_BLOCKED":

            print(
                "🛑 Spin blocked by IR safety."
            )

        # Optional higher-level integration hook.
        if self.event_callback is not None:

            try:

                self.event_callback(
                    event_name
                )

            except Exception as error:

                print(
                    "⚠️ Arduino callback error:",
                    error,
                )

    # =====================================================
    # READER LOOP
    # =====================================================

    def _reader_loop(self):

        while self.running:

            if (
                self.serial_connection
                is None
                or
                not self.serial_connection.is_open
            ):

                if not self.connect():

                    time.sleep(
                        RECONNECT_DELAY
                    )

                    continue

            try:

                raw = (
                    self.serial_connection.readline()
                )

                if not raw:
                    continue

                line = raw.decode(
                    "utf-8",
                    errors="ignore",
                ).strip()

                self.handle_line(
                    line
                )

            except Exception as error:

                print(
                    "⚠️ Arduino serial read error:",
                    error,
                )

                self.connected = False

                try:

                    if (
                        self.serial_connection
                        is not None
                    ):
                        self.serial_connection.close()

                except Exception:
                    pass

                self.serial_connection = None

                time.sleep(
                    RECONNECT_DELAY
                )


# =========================================================
# SIMPLE STANDALONE TEST
# =========================================================

def main():

    from src.modules.voice_module import VoiceModule

    print()
    print("=" * 60)
    print("MIMI ARDUINO BRIDGE TEST")
    print("=" * 60)

    voice = VoiceModule()

    bridge = None

    try:

        # We do not need microphone listening in this
        # hardware-only test.
        voice.start(
            listening=False
        )

        bridge = ArduinoBridge(
            voice_module=
                voice
        )

        bridge.start()

        print()
        print(
            "✅ Ready."
        )
        print(
            "جرّبي الآن:"
        )
        print(
            "- اقتربي أقل من 35 سم"
        )
        print(
            "- هزّي الروبوت"
        )
        print(
            "- المسِي Touch sensor"
        )
        print(
            "- قرّبي أحد IR من حافة الطاولة"
        )
        print()
        print(
            "Ctrl+C للخروج."
        )

        while True:
            time.sleep(
                1.0
            )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test stopped."
        )

    finally:

        if bridge is not None:
            bridge.close()

        voice.close()


if __name__ == "__main__":
    main()

