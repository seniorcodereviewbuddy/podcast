import io
import os
import pathlib
import shutil
import tempfile
import unittest

import models
import podcast_episode
import test_utils


def touch(file: pathlib.Path) -> None:
    with open(file, "w+") as f:
        f.write("1")


class TestPodcastEpisode(unittest.TestCase):
    def test_podcast_episode_new(self) -> None:
        podcast_folder = tempfile.mkdtemp()
        podcast_file = pathlib.Path(podcast_folder, "file.mp3")
        index = 10

        shutil.copyfile(
            os.path.join(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE),
            podcast_file,
        )

        episode = podcast_episode.PodcastEpisode.new(podcast_file, index)

        self.assertEqual(podcast_file, episode.path)
        self.assertEqual(index, episode.index)
        self.assertEqual(test_utils.TEST_FILE_LENGTH_IN_SECONDS, episode.duration)

        saved_data = io.StringIO()
        episode.save(saved_data)

        want = "%s\n%d\n%d\n%d\n" % (
            podcast_file,
            index,
            test_utils.TEST_FILE_LENGTH_IN_SECONDS,
            episode.modification_time,
        )
        self.assertEqual(want, saved_data.getvalue())

    def test_podcast_episode_load_and_save(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\n100\n")
        episode = podcast_episode.PodcastEpisode.load(data)

        saved_data = io.StringIO()
        episode.save(saved_data)
        self.assertEqual(data.getvalue(), saved_data.getvalue())

    def test_podcast_episode_load_bad_data_only_path(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_podcast_episode_load_bad_data_missing_duration_and_modification(
        self,
    ) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_podcast_episode_load_bad_data_missing_modification(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_podcast_episode_load_bad_data_index_not_int(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\nbad index\n15\n100\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_podcast_episode_load_bad_data_duration_not_int(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\nbad duration\n100\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_podcast_episode_load_bad_data_modification_not_int(self) -> None:
        data = io.StringIO("c:\\podcast\\podcast.mp3\n66\n15\nbad modification\n")
        with self.assertRaises(podcast_episode.PodcastEpisodeLoadingError):
            podcast_episode.PodcastEpisode.load(data)

    def test_is_podcast_file(self) -> None:
        podcast_folder = tempfile.mkdtemp()

        good_files = ["test.mp3", "test.m4a"]
        for x in good_files:
            p = pathlib.Path(podcast_folder, x)
            touch(p)
            self.assertTrue(podcast_episode.is_podcast_file(p))

        bad_files = ["test.db", "test.jpg", "test.jpeg", "test.partial", "test.png"]
        for x in bad_files:
            p = pathlib.Path(podcast_folder, x)
            touch(p)
            self.assertFalse(podcast_episode.is_podcast_file(p))

    def test_to_model(self) -> None:
        """Test converting PodcastEpisode to SQLAlchemy model."""
        path = pathlib.Path("/path/to/episode.mp3")
        episode = podcast_episode.PodcastEpisode(
            path=path,
            index=42,
            duration=3600,
            modification_time=1234567890,
        )
        show_id = 5

        model = episode.to_model(show_id)

        self.assertEqual(show_id, model.show_id)
        self.assertEqual(str(path), model.path)  # Path converted to string
        self.assertEqual(42, model.episode_index)
        self.assertEqual(3600, model.duration)
        self.assertEqual(1234567890, model.modification_time)

    def test_from_model(self) -> None:
        """Test creating PodcastEpisode from SQLAlchemy model."""
        model = models.EpisodeModel(
            show_id=5,
            path="/path/to/episode.mp3",
            episode_index=42,
            duration=3600,
            modification_time=1234567890,
        )

        episode = podcast_episode.PodcastEpisode.from_model(model)

        self.assertEqual(pathlib.Path("/path/to/episode.mp3"), episode.path)
        self.assertEqual(42, episode.index)
        self.assertEqual(3600, episode.duration)
        self.assertEqual(1234567890, episode.modification_time)

    def test_to_model_from_model_roundtrip(self) -> None:
        """Test round-trip conversion between PodcastEpisode and model."""
        original = podcast_episode.PodcastEpisode(
            path=pathlib.Path("/path/to/episode.mp3"),
            index=42,
            duration=3600,
            modification_time=1234567890,
        )
        show_id = 5

        model = original.to_model(show_id)
        restored = podcast_episode.PodcastEpisode.from_model(model)

        self.assertEqual(original.path, restored.path)
        self.assertEqual(original.index, restored.index)
        self.assertEqual(original.duration, restored.duration)
        self.assertEqual(original.modification_time, restored.modification_time)


if __name__ == "__main__":
    unittest.main()
