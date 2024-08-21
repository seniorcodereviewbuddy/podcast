import os
import shutil
import tempfile
import unittest

import move_file
import test_utils


class TestMoveFile(unittest.TestCase):
    def setUp(self) -> None:
        self.holding_dir = tempfile.TemporaryDirectory()

        self.podcast_show_name = "podcast_show"

        test_file_source = os.path.join(
            test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE
        )
        self.podcast_file = os.path.join(
            self.holding_dir.name, test_utils.MP3_TEST_FILE
        )
        shutil.copyfile(test_file_source, self.podcast_file)

        self.destination = os.path.join(self.holding_dir.name, "destination")
        os.makedirs(self.destination)

        self.archive = os.path.join(self.holding_dir.name, "archive")

        self.destination_podcast_path = os.path.join(
            self.destination, os.path.basename(self.podcast_file)
        )
        self.archived_podcast_path = os.path.join(
            self.archive, self.podcast_show_name, os.path.basename(self.podcast_file)
        )

    def tearDown(self) -> None:
        self.holding_dir.cleanup()

    def testDryRunArchive(self) -> None:
        args = [
            "--dry-run",
            "--archive-folder",
            self.archive,
            "--podcast-show-name",
            self.podcast_show_name,
            "--file-path",
            self.podcast_file,
            "--destination",
            self.destination,
        ]
        move_file.main(args)
        self.assertTrue(os.path.isfile(self.podcast_file))
        self.assertFalse(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))

    def testDryRunNoArchive(self) -> None:
        args = [
            "--dry-run",
            "--podcast-show-name",
            self.podcast_show_name,
            "--file-path",
            self.podcast_file,
            "--destination",
            self.destination,
        ]
        move_file.main(args)
        self.assertTrue(os.path.isfile(self.podcast_file))
        self.assertFalse(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))

    def testProdRunArchive(self) -> None:
        args = [
            "--archive-folder",
            self.archive,
            "--podcast-show-name",
            self.podcast_show_name,
            "--file-path",
            self.podcast_file,
            "--destination",
            self.destination,
        ]
        move_file.main(args)
        self.assertFalse(os.path.isfile(self.podcast_file))
        self.assertTrue(os.path.isfile(self.destination_podcast_path))
        self.assertTrue(os.path.isfile(self.archived_podcast_path))

    def testProdRunNoArchive(self) -> None:
        args = [
            "--podcast-show-name",
            self.podcast_show_name,
            "--file-path",
            self.podcast_file,
            "--destination",
            self.destination,
        ]
        move_file.main(args)
        self.assertFalse(os.path.isfile(self.podcast_file))
        self.assertTrue(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))


if __name__ == "__main__":
    unittest.main()
