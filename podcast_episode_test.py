import io
import os
import pathlib
import shutil
import tempfile
import unittest

import podcast_episode
import test_utils


def touch(file: pathlib.Path) -> None:
    with open(file, "w+") as f:
        f.write("1")


class TestPodcastEpisode(unittest.TestCase):
    def testPodcastEpisodeNew(self) -> None:
        podcast_folder = tempfile.mkdtemp()
        podcast_file = pathlib.Path(podcast_folder, "file.mp3")
        index = 10

        shutil.copyfile(
            os.path.join(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            podcast_file,
        )

        episode = podcast_episode.PodcastEpisode.New(podcast_file, index)

        self.assertEqual(podcast_file, episode.path)
        self.assertEqual(index, episode.index)
        self.assertEqual(test_utils.TEST_FILE_LENGTH_IN_SECONDS, episode.duration)

        saved_data = io.StringIO()
        episode.Save(saved_data)

        want = "%s\n%d\n%d\n%d\n" % (
            podcast_file,
            index,
            test_utils.TEST_FILE_LENGTH_IN_SECONDS,
            episode.modification_time,
        )
        self.assertEqual(want, saved_data.getvalue())

    def testPodcastEpisodeLoadAndSave(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\n100\n")
        episode = podcast_episode.PodcastEpisode.Load(data)

        saved_data = io.StringIO()
        episode.Save(saved_data)
        self.assertEqual(data.getvalue(), saved_data.getvalue())

    def testPodcastEpisodeLoadBadData_OnlyPath(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testPodcastEpisodeLoadBadData_MissingDurationAndModification(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testPodcastEpisodeLoadBadData_MissingModification(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testPodcastEpisodeLoadBadData_IndexNotInt(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\nbad index\n15\n100\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testPodcastEpisodeLoadBadData_DurationNotInt(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\nbad duration\n100\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testPodcastEpisodeLoadBadData_ModificationNotInt(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\nbad modification\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.Load(data)

    def testIsPodcastFile(self) -> None:
        podcast_folder = tempfile.mkdtemp()

        good_files = ["test.mp3", "test.m4a"]
        for x in good_files:
            p = pathlib.Path(podcast_folder, x)
            touch(p)
            self.assertTrue(podcast_episode.IsPodcastFile(p))

        bad_files = ["test.db", "test.jpg", "test.jpeg", "test.partial", "test.png"]
        for x in bad_files:
            p = pathlib.Path(podcast_folder, x)
            touch(p)
            self.assertFalse(podcast_episode.IsPodcastFile(p))


if __name__ == "__main__":
    unittest.main()
