import threading
import time

import serial
from serial.tools import list_ports


BAUD_RATE = 115200
READ_TIMEOUT = 0.25
RECONNECT_DELAY = 2.0
HEARTBEAT_TIMEOUT = 7.0
STATUS_PRINT_INTERVAL = 5.0

PREFERRED_PORT_PREFIXES = (
    "/dev/ttyACM",
    "/dev/ttyUSB",
)


class ArduinoBridge:

    def __init__(
        self,
        voice_module=None,
        port=None,
        baud_rate=BAUD_RATE,
    ):
        self.voice = voice_module
        self.port = port
        self.baud_rate = int(baud_rate)

        self.serial_connection = None
        self.running = False
        self.reader_thread = None
        self.connected = False

        self.last_line_time = 0.0
        self.last_heartbeat_time = 0.0
        self.last_status_print = 0.0

        self.last_distance_cm = None
        self.last_shake_strength = None

        self.event_callback = None

        self._serial_lock = threading.Lock()
        self._speak_lock = threading.Lock()

    def find_arduino_port(self):

        ports = list(
            list_ports.comports()
        )

        if not ports:
            return None

        for item in ports:

            text = (
                f"{item.description or ''} "
                f"{item.manufacturer or ''} "
                f"{item.product or ''}"
            ).lower()

            if (
                "arduino" in text
                or
                "mega" in text
            ):
                return item.device

        for prefix in PREFERRED_PORT_PREFIXES:

            for item in ports:

                if item.device.startswith(
                    prefix
                ):
                    return item.device

        return ports[0].device

    def connect(self):

        self.disconnect(
            print_message=False
        )

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

            connection = serial.Serial(
                port=selected_port,
                baudrate=self.baud_rate,
                timeout=READ_TIMEOUT,
                write_timeout=1.0,
            )

            time.sleep(2.4)

            connection.reset_input_buffer()

            with self._serial_lock:
                self.serial_connection = connection

            self.port = selected_port
            self.connected = True

            now = time.monotonic()

            self.last_line_time = now
            self.last_heartbeat_time = now

            print(
                f"✅ Arduino connected: "
                f"{selected_port}"
            )

            return True

        except Exception as error:

            self.connected = False

            print(
                "❌ Arduino connection error:",
                error,
            )

            return False

    def disconnect(
        self,
        print_message=True,
    ):

        with self._serial_lock:

            connection = (
                self.serial_connection
            )

            self.serial_connection = None

        if connection is not None:

            try:
                connection.close()
            except Exception:
                pass

        was_connected = self.connected
        self.connected = False

        if (
            print_message
            and
            was_connected
        ):
            print(
                "🔌 Arduino disconnected."
            )

    def start(self):

        if self.running:
            return

        self.running = True

        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
        )

        self.reader_thread.start()

        print(
            "🔌 Arduino Bridge started."
        )

    def close(self):

        self.running = False

        if (
            self.reader_thread is not None
            and
            self.reader_thread.is_alive()
            and
            threading.current_thread()
            is not
            self.reader_thread
        ):
            self.reader_thread.join(
                timeout=1.5
            )

        self.disconnect(
            print_message=False
        )

        print(
            "🔌 Arduino Bridge closed."
        )

    def set_event_callback(
        self,
        callback,
    ):

        self.event_callback = callback

    def _speak_async(
        self,
        text,
    ):

        def worker():

            if not self._speak_lock.acquire(
                blocking=False
            ):
                print(
                    "🔇 Mimi is already speaking; "
                    "skipping overlapping reaction."
                )
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

    def handle_line(
        self,
        line,
    ):

        line = str(
            line or ""
        ).strip()

        if not line:
            return

        now = time.monotonic()
        self.last_line_time = now

        if line.startswith(
            "HEARTBEAT:"
        ):

            self.last_heartbeat_time = now

            if (
                now - self.last_status_print
                >= STATUS_PRINT_INTERVAL
            ):
                self.last_status_print = now

                print(
                    f"💓 Arduino alive | {line}"
                )

            return

        print(
            f"🔹 Arduino: {line}"
        )

        if line.startswith(
            "DISTANCE_CM:"
        ):

            try:
                self.last_distance_cm = float(
                    line.split(":", 1)[1]
                )
            except Exception:
                pass

            return

        if line.startswith(
            "SHAKE_STRENGTH:"
        ):

            try:
                self.last_shake_strength = float(
                    line.split(":", 1)[1]
                )
            except Exception:
                pass

            return

        if line.startswith(
            "ERROR:"
        ):

            print(
                f"⚠️ Arduino sensor error: "
                f"{line}"
            )

            return

        if not line.startswith(
            "EVENT:"
        ):
            return

        event_name = (
            line.split(":", 1)[1]
            .strip()
        )

        if event_name == "ARDUINO_READY":

            print(
                "✅ Arduino hardware ready."
            )

        elif event_name == "DISTANCE_NEAR":

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

            print(
                f"🛑 Cliff safety: "
                f"{event_name}"
            )

        elif event_name == "MOVE_FORWARD_BLOCKED":

            print(
                "🛑 Forward movement blocked."
            )

        elif event_name == "SPIN_BLOCKED":

            print(
                "🛑 Spin blocked."
            )

        elif event_name == "MOVE_FORWARD_DONE":

            print(
                "✅ Forward 10cm movement done."
            )

        elif event_name == "SPIN_DONE":

            print(
                "✅ Touch spin done."
            )

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

    def _heartbeat_is_stale(self):

        if not self.connected:
            return False

        if self.last_heartbeat_time <= 0:
            return False

        return (
            time.monotonic()
            -
            self.last_heartbeat_time
            >
            HEARTBEAT_TIMEOUT
        )

    def _reader_loop(self):

        while self.running:

            if not self.connected:

                if not self.connect():

                    time.sleep(
                        RECONNECT_DELAY
                    )

                    continue

            if self._heartbeat_is_stale():

                print(
                    "⚠️ Arduino heartbeat lost. "
                    "Reconnecting..."
                )

                self.disconnect()

                time.sleep(
                    RECONNECT_DELAY
                )

                continue

            try:

                with self._serial_lock:
                    connection = (
                        self.serial_connection
                    )

                if connection is None:
                    self.connected = False
                    continue

                raw = connection.readline()

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

                self.disconnect()

                time.sleep(
                    RECONNECT_DELAY
                )


def main():

    from src.modules.voice_module import VoiceModule

    print()
    print("=" * 60)
    print("MIMI ARDUINO STABLE TEST")
    print("=" * 60)

    voice = VoiceModule()
    bridge = None

    try:

        voice.start(
            listening=False
        )

        bridge = ArduinoBridge(
            voice_module=voice
        )

        bridge.start()

        print()
        print(
            "✅ الاختبار شغال."
        )
        print(
            "💓 لازم يظهر Arduino alive كل عدة ثواني."
        )
        print()
        print(
            "1) أقل من 35cm -> 10cm forward + من هنا"
        )
        print(
            "2) هز الروبوت -> يا لقد هززتني"
        )
        print(
            "3) Touch -> لفتين + ويييييي"
        )
        print(
            "4) IR -> حماية الحافة"
        )
        print()
        print(
            "Ctrl+C للخروج."
        )

        while True:
            time.sleep(1.0)

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