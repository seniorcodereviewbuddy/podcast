import pathlib
import subprocess

# TODO: Include these as part of the git repo.
# TODO: Also verify adb is installed.
ANDROID_AVD_NAME = "Pixel_8_API_34"
SECOND_ANDROID_AVD_NAME = "Copy_of_Pixel_8_API_34"
MAX_TIMEOUT_FOR_EMULATOR_TO_CLOSE = 20


class AndroidEmulator:
    def __init__(self, avd_name: str = ANDROID_AVD_NAME, port: int = 5554):
        # The port must be between 5554 and 5682, and even.
        assert port % 2 == 0
        assert 5554 <= port <= 5682
        self.avd_name = avd_name
        self.id = f"emulator-{port}"
        self.device_ready = False

        args = [
            "emulator",
            f"@{avd_name}",
            "-no-snapshot",
            "-no-window",
            "-port",
            f"{port}",
        ]

        self.emulator_process = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _del_(self) -> None:
        # Tell the emulator to shut itself off.
        args = ["adb", "-s", self.id, "shell", "reboot", "-p"]
        subprocess.run(args, check=True)

        # Once the emulator has finished turning itself off, the process should exit.
        # We'll wait for this to happen, but with a timeout to raise an exception
        # in case there is an issue.
        self.emulator_process.wait(MAX_TIMEOUT_FOR_EMULATOR_TO_CLOSE)

    def wait_until_ready(self) -> None:
        if self.device_ready:
            return

        print("Waiting for device to start")
        args = ["adb", "-s", self.id, "wait-for-device"]
        subprocess.run(args, check=True)
        print("Device started")

        print("Waiting for device boot to complete")
        args = [
            "adb",
            "-s",
            self.id,
            "shell",
            "while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done;",
        ]
        subprocess.run(args, check=True)
        print("Device boot completed")

        self.device_ready = True

    def create_new_podcast_folder(self) -> pathlib.Path:
        # We have to wait for the phone to be ready as we can't create the folder if it isn't.
        self.wait_until_ready()

        args = ["adb", "-s", self.id, "shell", "mktemp", "-d"]
        results = subprocess.run(args, text=True, stdout=subprocess.PIPE, check=True)
        return pathlib.Path(results.stdout.strip())

    def delete_files(self, files: list[str]) -> None:
        for file in files:
            args = ["adb", "-s", self.id, "shell", "rm", f"'{file}'"]
            subprocess.run(args, text=True, stdout=subprocess.PIPE, check=True)
