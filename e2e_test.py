import json
import os
import pathlib
import shutil
import tempfile
import typing
import unittest
from unittest import mock

import android_emulator
import android_phone
import podcast_show
import prepare_for_phone
import settings
import test_utils


class TestE2E(unittest.TestCase):
    phone_emulator: typing.ClassVar[android_emulator.AndroidEmulator]

    @classmethod
    def setUpClass(cls) -> None:
        cls.phone_emulator = android_emulator.AndroidEmulator()
        cls.phone_emulator.wait_until_ready()

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.phone_emulator

    def setUp(self) -> None:
        self.root = tempfile.TemporaryDirectory()

        # Verify the emulator is ready and we can connect.
        self.assertTrue(android_phone.is_phone_connected(TestE2E.phone_emulator.id))

    def tearDown(self) -> None:
        self.root.cleanup()

    def default_shows(self) -> list[podcast_show.PodcastShow]:
        # TODO: Maybe these shouldn't be living in the same folder? Or they should be
        # handled in a better way.
        return [
            podcast_show.PodcastShow(
                pathlib.Path("Add To Phone"), podcast_show.PRIORITY_SKIP
            ),
            podcast_show.PodcastShow(
                pathlib.Path("Archive"), podcast_show.PRIORITY_SKIP
            ),
            podcast_show.PodcastShow(
                pathlib.Path("On Phone"), podcast_show.PRIORITY_SKIP
            ),
        ]

    def create_test_settings(
        self,
        phone_id: str,
        android_podcast_folder: pathlib.Path,
        computer_podcast_folder: pathlib.Path,
        podcasts: typing.Optional[list[podcast_show.PodcastShow]] = None,
        hours_to_add: int = 0,
    ) -> settings.Settings:
        processed_folder = pathlib.Path(computer_podcast_folder, "Add To Phone")

        archive_folder = pathlib.Path(computer_podcast_folder, "Archive")

        backup_folder = pathlib.Path(computer_podcast_folder, "On Phone")

        user_data_folder = pathlib.Path(self.root.name, "user_data")

        raw_settings = {
            "ANDROID_PHONE_ID": phone_id,
            "PODCAST_DIRECTORY_ON_PHONE": f"{android_podcast_folder}",
            "NUM_OLDEST_EPISODES_TO_ADD": 1,
            "TIME_OF_PODCASTS_TO_ADD_IN_HOURS": f"{hours_to_add}",
            "PODCAST_FOLDER": f"{computer_podcast_folder}",
            "PROCESSED_FILE_BOARDING_ZONE_FOLDER": f"{processed_folder}",
            "ARCHIVE_FOLDER": f"{archive_folder}",
            "BACKUP_FOLDER": f"{backup_folder}",
            "USER_DATA_FOLDER": f"{user_data_folder}",
        }

        settings_file = pathlib.Path(self.root.name, "user_settings.json")
        with open(settings_file, "w") as f:
            f.write(json.dumps(raw_settings))
        user_podcasts = podcasts if podcasts else []
        specified_files: typing.Dict[pathlib.Path, typing.List[pathlib.Path]] = {}

        return settings.Settings(
            settings_file,
            user_podcasts,
            specified_files,
        )

    def _PopulatePodcastShow(
        self,
        podcast_dir: pathlib.Path,
        num_episodes: int = 10,
        episodes_start_time: int = 1000,
        file_prefix: str = "",
    ) -> list[pathlib.Path]:
        podcast_folder = pathlib.Path(self.root.name, podcast_dir)
        podcast_folder.mkdir(exist_ok=True)

        test_files = [
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM),
            pathlib.Path(
                test_utils.TEST_DATA_DIR, test_utils.MP3_DIFFERENT_TITLE_ENCODING
            ),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_WITH_EMOJI),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_WITH_MULTIPLE_UTF8),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE),
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM),
            pathlib.Path(
                test_utils.TEST_DATA_DIR, test_utils.M4A_DIFFERENT_TITLE_ENCODING
            ),
        ]

        show_files = []
        for x in range(num_episodes):
            test_file = test_files[x % len(test_files)]
            new_file_name = file_prefix + test_file.stem + str(x + 1) + test_file.suffix
            copied_file = pathlib.Path(podcast_folder, new_file_name)
            show_files.append(copied_file)

            shutil.copyfile(
                test_file,
                copied_file,
            )

            new_time = episodes_start_time + 100 * x
            os.utime(copied_file, (new_time, new_time))

        return show_files

    @mock.patch("builtins.input")
    def testFullEndToEndTest_NoShows_NoCopyToPhone(self, user_input: mock.Mock) -> None:
        user_input.side_effect = [
            # Continue to Priority 1?
            "N",
            # Copy Files?
            "N",
        ]

        args: list[str] = []
        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()
        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
        )
        prepare_for_phone.main(args, test_settings)

    @mock.patch("builtins.input")
    def testFullEndToEndTest_WithShow_CopyToPhone_OneFile(
        self, user_input: mock.Mock
    ) -> None:
        user_input.side_effect = [
            # Initial for show 1.
            "Y",
            # Copy Files?
            "Y",
        ]

        args: list[str] = []

        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()

        podcast_show_folder = podcast_folder.joinpath("show_1")
        podcast_shows = self.default_shows() + [
            podcast_show.PodcastShow(podcast_show_folder, podcast_show.P1),
        ]

        episodes = self._PopulatePodcastShow(podcast_show_folder)

        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
            podcast_shows,
            hours_to_add=0,
        )

        prepare_for_phone.main(args, test_settings)

        # Since hours_to_add is 0, only 1 file should be added.
        expected_files_on_phone = [episodes[0].name]

        phone = android_phone.AndroidPhone(
            TestE2E.phone_emulator.id,
            test_settings.PodcastDirectoryOnPhone,
            test_settings.AndroidHistory,
        )
        self.assertCountEqual(
            expected_files_on_phone, phone.get_podcast_episodes_on_phone()
        )

        files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
        self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)

    @mock.patch("builtins.input")
    def testFullEndToEndTest_WithShow_CopyToPhone_OneFile_TwoPhonesActive(
        self, user_input: mock.Mock
    ) -> None:
        # Create another android emulator on a different port.
        # This shouldn't have any impact on the other emulator working.
        second_emulator = android_emulator.AndroidEmulator(
            avd_name=android_emulator.SECOND_ANDROID_AVD_NAME, port=5556
        )
        second_emulator.wait_until_ready()

        user_input.side_effect = [
            # Initial for show 1.
            "Y",
            # Copy Files?
            "Y",
        ]

        args: list[str] = []

        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()

        podcast_show_folder = podcast_folder.joinpath("show_1")
        podcast_shows = self.default_shows() + [
            podcast_show.PodcastShow(podcast_show_folder, podcast_show.P1),
        ]

        episodes = self._PopulatePodcastShow(podcast_show_folder)

        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
            podcast_shows,
            hours_to_add=0,
        )

        prepare_for_phone.main(args, test_settings)

        # Since hours_to_add is 0, only 1 file should be added.
        expected_files_on_phone = [episodes[0].name]

        phone = android_phone.AndroidPhone(
            TestE2E.phone_emulator.id,
            test_settings.PodcastDirectoryOnPhone,
            test_settings.AndroidHistory,
        )
        self.assertCountEqual(
            expected_files_on_phone, phone.get_podcast_episodes_on_phone()
        )

        files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
        self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)

    @mock.patch("builtins.input")
    def testFullEndToEndTest_WithShow_CopyToPhone_AllFiles(
        self, user_input: mock.Mock
    ) -> None:
        user_input.side_effect = [
            # Initial for show 1.
            "Y",
            # Continue with priority 1?
            "N",
            # Copy Files.
            "Y",
        ]

        args: list[str] = []

        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()
        podcast_show_folder = podcast_folder.joinpath("show_1")
        podcast_shows = self.default_shows() + [
            podcast_show.PodcastShow(podcast_show_folder, podcast_show.P0),
        ]

        episodes = self._PopulatePodcastShow(podcast_show_folder)

        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
            podcast_shows,
            hours_to_add=100,
        )

        prepare_for_phone.main(args, test_settings)

        # Since hours_to_add is bigger than all the files together, we should have added every file.
        expected_files_on_phone = [x.name for x in episodes]

        phone = android_phone.AndroidPhone(
            TestE2E.phone_emulator.id,
            test_settings.PodcastDirectoryOnPhone,
            test_settings.AndroidHistory,
        )

        self.assertCountEqual(
            expected_files_on_phone, phone.get_podcast_episodes_on_phone()
        )

        files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
        self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)

    @mock.patch("builtins.input")
    def testFullEndToEndTest_WithShow_CopyToPhone_MultipleTimes(
        self, user_input: mock.Mock
    ) -> None:
        times_to_run = 5
        user_input.side_effect = [
            # Initial for show 1.
            "Y",
            # Copy Files?
            "Y",
        ] * times_to_run

        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()

        podcast_show_folder = pathlib.Path(podcast_folder, "show_1")
        episodes = self._PopulatePodcastShow(podcast_show_folder)

        args: list[str] = []
        podcast_shows = self.default_shows() + [
            podcast_show.PodcastShow(podcast_show_folder, podcast_show.P1),
        ]

        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
            podcast_shows,
            hours_to_add=0,
        )

        for run_count in range(times_to_run):
            prepare_for_phone.main(args, test_settings)

            # Since we only add 1 file per run, we should have run_count + 1 files.
            expected_files_on_phone = [x.name for x in episodes[: run_count + 1]]

            phone = android_phone.AndroidPhone(
                TestE2E.phone_emulator.id,
                test_settings.PodcastDirectoryOnPhone,
                test_settings.AndroidHistory,
            )
            self.assertCountEqual(
                expected_files_on_phone, phone.get_podcast_episodes_on_phone()
            )

            files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
            self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)

    @mock.patch("builtins.input")
    def testFullEndToEndTest_WithShow_CopyToPhone_DeleteSomeEpisodes_CopyAgain(
        self, user_input: mock.Mock
    ) -> None:
        user_input.side_effect = [
            # Initial for show 1. Run 2.
            "Y",
            # Continue with priority 1? Run 1.
            "N",
            # Copy Files. Run 1.
            "Y",
        ]

        args: list[str] = []

        podcast_folder = pathlib.Path(self.root.name, "Podcasts")
        podcast_folder.mkdir()
        podcast_show_folder = podcast_folder.joinpath("show_1")

        podcast_shows = self.default_shows() + [
            podcast_show.PodcastShow(podcast_show_folder, podcast_show.P0),
        ]

        episodes = self._PopulatePodcastShow(
            podcast_show_folder,
            file_prefix="batch_1_",
        )

        test_settings = self.create_test_settings(
            TestE2E.phone_emulator.id,
            TestE2E.phone_emulator.create_new_podcast_folder(),
            podcast_folder,
            podcast_shows,
            hours_to_add=100,
        )

        prepare_for_phone.main(args, test_settings)

        # Since hours_to_add is bigger than all the files together, we should have added every file.
        expected_files_on_phone = [x.name for x in episodes]

        phone = android_phone.AndroidPhone(
            TestE2E.phone_emulator.id,
            test_settings.PodcastDirectoryOnPhone,
            test_settings.AndroidHistory,
        )

        self.assertCountEqual(
            expected_files_on_phone, phone.get_podcast_episodes_on_phone()
        )

        files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
        self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)

        # Delete the first half of the files from the phone.
        num_files_to_delete = len(episodes) // 2 + 1
        files_to_delete, files_to_keep = (
            episodes[:num_files_to_delete],
            episodes[num_files_to_delete:],
        )

        files_to_delete_full_path = [
            test_settings.PodcastDirectoryOnPhone.joinpath(x.name).as_posix()
            for x in files_to_delete
        ]
        TestE2E.phone_emulator.delete_files(files_to_delete_full_path)

        # Run a second time.
        user_input.side_effect = [
            # Continue with priority 1? Run 2.
            "N",
            # Copy Files. Run 2.
            "Y",
        ] + [
            # Confirmation to delete a file from the backup.
            "Y"
        ] * num_files_to_delete

        episodes = self._PopulatePodcastShow(
            podcast_show_folder,
            file_prefix="batch_2_",
        )

        prepare_for_phone.main(args, test_settings)

        # Since hours_to_add is bigger than all the files together, we should have added every file,
        # plus the undeleted files should still be there.
        expected_files_on_phone = [x.name for x in (episodes + files_to_keep)]
        self.maxDiff = None
        self.assertCountEqual(
            expected_files_on_phone, phone.get_podcast_episodes_on_phone()
        )

        files_in_backup_folder = set(os.listdir(test_settings.BackupFolder))
        self.assertCountEqual(expected_files_on_phone, files_in_backup_folder)


if __name__ == "__main__":
    unittest.main()
