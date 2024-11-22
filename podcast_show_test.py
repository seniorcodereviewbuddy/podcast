import datetime
import io
import os
import pathlib
import shutil
import tempfile
import typing
import unittest

import archive
import full_podcast_episode
import podcast_episode
import podcast_preprocessing_base
import podcast_show
import test_utils


class TestPodcast(unittest.TestCase):
    def setUp(self) -> None:
        self._root_directory = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._root_directory.name)

    def tearDown(self) -> None:
        self._root_directory.cleanup()

    def test_scan(self) -> None:
        podcast_folder = pathlib.Path(self.root, "podcast")
        os.mkdir(podcast_folder)

        now = 1330712292
        files = [
            "podcast_first.mp3",
            "podcast_second.mp3",
            "podcast_third.mp3",
            "podcast_fourth_ç.mp3",
        ]
        for x in files:
            full_path = pathlib.Path(podcast_folder, x)
            shutil.copyfile(
                pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
                full_path,
            )
            os.utime(full_path, (now, now))
            now += 10000

        p = podcast_show.PodcastShow(podcast_folder, podcast_show.P0)
        self.assertEqual([], p.remaining_episodes())

        p.scan_for_updates(self.root, allow_prompt=False)

        self.assertEqual(len(files), len(p.remaining_episodes()))
        self.assertEqual(
            test_utils.TEST_FILE_LENGTH_IN_SECONDS * len(files), p.remaining_time()
        )

        episodes: typing.List[podcast_episode.PodcastEpisode] = []
        for index, episode in enumerate(files):
            paths_to_ignore = [x.path for x in episodes]
            next_episode = p.first_episode(files_to_ignore=paths_to_ignore)
            self.assertIsNotNone(next_episode)
            episodes.append(next_episode)  # type:ignore
            self.assertEqual(episode, os.path.basename(episodes[-1].path))
            self.assertEqual(index + 1, episodes[-1].index)

            paths_to_ignore = [x.path for x in episodes]
            remaining_episodes = len(files) - len(episodes)
            self.assertEqual(
                remaining_episodes,
                len(p.remaining_episodes(files_to_ignore=paths_to_ignore)),
            )
            self.assertEqual(
                remaining_episodes * test_utils.TEST_FILE_LENGTH_IN_SECONDS,
                p.remaining_time(files_to_ignore=paths_to_ignore),
            )

        paths_to_ignore = [x.path for x in episodes]
        self.assertIsNone(p.first_episode(files_to_ignore=paths_to_ignore))
        self.assertEqual(0, p.remaining_time(files_to_ignore=paths_to_ignore))

    def test_save_and_load(self) -> None:
        podcast_folder = pathlib.Path(self.root, "podcast")
        os.mkdir(podcast_folder)

        p = podcast_show.PodcastShow(podcast_folder, podcast_show.P0)
        self.assertEqual([], p.remaining_episodes())

        saved = io.StringIO()
        p.save(saved)

        want = "%s\nNone\n0\n" % (podcast_folder.name)
        self.assertEqual(want, saved.getvalue())

        p.load(io.StringIO(saved.getvalue()))
        self.assertEqual(podcast_folder, p.podcast_folder)
        self.assertEqual([], p.remaining_episodes())

        # Add a file and ensure it appears.
        podcast_file = pathlib.Path(podcast_folder, "podcast_1_c.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            podcast_file,
        )
        now = 1330712222
        os.utime(podcast_file, (now, now))

        self.assertEqual(
            [podcast_file], p.scan_for_updates(self.root, allow_prompt=False)
        )
        self.assertEqual([], p.scan_for_updates(self.root, allow_prompt=False))

        saved = io.StringIO()
        p.save(saved)

        want = "%s\n2\n1\n%s\n1\n%d\n%d\n" % (
            podcast_folder.name,
            podcast_file,
            test_utils.TEST_FILE_LENGTH_IN_SECONDS,
            now,
        )
        self.assertEqual(saved.getvalue(), want)

        p.load(io.StringIO(saved.getvalue()))
        self.assertEqual(1, len(p.remaining_episodes()))

        # Remove the file and ensure we revert back to the original state.
        os.remove(podcast_file)

        self.assertEqual([], p.scan_for_updates(self.root, allow_prompt=False))

        saved = io.StringIO()
        p.save(saved)

        want = "%s\n2\n0\n" % (podcast_folder.name)
        self.assertEqual(want, saved.getvalue())

        p.load(io.StringIO(saved.getvalue()))
        self.assertEqual(0, len(p.remaining_episodes()))

    def test_preprocess(self) -> None:
        podcast_folder = pathlib.Path(self.root, "my_podcast")
        os.mkdir(podcast_folder)

        # Add a file and ensure it is deleted by the preprocess function.
        podcast_file = pathlib.Path(podcast_folder, "podcast_1.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            podcast_file,
        )
        self.assertTrue(podcast_file.is_file())

        def clear_file(
            folder: pathlib.Path,
            _lambda: podcast_preprocessing_base.DeletePrompt_TypeAlias,
        ) -> None:
            os.remove(pathlib.Path(folder, podcast_file))

        p = podcast_show.PodcastShow(
            podcast_folder, podcast_show.P0, preprocess=clear_file
        )
        p.scan_for_updates(self.root)
        self.assertFalse(os.path.exists(podcast_file))

    def test_bad_load(self) -> None:
        podcast_folder = pathlib.Path(self.root, "my_podcast")
        p = podcast_show.PodcastShow(podcast_folder, podcast_show.P0)
        self.assertIsNone(p.load(io.StringIO("bad_podcast\n0\n")))

    def test_get_episode_present(self) -> None:
        podcast_folder = pathlib.Path(self.root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "podcast_first.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            full_path,
        )
        now = 666
        os.utime(full_path, (now, now))

        p = podcast_show.PodcastShow(podcast_folder, podcast_show.P0)
        p.scan_for_updates(self.root, allow_prompt=False)

        expected_value = full_podcast_episode.FullPodcastEpisode(
            1,
            full_path,
            "podcast",
            podcast_show.DEFAULT_SPEED,
            archive.Archive.NO,
            datetime.datetime.fromtimestamp(now),
            datetime.timedelta(seconds=test_utils.TEST_FILE_LENGTH_IN_SECONDS),
        )
        self.assertEqual(expected_value, p.get_episode(full_path))

    def test_get_episode_not_present(self) -> None:
        podcast_folder = pathlib.Path(self.root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "podcast_first.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            full_path,
        )

        p = podcast_show.PodcastShow(podcast_folder, podcast_show.P0)
        p.scan_for_updates(self.root, allow_prompt=False)

        self.assertFalse(p.get_episode(pathlib.Path("fake_path")))


if __name__ == "__main__":
    unittest.main()
