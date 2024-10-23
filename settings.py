import json
import os
import pathlib
import typing

import podcast_show

SETTINGS_FILE = pathlib.Path(
    os.path.dirname(__file__), "user_data", "user_settings.json"
)


class SettingsError(Exception):
    pass


class Settings(object):
    _EXPECTED_STRINGS = [
        "ANDROID_PHONE_ID",
        "PODCAST_FOLDER",
        "PROCESSED_FILE_BOARDING_ZONE_FOLDER",
        "ARCHIVE_FOLDER",
        "BACKUP_FOLDER",
        "PODCAST_DIRECTORY_ON_PHONE",
        "USER_DATA_FOLDER",
    ]
    _EXPECTED_INT = [
        "NUM_OLDEST_EPISODES_TO_ADD",
        "TIME_OF_PODCASTS_TO_ADD_IN_HOURS",
    ]

    def __init__(
        self,
        settings_file: pathlib.Path,
        podcasts: list[podcast_show.PodcastShow],
        specified_files: typing.Dict[pathlib.Path, typing.List[pathlib.Path]],
    ):
        with open(settings_file, "r", encoding="utf-8") as f:
            try:
                raw_json = json.load(f)
            except json.decoder.JSONDecodeError as e:
                raise SettingsError(
                    "Failed to parse settings file %s. Error:\n%s" % (settings_file, e)
                )

        for x in self._EXPECTED_STRINGS + self._EXPECTED_INT:
            if x not in raw_json:
                raise SettingsError(
                    "Required setting %s not found in %s. Please add it"
                    % (x, settings_file)
                )

        self._ANDROID_PHONE_ID = str(raw_json["ANDROID_PHONE_ID"])
        self._PODCAST_FOLDER = pathlib.Path(raw_json["PODCAST_FOLDER"])
        self._PROCESSED_FILE_BOARDING_ZONE_FOLDER = pathlib.Path(
            raw_json["PROCESSED_FILE_BOARDING_ZONE_FOLDER"]
        )
        self._ARCHIVE_FOLDER = pathlib.Path(raw_json["ARCHIVE_FOLDER"])
        self._BACKUP_FOLDER = pathlib.Path(raw_json["BACKUP_FOLDER"])
        self._USER_DATA_FOLDER = pathlib.Path(raw_json["USER_DATA_FOLDER"])

        # If any of the required folders are missing, create them.
        self._ARCHIVE_FOLDER.mkdir(exist_ok=True)
        self._BACKUP_FOLDER.mkdir(exist_ok=True)
        self._USER_DATA_FOLDER.mkdir(exist_ok=True)

        self._PODCAST_DIRECTORY_ON_PHONE = pathlib.Path(
            raw_json["PODCAST_DIRECTORY_ON_PHONE"]
        )

        for key in self._EXPECTED_INT:
            try:
                int(raw_json[key])
            except ValueError:
                raise SettingsError(
                    'Required setting %s was expecting an integer, got "%s" in %s instead.'
                    % (key, raw_json[key], settings_file)
                )

        self._NUM_OLDEST_EPISODES_TO_ADD = int(raw_json["NUM_OLDEST_EPISODES_TO_ADD"])
        self._TIME_OF_PODCASTS_TO_ADD_IN_HOURS = int(
            raw_json["TIME_OF_PODCASTS_TO_ADD_IN_HOURS"]
        )

        self._PODCASTS = podcasts
        self._SPECIFIED_FILES = specified_files

    @property
    def android_phone_id(self) -> str:
        return self._ANDROID_PHONE_ID

    @property
    def podcast_folder(self) -> pathlib.Path:
        return self._PODCAST_FOLDER

    @property
    def processed__file__boarding_zone_folder(self) -> pathlib.Path:
        return self._PROCESSED_FILE_BOARDING_ZONE_FOLDER

    @property
    def archive_folder(self) -> pathlib.Path:
        return self._ARCHIVE_FOLDER

    @property
    def backup_folder(self) -> pathlib.Path:
        return self._BACKUP_FOLDER

    @property
    def podcast_directory_on_phone(self) -> pathlib.Path:
        return self._PODCAST_DIRECTORY_ON_PHONE

    @property
    def num_oldest_episodes_to_add(self) -> int:
        return self._NUM_OLDEST_EPISODES_TO_ADD

    @property
    def time_of_podcasts_to_add_in_hours(self) -> int:
        return self._TIME_OF_PODCASTS_TO_ADD_IN_HOURS

    @property
    def podcasts(self) -> typing.List[podcast_show.PodcastShow]:
        return self._PODCASTS

    @property
    def specified_files(self) -> typing.Dict[pathlib.Path, typing.List[pathlib.Path]]:
        return self._SPECIFIED_FILES

    @property
    def android_history(self) -> pathlib.Path:
        return pathlib.Path(self._USER_DATA_FOLDER, "android_history.txt")

    @property
    def backup_history(self) -> pathlib.Path:
        return pathlib.Path(self._USER_DATA_FOLDER, "android_history.txt")

    @property
    def podcast_database(self) -> pathlib.Path:
        return pathlib.Path(self._USER_DATA_FOLDER, "podcast.db")

    @property
    def podcast_history(self) -> pathlib.Path:
        return pathlib.Path(self._USER_DATA_FOLDER, "history.txt")

    @property
    def podcast_stats(self) -> pathlib.Path:
        return pathlib.Path(self._USER_DATA_FOLDER, "stats.txt")


# TODO: Maybe get a better name.
class DefaultSettings(Settings):
    def __init__(self, settings_file: pathlib.Path = SETTINGS_FILE):
        # TODO: Make podcast_shows and specific files cleaner settings,
        # instead of just importing python files.
        user_podcast_shows: list[podcast_show.PodcastShow] = []
        try:
            from user_data.subscribed_shows import PODCASTS  # noqa

            user_podcast_shows = PODCASTS
        except ModuleNotFoundError:
            print("No user podcast show file found.")

        user_specified_files: typing.Dict[pathlib.Path, typing.List[pathlib.Path]] = {}
        try:
            from user_data.specified_files import SPECIFIED_FILES  # noqa

            user_specified_files = SPECIFIED_FILES
        except ModuleNotFoundError:
            print("No user specified file found.")

        super().__init__(
            settings_file,
            user_podcast_shows,
            user_specified_files,
        )
