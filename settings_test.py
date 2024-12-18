import datetime
import json
import pathlib
import tempfile
import unittest

import settings


class TestSettings(unittest.TestCase):
    def setUp(self) -> None:
        self._root_directory = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._root_directory.name)

        self.podcast_folder = self.root.joinpath("Podcasts")
        self.processed_file_boarding_zone_folder = self.root.joinpath("Add to Phone")
        self.archive_folder = self.root.joinpath("Archive")
        self.backup_folder = self.root.joinpath("Backup Folder")
        self.user_data_folder = self.root.joinpath("User Data Folder")

        self._default_settings = {
            "ANDROID_PHONE_ID": "ABCD",
            "PODCAST_DIRECTORY_ON_PHONE": "/storage/emulated/0/Podcasts",
            "PODCAST_FOLDER": str(self.podcast_folder),
            "PROCESSED_FILE_BOARDING_ZONE_FOLDER": str(
                self.processed_file_boarding_zone_folder
            ),
            "ARCHIVE_FOLDER": str(self.archive_folder),
            "BACKUP_FOLDER": str(self.backup_folder),
            "NUM_OLDEST_EPISODES_TO_ADD": 1,
            "TIME_OF_PODCASTS_TO_ADD_IN_HOURS": 10,
            "USER_DATA_FOLDER": str(self.user_data_folder),
        }

    def tearDown(self) -> None:
        self._root_directory.cleanup()

    def test_load_valid_setting_files(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete_on_close=False) as f:
            f.write(json.dumps(self._default_settings))
            f.close()

            user_settings = settings.DefaultSettings(pathlib.Path(f.name))
            self.assertEqual("ABCD", user_settings.android_phone_id)
            self.assertEqual(
                pathlib.Path("/storage/emulated/0/Podcasts"),
                user_settings.podcast_directory_on_phone,
            )
            self.assertEqual(self.podcast_folder, user_settings.podcast_folder)
            self.assertEqual(
                self.processed_file_boarding_zone_folder,
                user_settings.processed_file_boarding_zone_folder,
            )
            self.assertEqual(self.archive_folder, user_settings.archive_folder)
            self.assertEqual(self.backup_folder, user_settings.backup_folder)
            self.assertEqual(1, user_settings.num_oldest_episodes_to_add)
            self.assertEqual(
                datetime.timedelta(hours=10), user_settings.time_of_podcasts_to_add
            )

    def test_settings_file_missing_key(self) -> None:
        for key in self._default_settings.keys():
            with self.subTest(key=key):
                with tempfile.NamedTemporaryFile(mode="w", delete_on_close=False) as f:
                    incomplete_settings = self._default_settings.copy()
                    del incomplete_settings[key]
                    f.write(json.dumps(incomplete_settings))
                    f.close()

                    with self.assertRaisesRegex(
                        settings.SettingsError, "Required setting %s not found" % (key)
                    ):
                        settings.DefaultSettings(pathlib.Path(f.name))

    def test_settings_file_invalid_types_for_expected_integers(self) -> None:
        for key in settings.Settings._EXPECTED_INT:
            with tempfile.NamedTemporaryFile(mode="w", delete_on_close=False) as f:
                invalid_settings = self._default_settings.copy()
                invalid_settings[key] = "Not an Int"
                f.write(json.dumps(invalid_settings))
                f.close()

                with self.assertRaisesRegex(
                    settings.SettingsError,
                    "Required setting %s was expecting an integer" % (key),
                ):
                    settings.DefaultSettings(pathlib.Path(f.name))

    def test_settings_invalid_json(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete_on_close=False) as f:
            f.write("")
            f.close()

            with self.assertRaises(settings.SettingsError):
                settings.DefaultSettings(pathlib.Path(f.name))


if __name__ == "__main__":
    unittest.main()
