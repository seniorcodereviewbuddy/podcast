import pathlib
import tempfile
import typing
import unittest

import android_emulator
import android_phone
import test_utils


class IntegrationTestAndroidPhone(unittest.TestCase):
    phone_emulator: typing.ClassVar[android_emulator.AndroidEmulator]

    @classmethod
    def setUpClass(cls) -> None:
        cls.phone_emulator = android_emulator.AndroidEmulator()
        cls.phone_emulator.WaitUntilReady()

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.phone_emulator

    def setUp(self) -> None:
        self.root = tempfile.TemporaryDirectory()

        self.android_history_log_file = tempfile.NamedTemporaryFile(delete=False)
        self.android_history_log_file.close()

        self.phone_folder = (
            IntegrationTestAndroidPhone.phone_emulator.CreateNewPodcastFolder()
        )

        self.phone = android_phone.AndroidPhone(
            IntegrationTestAndroidPhone.phone_emulator.id,
            self.phone_folder,
            pathlib.Path(self.android_history_log_file.name),
        )

    def tearDown(self) -> None:
        self.root.cleanup()

    def testCopyFilesToCopyFilesToPhone(self) -> None:
        files_to_copy = [
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(
                test_utils.TEST_DATA_DIR, test_utils.MP3_DIFFERENT_TITLE_ENCODING
            ),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM),
        ]

        results = self.phone.CopyFilesToPhone(files_to_copy)
        self.assertCountEqual([], results.failed_to_copy)
        self.assertCountEqual(files_to_copy, results.copied)

    def testGetPodcastEpisodesOnPhone(self) -> None:
        files_to_copy = [
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(
                test_utils.TEST_DATA_DIR, test_utils.MP3_DIFFERENT_TITLE_ENCODING
            ),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_WITH_MULTIPLE_UTF8),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_WITH_EMOJI),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM),
        ]

        self.assertCountEqual(self.phone.GetPodcastEpisodesOnPhone(), [])

        results = self.phone.CopyFilesToPhone(files_to_copy)
        self.assertCountEqual([], results.failed_to_copy)
        self.assertCountEqual(files_to_copy, results.copied)

        expected_files_on_phone = [x.name for x in files_to_copy]
        self.assertCountEqual(
            self.phone.GetPodcastEpisodesOnPhone(), expected_files_on_phone
        )


if __name__ == "__main__":
    unittest.main()
