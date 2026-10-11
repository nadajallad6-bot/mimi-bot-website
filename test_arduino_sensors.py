import glob
import time

import serial


# =========================================================
# MIMI BOT
# RASPBERRY PI <-> ARDUINO MEGA TEST
# =========================================================


BAUD_RATE = 9600


# =========================================================
# FIND ARDUINO
# =========================================================

def find_arduino():

    ports = (
        glob.glob(
            "/dev/ttyACM*"
        )
        +
        glob.glob(
            "/dev/ttyUSB*"
        )
    )

    if not ports:

        return None

    print()
    print(
        "Serial ports found:"
    )

    for port in ports:

        print(
            " -",
            port
        )

    return ports[0]


# =========================================================
# CONNECT
# =========================================================

def connect_arduino():

    port = (
        find_arduino()
    )

    if port is None:

        print()
        print(
            "❌ Arduino was not found."
        )

        print(
            "Check the USB cable."
        )

        return None

    print()
    print(
        f"🔌 Connecting to {port}..."
    )

    try:

        arduino = (
            serial.Serial(
                port=port,
                baudrate=BAUD_RATE,
                timeout=0.2,
            )
        )

    except Exception as error:

        print()
        print(
            "❌ Could not open Arduino:"
        )

        print(
            error
        )

        return None

    # Opening serial often resets Arduino.
    time.sleep(
        2.0
    )

    arduino.reset_input_buffer()

    print()
    print(
        "✅ Arduino connected."
    )

    return arduino


# =========================================================
# SEND COMMAND
# =========================================================

def send_command(
    arduino,
    command,
):

    command = str(
        command
    ).strip()

    if not command:

        return

    data = (
        command
        +
        "\n"
    ).encode(
        "utf-8"
    )

    arduino.write(
        data
    )

    arduino.flush()

    print(
        f"➡️ PI -> MEGA: {command}"
    )


# =========================================================
# PROCESS ARDUINO EVENT
# =========================================================

def process_event(
    line,
):

    # =====================================================
    # TOUCH
    # =====================================================

    if (
        line
        ==
        "TOUCH_DETECTED"
    ):

        print()
        print(
            "🤚 TOUCH DETECTED"
        )

        print(
            "Mimi: someone touched me!"
        )

        return


    # =====================================================
    # MOTOR
    # =====================================================

    if (
        line
        ==
        "HAPPY_SPIN"
    ):

        print(
            "💃 Mimi started happy spin."
        )

        return


    if (
        line
        ==
        "HAPPY_SPIN_DONE"
    ):

        print(
            "✅ Happy spin finished."
        )

        return


    # =====================================================
    # DISTANCE
    # =====================================================

    if line.startswith(
        "DISTANCE_NEAR:"
    ):

        try:

            distance_mm = int(
                line.split(
                    ":",
                    1,
                )[1]
            )

            distance_cm = (
                distance_mm
                /
                10.0
            )

        except Exception:

            distance_cm = None

        print()
        print(
            "👋 SOMEONE IS NEAR MIMI"
        )

        if distance_cm is not None:

            print(
                f"Distance: "
                f"{distance_cm:.1f} cm"
            )

        # Later:
        # mimi.say("أهلا")

        return


    if line.startswith(
        "DISTANCE_CLEAR:"
    ):

        try:

            distance_mm = int(
                line.split(
                    ":",
                    1,
                )[1]
            )

            distance_cm = (
                distance_mm
                /
                10.0
            )

        except Exception:

            distance_cm = None

        print()
        print(
            "👋 Person moved away."
        )

        if distance_cm is not None:

            print(
                f"Distance: "
                f"{distance_cm:.1f} cm"
            )

        return


    # =====================================================
    # SHAKE
    # =====================================================

    if line.startswith(
        "SHAKE_DETECTED:"
    ):

        parts = (
            line.split(
                ":"
            )
        )

        accel = None
        gyro = None

        try:

            if len(parts) >= 3:

                accel = float(
                    parts[1]
                )

                gyro = float(
                    parts[2]
                )

        except Exception:

            pass

        print()
        print(
            "🫨 SHAKE DETECTED"
        )

        if (
            accel is not None
            and
            gyro is not None
        ):

            print(
                f"Accel: {accel:.2f} g"
            )

            print(
                f"Gyro : {gyro:.1f} deg/s"
            )

        # Later:
        # mimi.say("ليش بتهزني؟")

        return


    # =====================================================
    # READY
    # =====================================================

    if (
        line
        ==
        "MIMI_MEGA_READY"
    ):

        print()
        print(
            "🤖 Arduino Mega is ready."
        )

        return


    # =====================================================
    # SENSOR STATUS
    # =====================================================

    if line.startswith(
        "DISTANCE_SENSOR:"
    ):

        print(
            "📏",
            line
        )

        return


    if line.startswith(
        "IMU_SENSOR:"
    ):

        print(
            "🧭",
            line
        )

        return


    if line.startswith(
        "IMU_WHO_AM_I:"
    ):

        print(
            "🧭",
            line
        )

        return


    # =====================================================
    # PING
    # =====================================================

    if (
        line
        ==
        "PONG"
    ):

        print(
            "✅ Arduino answered PING."
        )

        return


    # =====================================================
    # OTHER
    # =====================================================

    print(
        "📨",
        line
    )


# =========================================================
# MAIN
# =========================================================

def main():

    arduino = (
        connect_arduino()
    )

    if arduino is None:

        return

    print()
    print("=" * 60)

    print(
        "🤖 MIMI ARDUINO SENSOR TEST"
    )

    print("=" * 60)

    print()
    print(
        "Try:"
    )

    print(
        "1. Touch Mimi"
    )

    print(
        "2. Put your hand within 20 cm"
    )

    print(
        "3. Shake the robot gently"
    )

    print()
    print(
        "Press Ctrl+C to stop."
    )

    print()

    # Test communication
    send_command(
        arduino,
        "PING"
    )

    try:

        while True:

            if (
                arduino.in_waiting
                >
                0
            ):

                raw = (
                    arduino.readline()
                )

                try:

                    line = (
                        raw.decode(
                            "utf-8",
                            errors="ignore",
                        )
                        .strip()
                    )

                except Exception:

                    line = ""

                if line:

                    process_event(
                        line
                    )

            time.sleep(
                0.01
            )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test stopped."
        )

    finally:

        try:

            send_command(
                arduino,
                "STOP"
            )

        except Exception:

            pass

        try:

            arduino.close()

        except Exception:

            pass

        print(
            "✅ Arduino serial closed."
        )


if __name__ == "__main__":

    main()
