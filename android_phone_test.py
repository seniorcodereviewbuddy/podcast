import os
import pathlib
import shutil
import tempfile
import typing
import unittest
from unittest import mock

import android_phone
import test_utils


def make_test_mp3(path: pathlib.Path) -> None:
    test_file = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
    shutil.copyfile(test_file, path)


def split(x: typing.List[str]) -> typing.Tuple[typing.List[str], typing.List[str]]:
    midpoint = len(x) // 2
    return x[:midpoint], x[midpoint:]


class MockProcess(object):
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


class TestAndroidPhone(unittest.TestCase):
    def setUp(self) -> None:
        self.phone_name = "fake_id"
        self.root = tempfile.TemporaryDirectory()

        self.android_history_log_file = tempfile.NamedTemporaryFile(delete=False)
        self.android_history_log_file.close()

        self.holding_dir = pathlib.Path(self.root.name, "holding")
        self.phone_folder = pathlib.Path(self.root.name, "phone")

        os.makedirs(self.holding_dir)
        os.makedirs(self.phone_folder)

        self.phone = android_phone.AndroidPhone(
            self.phone_name,
            self.phone_folder,
            pathlib.Path(self.android_history_log_file.name),
        )

    def tearDown(self) -> None:
        self.root.cleanup()

    @mock.patch("subprocess.run")
    def test_IsConnected_NoDevices(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess("List of devices attached", 0)
        self.assertFalse(self.phone.connected_to_phone(retry=False))

    @mock.patch("subprocess.run")
    def test_IsConnected_ConnectedNotAuthorized(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess(
            "List of devices attached\nfake_id  unauthorized", 0
        )
        self.assertFalse(self.phone.connected_to_phone(retry=False))

    @mock.patch("subprocess.run")
    def test_IsConnected_ConnectedAuthorized(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess(
            "List of devices attached\nfake_id  device", 0
        )
        self.assertTrue(self.phone.connected_to_phone(retry=False))

    @mock.patch("subprocess.run")
    def test_copy_files_to_phone(self, mock_run: mock.Mock) -> None:
        podcast_episodes = [
            pathlib.Path(self.holding_dir, "test_podcast_%d.mp3" % x) for x in range(5)
        ]
        for podcast in podcast_episodes:
            make_test_mp3(podcast)

        mock_run.return_value = MockProcess("Success", 0)

        results = self.phone.copy_files_to_phone(podcast_episodes)
        self.assertCountEqual([], results.failed_to_copy)
        self.assertCountEqual(podcast_episodes, results.copied)

        for podcast in podcast_episodes:
            podcast_name = podcast.name
            expected_destination = pathlib.Path(self.phone_folder, podcast_name)
            mock_run.assert_any_call(
                [
                    "adb",
                    "-s",
                    self.phone_name,
                    "push",
                    str(podcast),
                    expected_destination.as_posix(),
                ]
            )

    @mock.patch("subprocess.run")
    def test_CopyFilesToPhone_NoPhoneFound(self, mock_run: mock.Mock) -> None:
        mock_run.side_effect = [
            MockProcess("adb: work", returncode=0),
            MockProcess("adb: error", returncode=1),
            MockProcess("adb: work", returncode=0),
        ]

        podcast_episodes = [
            pathlib.Path(self.holding_dir, "test_podcast_%d.mp3" % x) for x in range(3)
        ]
        for podcast in podcast_episodes:
            make_test_mp3(podcast)

        results = self.phone.copy_files_to_phone(podcast_episodes)
        self.assertCountEqual(podcast_episodes[1:2], results.failed_to_copy)
        self.assertCountEqual(
            podcast_episodes[:1] + podcast_episodes[2:], results.copied
        )

        for index, podcast in enumerate(podcast_episodes):
            podcast_name = os.path.basename(podcast)
            expected_destination = pathlib.Path(self.phone_folder, podcast_name)
            mock_run.assert_any_call(
                [
                    "adb",
                    "-s",
                    self.phone_name,
                    "push",
                    str(podcast),
                    expected_destination.as_posix(),
                ]
            )

    @mock.patch("subprocess.run")
    def test_CopyFilesToPhone_OddFileEncoding(self, mock_run: mock.Mock) -> None:
        podcast_episodes = [
            pathlib.Path(self.holding_dir, test_utils.MP3_DIFFERENT_TITLE_ENCODING),
            pathlib.Path(self.holding_dir, test_utils.M4A_DIFFERENT_TITLE_ENCODING),
        ]

        for podcast_episode in podcast_episodes:
            test_file_source = pathlib.Path(
                test_utils.TEST_DATA_DIR, podcast_episode.name
            )
            shutil.copyfile(test_file_source, podcast_episode)

        mock_run.return_value = MockProcess("Success", 0)

        results = self.phone.copy_files_to_phone(podcast_episodes)
        self.assertCountEqual([], results.failed_to_copy)
        self.assertCountEqual(podcast_episodes, results.copied)

        for podcast in podcast_episodes:
            podcast_name = os.path.basename(podcast)
            expected_destination = pathlib.Path(self.phone_folder, podcast_name)
            mock_run.assert_any_call(
                [
                    "adb",
                    "-s",
                    self.phone_name,
                    "push",
                    str(podcast),
                    expected_destination.as_posix(),
                ]
            )

    @mock.patch("subprocess.run")
    def test_get_podcast_episodes_on_phone(self, mock_run: mock.Mock) -> None:
        all_files = ["test_podcast_%d" % x for x in range(10)]

        mock_run.return_value = MockProcess("\n".join(all_files))

        files_found_on_phone = self.phone.get_podcast_episodes_on_phone()

        self.assertSetEqual(files_found_on_phone, set(all_files))

    @mock.patch("subprocess.run")
    def test_GetPodcastEpisodesOnPhone_OddEncoding(self, mock_run: mock.Mock) -> None:
        all_files = [
            test_utils.MP3_DIFFERENT_TITLE_ENCODING,
            test_utils.M4A_DIFFERENT_TITLE_ENCODING,
        ]

        mock_run.return_value = MockProcess("\n".join(all_files))

        files_found_on_phone = self.phone.get_podcast_episodes_on_phone()

        self.assertSetEqual(files_found_on_phone, set(all_files))

    @mock.patch("subprocess.run")
    def test_ConnectedToPhone_PhonePresent(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess(
            "List of devices attached\n%s device" % (self.phone_name,)
        )
        self.assertTrue(self.phone.connected_to_phone())

    @mock.patch("subprocess.run")
    def test_ConnectedToPhone_PhoneNotPresent(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess("List of devices attached\n")
        self.assertFalse(self.phone.connected_to_phone(retry=False))

    @mock.patch("subprocess.run")
    def test_ConnectedToPhone_ADBError(self, mock_run: mock.Mock) -> None:
        mock_run.return_value = MockProcess("Error", returncode=1)
        self.assertFalse(self.phone.connected_to_phone(retry=False))


if __name__ == "__main__":
    unittest.main()
