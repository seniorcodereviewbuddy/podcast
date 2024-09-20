import os
import pathlib
import shutil
import tempfile
import unittest

import audio_metadata
import move_file
import test_utils


class TestMoveFile(unittest.TestCase):
    def setUp(self) -> None:
        self.holding_dir = tempfile.TemporaryDirectory()

        test_file_source = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE
        )
        self.podcast_file = pathlib.Path(
            self.holding_dir.name, test_utils.MP3_TEST_FILE
        )
        shutil.copyfile(test_file_source, self.podcast_file)

        self.destination = pathlib.Path(self.holding_dir.name, "destination")
        os.makedirs(self.destination)

        self.archive = pathlib.Path(self.holding_dir.name, "archive")

        self.destination_podcast_path = pathlib.Path(
            self.destination, os.path.basename(self.podcast_file)
        )
        self.archived_podcast_path = pathlib.Path(
            self.archive, "fake_show_archive", os.path.basename(self.podcast_file)
        )

    def tearDown(self) -> None:
        self.holding_dir.cleanup()

    def testDryRunArchive(self) -> None:
        args = [
            "--dry-run",
            "--archive-destination",
            str(self.archived_podcast_path),
            "--file-path",
            str(self.podcast_file),
            "--file-destination",
            str(self.destination_podcast_path),
            "--title",
            "new_title",
            "--album",
            "new_album",
        ]
        move_file.main(args)
        self.assertTrue(os.path.isfile(self.podcast_file))
        self.assertFalse(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))

    def testDryRunNoArchive(self) -> None:
        args = [
            "--dry-run",
            "--file-path",
            str(self.podcast_file),
            "--file-destination",
            str(self.destination_podcast_path),
            "--title",
            "new_title",
            "--album",
            "new_album",
        ]
        move_file.main(args)
        self.assertTrue(os.path.isfile(self.podcast_file))
        self.assertFalse(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))

    def testProdRunArchive(self) -> None:
        args = [
            "--archive-destination",
            str(self.archived_podcast_path),
            "--file-path",
            str(self.podcast_file),
            "--file-destination",
            str(self.destination_podcast_path),
            "--title",
            "new_title",
            "--album",
            "new_album",
        ]
        move_file.main(args)
        self.assertFalse(os.path.isfile(self.podcast_file))
        self.assertTrue(os.path.isfile(self.destination_podcast_path))
        self.assertTrue(os.path.isfile(self.archived_podcast_path))

        self.assertEqual(
            "new_title", audio_metadata.GetTitle(self.destination_podcast_path)
        )
        self.assertEqual(
            "new_album", audio_metadata.GetAlbum(self.destination_podcast_path)
        )

    def testProdRunNoArchive(self) -> None:
        args = [
            "--file-path",
            str(self.podcast_file),
            "--file-destination",
            str(self.destination_podcast_path),
            "--title",
            "new_title",
            "--album",
            "new_album",
        ]
        move_file.main(args)
        self.assertFalse(os.path.isfile(self.podcast_file))
        self.assertTrue(os.path.isfile(self.destination_podcast_path))
        self.assertFalse(os.path.isfile(self.archived_podcast_path))

        self.assertEqual(
            "new_title", audio_metadata.GetTitle(self.destination_podcast_path)
        )
        self.assertEqual(
            "new_album", audio_metadata.GetAlbum(self.destination_podcast_path)
        )


if __name__ == "__main__":
    unittest.main()
