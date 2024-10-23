import json
import pathlib
import tempfile
import unittest

import settings


class TestSettings(unittest.TestCase):
    def setUp(self) -> None:
        self._default_settings = {
            "ANDROID_PHONE_ID": "ABCD",
            "PODCAST_DIRECTORY_ON_PHONE": "/storage/emulated/0/Podcasts",
            "PODCAST_FOLDER": "D:\\Podcasts",
            "PROCESSED_FILE_BOARDING_ZONE_FOLDER": "D:\\Podcasts\\Add to Phone",
            "ARCHIVE_FOLDER": "D:\\Podcasts\\Archive",
            "BACKUP_FOLDER": "D:\\Podcasts\\On Phone",
            "NUM_OLDEST_EPISODES_TO_ADD": 1,
            "TIME_OF_PODCASTS_TO_ADD_IN_HOURS": 10,
            "USER_DATA_FOLDER": "E:\\podcast",
        }

    def test_load_valid_setting_files(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete_on_close=False) as f:
            f.write(json.dumps(self._default_settings))
            f.close()

            user_settings = settings.DefaultSettings(pathlib.Path(f.name))
            self.assertEqual("ABCD", user_settings.AndroidPhoneID)
            self.assertEqual(
                pathlib.Path("/storage/emulated/0/Podcasts"),
                user_settings.PodcastDirectoryOnPhone,
            )
            self.assertEqual(pathlib.Path("D:\\Podcasts"), user_settings.PodcastFolder)
            self.assertEqual(
                pathlib.Path("D:\\Podcasts\\Add to Phone"),
                user_settings.ProcessedFileBoardingZoneFolder,
            )
            self.assertEqual(
                pathlib.Path("D:\\Podcasts\\Archive"), user_settings.ArchiveFolder
            )
            self.assertEqual(
                pathlib.Path("D:\\Podcasts\\On Phone"), user_settings.BackupFolder
            )
            self.assertEqual(1, user_settings.NumOldestEpisodesToAdd)
            self.assertEqual(10, user_settings.TimeOfPodcastsToAddInHours)

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
