import copy
import datetime
import pathlib
import unittest

import archive
import full_podcast_episode


class TestFullPodcastEpisode(unittest.TestCase):
    def testEquality(self) -> None:
        selected = full_podcast_episode.FullPodcastEpisode(
            index=1,
            path=pathlib.Path("Test/Path"),
            podcast_show_name="Test Show",
            speed=1.0,
            archive=archive.Archive.NO,
            modification_time=datetime.datetime.fromisoformat("2020-02-02"),
            duration=datetime.timedelta(seconds=10),
        )

        selected_copy = copy.deepcopy(selected)
        self.assertEqual(selected, selected_copy)

        wrong_index = copy.deepcopy(selected)
        wrong_index.index += 1
        self.assertNotEqual(selected, wrong_index)

        wrong_path = copy.deepcopy(selected)
        wrong_path.path = wrong_path.path.with_name("different_name")
        self.assertNotEqual(selected, wrong_path)

        wrong_show_name = copy.deepcopy(selected)
        wrong_show_name.podcast_show_name += "different"
        self.assertNotEqual(selected, wrong_show_name)

        wrong_speed = copy.deepcopy(selected)
        wrong_speed.speed += 1
        self.assertNotEqual(selected, wrong_speed)

        wrong_archive = copy.deepcopy(selected)
        wrong_archive.archive = archive.Archive.YES
        self.assertNotEqual(selected, wrong_archive)

        wrong_modification_time = copy.deepcopy(selected)
        wrong_modification_time.modification_time += datetime.timedelta(hours=1)
        self.assertNotEqual(selected, wrong_modification_time)

        wrong_duration = copy.deepcopy(selected)
        wrong_duration.duration += datetime.timedelta(hours=1)
        self.assertNotEqual(selected, wrong_duration)

    def testStr(self) -> None:
        selected = full_podcast_episode.FullPodcastEpisode(
            index=1,
            path=pathlib.Path("Test/Path"),
            podcast_show_name="Test Show",
            speed=1.0,
            archive=archive.Archive.NO,
            modification_time=datetime.datetime.fromisoformat("2020-02-02"),
            duration=datetime.timedelta(seconds=10),
        )

        expected_string = "FullPodcastEpisode(Test\\Path:(10s) with index 1 from Test Show with speed 1.00, archive Archive.NO and modification_time 2020-02-02 00:00:00)"
        self.assertEqual(expected_string, str(selected))


if __name__ == "__main__":
    unittest.main()
