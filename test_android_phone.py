"""A test version of AndroidPhone that can be used in some cases.

Not all functions are supported, so you might need to add new functionality to
support your use case.
"""

import pathlib
import tempfile
import typing

import android_phone


class TestAndroidPhone(android_phone.AndroidPhone):
    def __init__(self, episodes_on_phone: set[str]):
        self.temp_dir = tempfile.TemporaryDirectory()
        podcast_directory = pathlib.Path(self.temp_dir.name, "dir")
        history_file = pathlib.Path(self.temp_dir.name, "history.txt")

        super(TestAndroidPhone, self).__init__(
            phone_name="TestAndroidPhone",
            podcast_directory=podcast_directory,
            history_file=history_file,
        )
        self.episodes_on_phone = episodes_on_phone

    def __del__(self) -> None:
        self.temp_dir.cleanup()

    def connect_to_phone(self, retry: bool = True) -> bool:
        return True

    def copy_files_to_phone(
        self, files: typing.List[pathlib.Path]
    ) -> android_phone.CopyFilesToPhoneResults:
        raise NotImplementedError

    def get_podcast_episodes_on_phone(self) -> set[str]:
        return self.episodes_on_phone
