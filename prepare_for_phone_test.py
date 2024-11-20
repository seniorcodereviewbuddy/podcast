import datetime
import os
import pathlib
import shutil
import tempfile
import typing
import unittest

import archive
import full_podcast_episode
import podcast_database
import podcast_show
import prepare_for_phone
import test_utils


def _list_of_full_podcast_episodes_to_list_of_names(
    paths: list[full_podcast_episode.FullPodcastEpisode],
) -> list[str]:
    return [x.path.name for x in paths]


def _get_x_oldest_episodes(
    show: podcast_show.PodcastShow, x: int
) -> list[full_podcast_episode.FullPodcastEpisode]:
    episodes = show.remaining_episodes()

    # Make sure they are in sorted order by age.
    sorted(episodes, key=lambda x: x.modification_time)

    return episodes[0:x]


class TestPrepareForPhone(unittest.TestCase):
    def setUp(self) -> None:
        self._root_directory = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._root_directory.name)

    def tearDown(self) -> None:
        self._root_directory.cleanup()

    def _create_podcast_show(
        self,
        podcast_dir: pathlib.Path,
        priority: int,
        num_episodes: int,
        episodes_start_time: typing.Optional[int] = None,
    ) -> podcast_show.PodcastShow:
        podcast_folder = pathlib.Path(self.root, podcast_dir)
        os.mkdir(podcast_folder)

        test_file = os.path.join(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        for x in range(num_episodes):
            episode_path = pathlib.Path(podcast_folder, "podcast_%d.mp3" % (x + 1))

            shutil.copyfile(
                test_file,
                podcast_folder.joinpath(episode_path),
            )

            if episodes_start_time:
                new_time = episodes_start_time + 100 * x
                os.utime(episode_path, (new_time, new_time))

        show = podcast_show.PodcastShow(podcast_folder, priority)
        show.scan_for_updates(self.root, allow_prompt=False)

        return show

    def test_find_unknown_folders_only_unknown(self) -> None:
        unknown_folder = pathlib.Path("unknown_folder")
        os.mkdir(pathlib.Path(self.root, unknown_folder))

        self.assertEqual(
            prepare_for_phone.find_unknown_folders(self.root, expected_folders=[]),
            [unknown_folder],
        )

    def test_find_unknown_folders_only_known(self) -> None:
        known_folder = pathlib.Path("known_folder")
        os.mkdir(pathlib.Path(self.root, known_folder))

        self.assertEqual(
            prepare_for_phone.find_unknown_folders(
                self.root, expected_folders=[known_folder.name]
            ),
            [],
        )

    def test_find_unknown_folders_known_and_unknown(self) -> None:
        known_folder = pathlib.Path("known_folder")
        os.mkdir(pathlib.Path(self.root, known_folder))

        unknown_folder = pathlib.Path("unknown_folder")
        os.mkdir(pathlib.Path(self.root, unknown_folder))

        self.assertEqual(
            prepare_for_phone.find_unknown_folders(
                self.root, expected_folders=[known_folder.name]
            ),
            [unknown_folder],
        )

    def test_validate_podcast_folders_known_folder_present(self) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        # Verify this doesn't raise an exception when called with only
        # known folders.
        prepare_for_phone.validate_podcast_folders(
            self.root, podcast_shows=podcast_shows
        )

    def test_validate_podcast_folders_unknown_folder_present(self) -> None:
        unknown_folder = pathlib.Path("unknown_folder")
        os.mkdir(pathlib.Path(self.root, unknown_folder))

        with self.assertRaises(prepare_for_phone.UnknownPodcastFoldersError):
            prepare_for_phone.validate_podcast_folders(self.root, podcast_shows=[])

    def test_validate_podcast_folders_known_and_unknowns_folders_present(
        self,
    ) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        unknown_folder = pathlib.Path("unknown_folder")
        os.mkdir(pathlib.Path(self.root, unknown_folder))

        with self.assertRaises(prepare_for_phone.UnknownPodcastFoldersError):
            prepare_for_phone.validate_podcast_folders(
                self.root, podcast_shows=podcast_shows
            )

    def test_process_and_move_files_over(self) -> None:
        podcast_folder = pathlib.Path("podcast_show")
        podcast_test_show = self._create_podcast_show(
            podcast_folder, podcast_show.P1, 3
        )
        podcast_test_show.archive = archive.Archive.YES

        database = podcast_database.PodcastDatabase(
            self.root, [podcast_test_show], False
        )
        database.update_podcasts(allow_prompt=False)

        unprocessed_files = podcast_test_show.remaining_episodes()

        # Moved folder should be empty for dry run.
        copied_folder = pathlib.Path(tempfile.mkdtemp())
        archive_folder = pathlib.Path(tempfile.mkdtemp())

        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, True
        )

        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(podcast_test_show.podcast_folder),
        )
        self.assertEqual([], os.listdir(copied_folder))
        self.assertEqual([], os.listdir(archive_folder))

        # Moved folder should have all the files.
        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, False
        )
        self.assertEqual([], os.listdir(podcast_test_show.podcast_folder))
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(copied_folder),
        )

        self.assertEqual([podcast_folder.name], os.listdir(archive_folder))
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(os.path.join(archive_folder, podcast_folder)),
        )

    def test_move_files_overs_no_archive(self) -> None:
        podcast_folder = pathlib.Path(self.root, "new show")
        podcast_test_show = self._create_podcast_show(
            podcast_folder, podcast_show.P1, 3
        )
        podcast_test_show.archive = archive.Archive.NO

        database = podcast_database.PodcastDatabase(
            self.root, [podcast_test_show], False
        )
        database.update_podcasts(allow_prompt=False)

        unprocessed_files = podcast_test_show.remaining_episodes()

        # Moved folder should be empty for dry run.
        copied_folder = pathlib.Path(tempfile.mkdtemp())
        archive_folder = pathlib.Path(tempfile.mkdtemp())
        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, True
        )
        self.assertEqual(
            ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"],
            os.listdir(podcast_folder),
        )
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(podcast_test_show.podcast_folder),
        )
        self.assertEqual([], os.listdir(copied_folder))
        self.assertEqual([], os.listdir(archive_folder))

        # Moved folder should have all the files.
        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, False
        )
        self.assertEqual([], os.listdir(podcast_test_show.podcast_folder))
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(copied_folder),
        )
        self.assertEqual([], os.listdir(archive_folder))

    def test_move_files_overs_copy_and_archive_different_encodings(self) -> None:
        podcast_folder = pathlib.Path(self.root, "podcast_show")
        os.mkdir(podcast_folder)

        test_files = [
            test_utils.MP3_TEST_FILE,
            test_utils.MP3_NO_TITLE_NO_ALBUM,
            test_utils.MP3_DIFFERENT_TITLE_ENCODING,
            test_utils.MP3_WITH_EMOJI,
            test_utils.MP3_WITH_MULTIPLE_UTF8,
            test_utils.M4A_TEST_FILE,
            test_utils.M4A_NO_TITLE_NO_ALBUM,
            test_utils.M4A_DIFFERENT_TITLE_ENCODING,
        ]
        for test_file in test_files:
            source = pathlib.Path(test_utils.TEST_DATA_DIR, test_file)
            episode_path = pathlib.Path(podcast_folder, test_file)
            shutil.copyfile(
                source,
                episode_path,
            )

        podcast_test_show = podcast_show.PodcastShow(
            podcast_folder, podcast_show.P0, archive=archive.Archive.YES
        )
        podcast_test_show.scan_for_updates(self.root, allow_prompt=False)

        database = podcast_database.PodcastDatabase(
            self.root, [podcast_test_show], False
        )
        database.update_podcasts(allow_prompt=False)

        unprocessed_files = podcast_test_show.remaining_episodes()

        # Moved folder should be empty for dry run.
        copied_folder = pathlib.Path(tempfile.mkdtemp())
        archive_folder = pathlib.Path(tempfile.mkdtemp())

        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, True
        )

        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(podcast_test_show.podcast_folder),
        )
        self.assertEqual([], os.listdir(copied_folder))
        self.assertEqual([], os.listdir(archive_folder))

        # Moved folder should have all the files.
        prepare_for_phone.process_and_move_files_over(
            unprocessed_files, copied_folder, archive_folder, False
        )
        self.assertEqual([], os.listdir(podcast_test_show.podcast_folder))
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(copied_folder),
        )

        self.assertEqual([podcast_folder.name], os.listdir(archive_folder))
        self.assertCountEqual(
            _list_of_full_podcast_episodes_to_list_of_names(unprocessed_files),
            os.listdir(archive_folder.joinpath(podcast_folder.name)),
        )

    def test_get_batch_of_podcast_files_only_priority(self) -> None:
        priority_path = pathlib.Path("priority_podcast")
        priority_show = self._create_podcast_show(
            priority_path, podcast_show.P0, 3, episodes_start_time=6666
        )

        old_podcast_path = pathlib.Path("old_podcast")
        old_podcast_show = self._create_podcast_show(
            old_podcast_path, podcast_show.P2, 3, episodes_start_time=3000
        )

        podcast_shows = [priority_show, old_podcast_show]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS - 1),
            num_oldest_files_to_get=0,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(priority_show, 1)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 2 - 1),
            num_oldest_files_to_get=0,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(priority_show, 2)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 3 - 1),
            num_oldest_files_to_get=0,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(priority_show, 3)
        self.assertCountEqual(files, expected_result)

    def test_get_batch_of_podcast_files_only_oldest(self) -> None:
        old_path = pathlib.Path("priority_podcast")
        old_show = self._create_podcast_show(
            old_path, podcast_show.P2, 3, episodes_start_time=3000
        )

        new_priority_path = pathlib.Path("new_podcast")
        new_priority_show = self._create_podcast_show(
            new_priority_path, podcast_show.P0, 3, episodes_start_time=6666
        )

        podcast_shows = [
            old_show,
            new_priority_show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS - 1),
            num_oldest_files_to_get=1,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_show, 1)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 2 - 1),
            num_oldest_files_to_get=2,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_show, 2)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 3 - 1),
            num_oldest_files_to_get=3,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_show, 3)
        self.assertCountEqual(files, expected_result)

    def test_get_batch_of_podcast_files_oldest_and_priority(self) -> None:
        old_path = pathlib.Path("priority_podcast")
        old_show = self._create_podcast_show(
            old_path, podcast_show.P2, 3, episodes_start_time=3000
        )

        new_priority_path = pathlib.Path("new_podcast")
        new_priority_show = self._create_podcast_show(
            new_priority_path, podcast_show.P0, 3, episodes_start_time=6666
        )

        podcast_shows = [
            old_show,
            new_priority_show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 2 - 1),
            num_oldest_files_to_get=1,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_show, 1) + _get_x_oldest_episodes(
            new_priority_show, 1
        )
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 4 - 1),
            num_oldest_files_to_get=2,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_show, 2) + _get_x_oldest_episodes(
            new_priority_show, 2
        )
        self.assertCountEqual(files, expected_result)

    def test_get_batch_of_podcast_files_oldest_was_priority(self) -> None:
        old_priority_path = pathlib.Path("priority_podcast")
        old_priority_show = self._create_podcast_show(
            old_priority_path, podcast_show.P0, 3, episodes_start_time=3000
        )

        new_low_priority_path = pathlib.Path("new_podcast")
        new_low_priority_show = self._create_podcast_show(
            new_low_priority_path, podcast_show.P2, 3, episodes_start_time=6666
        )

        podcast_shows = [
            old_priority_show,
            new_low_priority_show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS - 1),
            num_oldest_files_to_get=1,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_priority_show, 1)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 3 - 1),
            num_oldest_files_to_get=1,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(old_priority_show, 3)
        self.assertCountEqual(files, expected_result)

        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 4 - 1),
            num_oldest_files_to_get=1,
            user_prompt=lambda x: True,
        )
        expected_result = _get_x_oldest_episodes(
            old_priority_show, 3
        ) + _get_x_oldest_episodes(new_low_priority_show, 1)
        self.assertCountEqual(files, expected_result)

    def test_get_batch_of_podcast_files_all_oldest_were_specified(self) -> None:
        show_path = pathlib.Path(self.root, "podcast_show")
        show = self._create_podcast_show(
            show_path, podcast_show.P2, 3, episodes_start_time=3000
        )
        podcast_shows = [
            show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        oldest_episode = _get_x_oldest_episodes(show, 1)
        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=0),
            num_oldest_files_to_get=1,
            required_files={
                pathlib.Path(show_path.name): [
                    pathlib.Path(oldest_episode[0].path.name)
                ]
            },
            user_prompt=lambda x: True,
        )
        self.assertCountEqual(files, oldest_episode)

    def test_get_batch_of_podcast_files_specified_over_duration(self) -> None:
        show_path = pathlib.Path(self.root, "podcast_show")
        show = self._create_podcast_show(
            show_path, podcast_show.P2, 3, episodes_start_time=3000
        )
        podcast_shows = [
            show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        oldest_episode = _get_x_oldest_episodes(show, 1)
        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=0),
            num_oldest_files_to_get=0,
            required_files={
                pathlib.Path(show_path.name): [
                    pathlib.Path(oldest_episode[0].path.name)
                ]
            },
            user_prompt=lambda x: True,
        )
        self.assertCountEqual(files, oldest_episode)

    def test_get_batch_of_podcast_files_oldest_and_specified_over_duration(
        self,
    ) -> None:
        show_path = pathlib.Path(self.root, "podcast_show")
        show = self._create_podcast_show(
            show_path, podcast_show.P2, 3, episodes_start_time=3000
        )
        podcast_shows = [
            show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        oldest_episodes = _get_x_oldest_episodes(show, 2)
        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=0),
            num_oldest_files_to_get=1,
            required_files={
                pathlib.Path(show_path.name): [
                    pathlib.Path(oldest_episodes[1].path.name)
                ]
            },
            user_prompt=lambda x: True,
        )
        self.assertCountEqual(files, oldest_episodes)

    def test_get_batch_of_podcast_files_oldest_and_specified_under_duration(
        self,
    ) -> None:
        show_path = pathlib.Path(self.root, "podcast_show")
        show = self._create_podcast_show(
            show_path, podcast_show.P2, 4, episodes_start_time=3000
        )
        podcast_shows = [
            show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        oldest_episodes = _get_x_oldest_episodes(show, 3)
        files = prepare_for_phone.get_batch_of_podcast_files(
            database,
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 3 - 1),
            num_oldest_files_to_get=1,
            required_files={
                pathlib.Path(show_path.name): [
                    pathlib.Path(oldest_episodes[1].path.name)
                ]
            },
            user_prompt=lambda x: True,
        )
        self.assertCountEqual(files, oldest_episodes)

    def test_get_batch_of_podcast_files_specified_file_missing(self) -> None:
        show_path = pathlib.Path(self.root, "podcast_show")
        show = self._create_podcast_show(
            show_path, podcast_show.P2, 4, episodes_start_time=3000
        )
        podcast_shows = [
            show,
        ]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.update_podcasts(allow_prompt=False)

        with self.assertRaises(podcast_database.PodcastEpisodePathError):
            prepare_for_phone.get_batch_of_podcast_files(
                database,
                datetime.timedelta(
                    seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 4 - 1
                ),
                num_oldest_files_to_get=1,
                required_files={
                    pathlib.Path(show_path.name): [pathlib.Path("fake_path")]
                },
                user_prompt=lambda x: True,
            )


if __name__ == "__main__":
    unittest.main()
