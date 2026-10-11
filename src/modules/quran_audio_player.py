import subprocess
import time
from pathlib import Path

from src.vision.mimi_vision import detect_audio_devices
from src.quran.quran_audio_cache import (
    ensure_ayah,
    prefetch_next_ayah,
)


class QuranAudioPlayer:

    def __init__(
        self,
        volume=60,
    ):

        self.volume = max(
            0,
            min(
                100,
                int(volume),
            ),
        )

        self.speaker_device = None

        self.ffmpeg_process = None
        self.aplay_process = None

        self.stop_requested = False
        self.last_interrupted = False

    def detect_speaker(self):

        try:
            _, speaker = detect_audio_devices()
            self.speaker_device = speaker

        except Exception as error:
            print()
            print("⚠️ Speaker detection error:")
            print(error)
            self.speaker_device = None

        return self.speaker_device

    def get_card_number(self):

        if not self.speaker_device:
            return None

        try:
            device = self.speaker_device.split(":", 1)[1]
            return device.split(",", 1)[0]

        except Exception:
            return None

    def set_volume(
        self,
        volume=None,
    ):

        if volume is not None:
            try:
                self.volume = max(
                    0,
                    min(
                        100,
                        int(
                            round(
                                float(volume)
                            )
                        ),
                    ),
                )
            except Exception:
                pass

        if not self.speaker_device:
            self.detect_speaker()

        card = self.get_card_number()

        if card is None:
            return False

        for control in (
            "PCM",
            "Speaker",
            "Master",
        ):

            try:
                result = subprocess.run(
                    [
                        "amixer",
                        "-c",
                        str(card),
                        "sset",
                        control,
                        f"{self.volume}%",
                        "unmute",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )

                if result.returncode == 0:
                    print(
                        f"🔊 Quran volume: "
                        f"{self.volume}%"
                    )
                    return True

            except Exception:
                continue

        print("⚠️ Could not change Quran volume.")
        return False

    def lower_volume(
        self,
        step=15,
    ):

        try:
            step = abs(int(step))
        except Exception:
            step = 15

        return self.set_volume(
            self.volume - step
        )

    def raise_volume(
        self,
        step=15,
    ):

        try:
            step = abs(int(step))
        except Exception:
            step = 15

        return self.set_volume(
            self.volume + step
        )

    def ensure_ayah(
        self,
        surah_number,
        ayah_number,
    ):

        try:
            return ensure_ayah(
                surah_number,
                ayah_number,
            )

        except Exception as error:
            print()
            print("❌ Could not prepare Quran ayah:")
            print(error)
            return None

    def is_playing(self):

        for process in (
            self.aplay_process,
            self.ffmpeg_process,
        ):

            if (
                process is not None
                and
                process.poll() is None
            ):
                return True

        return False

    def stop(self):

        self.stop_requested = True
        self.last_interrupted = True

        stopped = False

        for process in (
            self.aplay_process,
            self.ffmpeg_process,
        ):

            if process is None:
                continue

            try:
                if process.poll() is None:
                    process.terminate()
                    stopped = True

                    try:
                        process.wait(timeout=0.6)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=0.6)

            except Exception:
                pass

        if stopped:
            print()
            print("🛑 Quran playback stopped.")

        return stopped

    def _clear_processes(self):

        self.aplay_process = None
        self.ffmpeg_process = None

    def play_ayah(
        self,
        surah_number,
        ayah_number,
        prefetch=True,
        control_callback=None,
    ):

        try:
            surah_number = int(surah_number)
            ayah_number = int(ayah_number)

        except Exception:
            print("❌ Invalid Quran ayah numbers.")
            return False

        print()
        print(
            f"📖 Preparing Surah {surah_number}, "
            f"Ayah {ayah_number}..."
        )

        audio_path = self.ensure_ayah(
            surah_number,
            ayah_number,
        )

        if audio_path is None:
            print()
            print(
                f"❌ Quran audio unavailable: "
                f"{surah_number}:{ayah_number}"
            )
            return False

        if prefetch:
            try:
                prefetch_next_ayah(
                    surah_number,
                    ayah_number,
                )
            except Exception as error:
                print()
                print("⚠️ Quran prefetch error:")
                print(error)

        return self.play(
            audio_path,
            control_callback=control_callback,
        )

    def play(
        self,
        audio_file,
        control_callback=None,
    ):

        audio_file = Path(audio_file)

        if not audio_file.exists():
            print()
            print("❌ Quran audio not found:")
            print(audio_file)
            return False

        if not self.speaker_device:
            self.detect_speaker()

        if not self.speaker_device:
            print("❌ No speaker found.")
            return False

        self.set_volume()

        print()
        print("📖 Playing Quran:")
        print(audio_file)

        self.stop_requested = False
        self.last_interrupted = False

        # MP3 -> ffmpeg -> raw PCM -> aplay
        # This keeps playback controllable while it is running.
        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(audio_file),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "pipe:1",
        ]

        aplay_cmd = [
            "aplay",
            "-q",
            "-D",
            self.speaker_device,
            "-f",
            "S16_LE",
            "-c",
            "1",
            "-r",
            "44100",
        ]

        ffmpeg_process = None
        aplay_process = None

        try:
            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            self.ffmpeg_process = ffmpeg_process

            aplay_process = subprocess.Popen(
                aplay_cmd,
                stdin=ffmpeg_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self.aplay_process = aplay_process

            if ffmpeg_process.stdout is not None:
                ffmpeg_process.stdout.close()

            while aplay_process.poll() is None:

                if self.stop_requested:
                    break

                if callable(control_callback):
                    try:
                        command = control_callback()
                    except Exception as error:
                        print(
                            "⚠️ Quran control callback error:",
                            error,
                        )
                        command = None

                    if command == "stop":
                        self.stop()
                        break

                time.sleep(0.04)

            if self.stop_requested:
                self.stop()
                self._clear_processes()
                return False

            aplay_rc = aplay_process.returncode

            try:
                ffmpeg_rc = ffmpeg_process.wait(
                    timeout=2.0
                )
            except subprocess.TimeoutExpired:
                ffmpeg_process.kill()
                ffmpeg_rc = ffmpeg_process.wait(
                    timeout=1.0
                )

            self._clear_processes()

            if aplay_rc != 0:
                print(
                    f"❌ Quran aplay failed "
                    f"with code: {aplay_rc}"
                )
                return False

            if ffmpeg_rc not in (
                0,
                None,
            ):
                print(
                    f"❌ Quran ffmpeg failed "
                    f"with code: {ffmpeg_rc}"
                )
                return False

            print("✅ Quran audio finished.")
            return True

        except KeyboardInterrupt:
            self.stop()
            return False

        except FileNotFoundError as error:
            print()
            print("❌ ffmpeg/aplay not found:")
            print(error)
            return False

        except Exception as error:
            print()
            print("❌ Quran player error:")
            print(error)
            return False

        finally:
            for process in (
                aplay_process,
                ffmpeg_process,
            ):

                if process is None:
                    continue

                try:
                    if process.poll() is None:
                        process.terminate()
                except Exception:
                    pass

            self._clear_processes()


def test_player():

    player = QuranAudioPlayer(
        volume=60
    )

    speaker = player.detect_speaker()

    print()
    print(
        f"🔊 Speaker: {speaker}"
    )

    print()
    print("=" * 60)
    print("📖 QURAN AUDIO ON-DEMAND TEST")
    print("=" * 60)

    success = player.play_ayah(
        67,
        1,
        prefetch=True,
    )

    print()
    print(
        "RESULT:",
        success,
    )


if __name__ == "__main__":
    test_player()
