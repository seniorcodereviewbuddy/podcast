import datetime
import os
import pathlib
import shutil
import tempfile
import typing
import unittest

import full_podcast_episode
import podcast_database
import podcast_episode
import podcast_show
import test_utils


def FileContents(file: pathlib.Path) -> str:
    with open(file, "r", encoding="utf-8") as f:
        return f.read()


class TestPodcastDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self._root_directory = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._root_directory.name)

    def tearDown(self) -> None:
        self._root_directory.cleanup()

    def _CreatePodcastShow(
        self,
        podcast_dir: pathlib.Path,
        priority: int,
        episodes: list[str],
        episodes_start_time: int,
    ) -> podcast_show.PodcastShow:
        podcast_folder = pathlib.Path(self.root, podcast_dir)
        os.mkdir(podcast_folder)

        test_file = os.path.join(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        for i, episode in enumerate(episodes):
            episode_path = pathlib.Path(podcast_folder, episode)

            shutil.copyfile(
                test_file,
                podcast_folder.joinpath(episode_path),
            )

            new_time = episodes_start_time + 100 * i
            os.utime(episode_path, (new_time, new_time))

        return podcast_show.PodcastShow(podcast_folder, priority)

    def testSaveAndLoad_Empty(self) -> None:
        database = podcast_database.PodcastDatabase(self.root, [], False)

        database_folder = tempfile.mkdtemp()
        database_file = pathlib.Path(database_folder, "database.txt")
        database.Save(database_file)
        self.assertEqual("0\n", FileContents(database_file))

        database.Load(database_file)

    def testSaveAndLoad_Basic(self) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_folder = pathlib.Path(self.root, known_folder)
        os.mkdir(podcast_folder)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        # Ensure all podcast_shows have their next_index set.
        for p in database.podcast_shows:
            p.next_index = 1

        database.UpdatePodcasts()

        database_folder = tempfile.mkdtemp()
        database_file = pathlib.Path(database_folder, "database.txt")
        database.Save(database_file)

        self.assertEqual(
            "1\nknown_folder\nknown_folder\n1\n0\n", FileContents(database_file)
        )

        self.assertEqual(1, database.Load(database_file))

        # Now try with files.
        # TODO: Move this creation into a helper function, it happens a lot here.
        episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_élè.mp3"]
        now = 666
        for index, episode in enumerate(episodes):
            full_path = pathlib.Path(podcast_folder, episode)
            shutil.copyfile(
                pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
                full_path,
            )
            os.utime(full_path, (now + 100 * index, now + 100 * index))

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts()

        database.Save(database_file)
        contents = FileContents(database_file)
        want = "1\nknown_folder\nknown_folder\n4\n3\n"
        for index, episode in enumerate(episodes):
            full_path = pathlib.Path(podcast_folder, episode)
            want += "%s\n%d\n%d\n%d\n" % (
                full_path,
                index + 1,
                test_utils.TEST_FILE_LENGTH_IN_SECONDS,
                now + 100 * index,
            )
        self.assertEqual(contents, want)

        self.assertEqual(1, database.Load(database_file))

        # Delete the folder and ensure we save nothing.
        shutil.rmtree(podcast_folder)
        database.UpdatePodcasts()

        database.Save(database_file)
        self.assertEqual("0\n", FileContents(database_file))

    def testSaveAndLoad_PodcastRemoved(self) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_folder = pathlib.Path(self.root, known_folder)
        os.mkdir(podcast_folder)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        # Ensure all podcast_shows have their next_index set.
        for p in database.podcast_shows:
            p.next_index = 1

        database.UpdatePodcasts()

        database_folder = tempfile.mkdtemp()
        database_file = pathlib.Path(database_folder, "database.txt")
        database.Save(database_file)

        self.assertEqual(
            "1\nknown_folder\nknown_folder\n1\n0\n", FileContents(database_file)
        )

        self.assertEqual(1, database.Load(database_file))

        # Now try to load the podcast database without this podcast and don't remove it.
        database = podcast_database.PodcastDatabase(self.root, [], False)
        with self.assertRaises(podcast_database.DatabaseLoadingException):
            database.Load(database_file, lambda x: "don't remove")

        database = podcast_database.PodcastDatabase(self.root, [], False)
        podcasts_loaded = database.Load(database_file, lambda x: "REMOVE")
        self.assertEqual(0, podcasts_loaded)

        # Ensure we now save an empty database.
        database.Save(database_file)
        self.assertEqual("0\n", FileContents(database_file))

    def testGetPodcastEpisodesByPriority(self) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_folder = pathlib.Path(self.root, known_folder)
        os.mkdir(podcast_folder)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        episodes_names = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        expected_selected_episodes = []
        now = 666
        for index, episode_name in enumerate(episodes_names):
            full_path = pathlib.Path(podcast_folder, episode_name)
            utime = now + 100 * index

            expected_selected_episodes.append(
                full_podcast_episode.FullPodcastEpisode(
                    index=index + 1,
                    path=full_path,
                    podcast_show_name=podcast_shows[0].podcast_name,
                    speed=podcast_shows[0].speed,
                    archive=podcast_shows[0].archive,
                    modification_time=datetime.datetime.fromtimestamp(utime),
                    duration=datetime.timedelta(
                        seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS
                    ),
                )
            )

            shutil.copyfile(
                pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
                full_path,
            )
            os.utime(full_path, (utime, utime))

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS - 1),
            user_prompt=lambda x: True,
        )
        self.assertEqual(expected_selected_episodes[0:1], results)

        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS * 2 - 1),
            user_prompt=lambda x: True,
        )
        self.assertEqual(
            expected_selected_episodes[0:2],
            results,
        )

        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(hours=10), user_prompt=lambda x: True
        )
        self.assertEqual(
            expected_selected_episodes,
            results,
        )

    def testGetPodcastEpisodesByPriority_TestIgnore(self) -> None:
        known_folder = pathlib.Path("known_folder")
        episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        show = self._CreatePodcastShow(known_folder, podcast_show.P1, episodes, 666)
        podcast_shows = [show]

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(hours=10), user_prompt=lambda x: True
        )

        self.assertEqual(3, len(results))
        self.assertEqual("podcast_1.mp3", os.path.basename(results[0].path))
        self.assertEqual("podcast_2.mp3", os.path.basename(results[1].path))
        self.assertEqual("podcast_3.mp3", os.path.basename(results[2].path))

        first_episode = podcast_shows[0].FirstEpisode()
        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(hours=10),
            user_prompt=lambda x: True,
            files_to_ignore=[
                (typing.cast(podcast_episode.PodcastEpisode, first_episode)).path
            ],
        )
        self.assertEqual(2, len(results))
        self.assertEqual("podcast_2.mp3", os.path.basename(results[0].path))
        self.assertEqual("podcast_3.mp3", os.path.basename(results[1].path))

        all_episodes = podcast_shows[0].RemainingEpisodes()
        results = database.GetPodcastEpisodesByPriority(
            datetime.timedelta(hours=10),
            user_prompt=lambda x: True,
            files_to_ignore=[x.path for x in all_episodes],
        )
        self.assertFalse(results)

    def testGetOldestFiles(self) -> None:
        known_folder = pathlib.Path("known_folder")
        podcast_folder = pathlib.Path(self.root, known_folder)
        os.mkdir(podcast_folder)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]

        episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        now = 666
        for index, episode in enumerate(episodes):
            full_path = pathlib.Path(podcast_folder, episode)
            shutil.copyfile(
                pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
                full_path,
            )
            os.utime(full_path, (now + 100 * index, now + 100 * index))

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        results = database.GetOldestFiles(1)
        self.assertEqual(1, len(results))
        self.assertEqual("podcast_1.mp3", os.path.basename(results[0].path))

        results = database.GetOldestFiles(2)
        self.assertEqual(2, len(results))
        self.assertEqual("podcast_1.mp3", os.path.basename(results[0].path))
        self.assertEqual(
            "podcast_2.mp3",
            os.path.basename(results[1].path),
            [str(x) for x in results],
        )

        results = database.GetOldestFiles(3)
        self.assertEqual(3, len(results))
        self.assertEqual("podcast_1.mp3", os.path.basename(results[0].path))
        self.assertEqual("podcast_2.mp3", os.path.basename(results[1].path))
        self.assertEqual("podcast_3.mp3", os.path.basename(results[2].path))

        results = database.GetOldestFiles(4)
        self.assertEqual(3, len(results), results)
        self.assertEqual("podcast_1.mp3", os.path.basename(results[0].path))
        self.assertEqual("podcast_2.mp3", os.path.basename(results[1].path))
        self.assertEqual("podcast_3.mp3", os.path.basename(results[2].path))

        first_episode = podcast_shows[0].FirstEpisode()
        self.assertTrue(first_episode)
        results = database.GetOldestFiles(
            2,
            files_to_ignore=[
                typing.cast(podcast_episode.PodcastEpisode, first_episode).path
            ],
        )
        self.assertEqual(2, len(results))
        self.assertEqual("podcast_2.mp3", os.path.basename(results[0].path))
        self.assertEqual("podcast_3.mp3", os.path.basename(results[1].path))

    def testGetOldestFilesFromMultiple(self) -> None:
        known_folder = pathlib.Path("known_folder")
        known_folder_2 = pathlib.Path("known_folder_2")
        podcast_folder = pathlib.Path(self.root, known_folder)
        podcast_folder_2 = pathlib.Path(self.root, known_folder_2)
        os.mkdir(podcast_folder)
        os.mkdir(podcast_folder_2)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P2),
            podcast_show.PodcastShow(known_folder_2, podcast_show.P1),
        ]
        episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        now = 666
        for podcast_index, p in enumerate(podcast_shows):
            podcast_time = podcast_index * 1000 + now
            for episode_index, episode in enumerate(episodes):
                full_path = pathlib.Path(self.root, p.podcast_folder, episode)
                shutil.copyfile(
                    pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
                    full_path,
                )
                os.utime(
                    full_path,
                    (
                        podcast_time + 100 * episode_index,
                        podcast_time + 100 * episode_index,
                    ),
                )

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        expected_episodes_by_age = [
            pathlib.Path(self.root, known_folder, episodes[0]),
            pathlib.Path(self.root, known_folder, episodes[1]),
            pathlib.Path(self.root, known_folder, episodes[2]),
            pathlib.Path(self.root, known_folder_2, episodes[0]),
            pathlib.Path(self.root, known_folder_2, episodes[1]),
            pathlib.Path(self.root, known_folder_2, episodes[2]),
        ]

        for i in range(1, len(expected_episodes_by_age) + 1):
            results = database.GetOldestFiles(i)
            self.assertEqual(i, len(results))
            for q in range(i):
                self.assertEqual(expected_episodes_by_age[q], results[q].path)

    def testRepeatedPath(self) -> None:
        known_folder = pathlib.Path("repeated_folder")
        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
        ]
        with self.assertRaises(Exception):
            podcast_database.PodcastDatabase(pathlib.Path("root"), podcast_shows, False)

    def testStats(self) -> None:
        known_folder = pathlib.Path("known_folder")
        known_folder_2 = pathlib.Path("known_folder_2")
        podcast_folder = pathlib.Path(self.root, known_folder)
        podcast_folder_2 = pathlib.Path(self.root, known_folder_2)
        os.mkdir(podcast_folder)
        os.mkdir(podcast_folder_2)

        podcast_shows = [
            podcast_show.PodcastShow(known_folder, podcast_show.P1),
            podcast_show.PodcastShow(known_folder_2, podcast_show.P2),
        ]
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder, "podcast_1.mp3"),
        )
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder, "podcast_2.mp3"),
        )
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder, "podcast_3.mp3"),
        )
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder_2, "podcast_1.mp3"),
        )
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder_2, "podcast_2.mp3"),
        )
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            pathlib.Path(podcast_folder_2, "podcast_3.mp3"),
        )

        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        history = pathlib.Path(self.root, "history")
        database.UpdateRemainingTime(history, date=datetime.datetime(2020, 1, 1))
        want = f"As of 2020-01-01 00:00:00, the podcast episode backlog is 6 episodes with total duration {test_utils.TEST_FILE_LENGTH_IN_SECONDS*6}s\n"
        self.assertEqual(want, FileContents(history))

        stats = pathlib.Path(self.root, "stats")
        database.LogStats(stats)
        want = (
            f"known_folder: total duration of {test_utils.TEST_FILE_LENGTH_IN_SECONDS*3}s, 3 episodes, {test_utils.TEST_FILE_LENGTH_IN_SECONDS}s long on average\n"
            f"known_folder_2: total duration of {test_utils.TEST_FILE_LENGTH_IN_SECONDS*3}s, 3 episodes, {test_utils.TEST_FILE_LENGTH_IN_SECONDS}s long on average\n"
        )
        self.assertEqual(want, FileContents(stats))

    def testGetSpecifiedFiles(self) -> None:
        show_1_path = pathlib.Path(self.root, "show_1")
        show_1_episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        show_1 = self._CreatePodcastShow(
            show_1_path, podcast_show.P1, show_1_episodes, 666
        )

        show_2_path = pathlib.Path(self.root, "show_2")
        show_2_episodes = [
            "show_2_podcast_1.mp3",
            "show_2_podcast_2.mp3",
            "show_2_podcast_3.mp3",
        ]
        show_2 = self._CreatePodcastShow(
            show_2_path, podcast_show.P1, show_2_episodes, 666
        )

        podcast_shows = [show_1, show_2]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        files_to_get = {
            show_1_path: [pathlib.Path(show_1_path, show_1_episodes[1])],
            show_2_path: [pathlib.Path(show_2_path, show_2_episodes[2])],
        }

        files = database.GetSpecifiedFiles(files_to_get)
        expected_files = [
            show_1.GetEpisode(pathlib.Path(show_1_path, show_1_episodes[1])),
            show_2.GetEpisode(pathlib.Path(show_2_path, show_2_episodes[2])),
        ]
        self.assertCountEqual(expected_files, files)

    def testGetSpecifiedFilesInIgnoreList(self) -> None:
        show_1_path = pathlib.Path(self.root, "show_1")
        show_1_episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        show_1 = self._CreatePodcastShow(
            show_1_path, podcast_show.P1, show_1_episodes, 666
        )

        show_2_path = pathlib.Path(self.root, "show_2")
        show_2_episodes = [
            "show_2_podcast_1.mp3",
            "show_2_podcast_2.mp3",
            "show_2_podcast_3.mp3",
        ]
        show_2 = self._CreatePodcastShow(
            show_2_path, podcast_show.P1, show_2_episodes, 666
        )

        podcast_shows = [show_1, show_2]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        files_to_get = {
            show_1_path: [pathlib.Path(show_1_path, show_1_episodes[1])],
            show_2_path: [pathlib.Path(show_2_path, show_2_episodes[2])],
        }

        files = database.GetSpecifiedFiles(
            files_to_get,
            files_to_ignore=[pathlib.Path(show_1_path, show_1_episodes[1])],
        )
        expected_files = [
            show_2.GetEpisode(pathlib.Path(show_2_path, show_2_episodes[2])),
        ]
        self.assertCountEqual(expected_files, files)

    def testGetSpecifiedFilesMissingShow(self) -> None:
        show_1_path = pathlib.Path(self.root, "show_1")
        show_1_episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        show_1 = self._CreatePodcastShow(
            show_1_path, podcast_show.P1, show_1_episodes, 666
        )

        podcast_shows = [show_1]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        files_to_get = {
            pathlib.Path("Fake_show"): [pathlib.Path(show_1_path, show_1_episodes[0])]
        }

        with self.assertRaises(podcast_database.InvalidPodcastShowPath):
            database.GetSpecifiedFiles(files_to_get)

    def testGetSpecifiedFilesMissingEpisodes(self) -> None:
        show_1_path = pathlib.Path(self.root, "show_1")
        show_1_episodes = ["podcast_1.mp3", "podcast_2.mp3", "podcast_3.mp3"]
        show_1 = self._CreatePodcastShow(
            show_1_path, podcast_show.P1, show_1_episodes, 666
        )

        podcast_shows = [show_1]
        database = podcast_database.PodcastDatabase(self.root, podcast_shows, False)
        database.UpdatePodcasts(allow_prompt=False)

        files_to_get = {show_1_path: [pathlib.Path("fake_path")]}

        with self.assertRaises(podcast_database.InvalidPodcastEpisodePath):
            database.GetSpecifiedFiles(files_to_get)


if __name__ == "__main__":
    unittest.main()
