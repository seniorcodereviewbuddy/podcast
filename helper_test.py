import os
import pathlib
import shutil
import tempfile
import unittest

import helper
import test_utils


class TestHelper(unittest.TestCase):
    def testGetAlbumMP3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = helper.GetAlbum(full_path)
        self.assertEqual("Test Data Album", title)

    def testGetAlbumMP3ValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = helper.GetAlbum(full_path)
        self.assertEqual(
            helper.NO_ALBUM_FOUND,
            title,
        )

    def testGetAlbumM4A(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = helper.GetAlbum(full_path)
        self.assertEqual(
            "m4a test album",
            title,
        )

    def testGetAlbumM4AValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = helper.GetAlbum(full_path)
        self.assertEqual(
            helper.NO_ALBUM_FOUND,
            title,
        )

    def testGetTitleMP3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = helper.GetTitle(full_path)
        self.assertEqual("Test MP3", title)

    def testGetTitleMP3ValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = helper.GetTitle(full_path)
        self.assertEqual(
            helper.NO_TITLE_FOUND,
            title,
        )

    def testGetTitleM4A(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = helper.GetTitle(full_path)
        self.assertEqual(
            "m4a test",
            title,
        )

    def testGetTitleM4AValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = helper.GetTitle(full_path)
        self.assertEqual(
            helper.NO_TITLE_FOUND,
            title,
        )

    def testPrepareAudioAndMoveMP3(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.mp3")
        final_full_path = pathlib.Path(podcast_folder, "test_finally.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE), full_path
        )

        helper.PrepareAudioAndMove(
            full_path, final_full_path, "podcast album", "title_prefix: ", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual("podcast album", helper.GetAlbum(final_full_path))
        self.assertEqual("title_prefix: Test MP3", helper.GetTitle(final_full_path))

    def testListTitleAndAlbum(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.m4a")
        final_full_path = pathlib.Path(podcast_folder, "test_finally.m4a")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE),
            full_path,
        )

        helper.PrepareAudioAndMove(
            full_path, final_full_path, "podcast album", "title_prefix: ", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual("podcast album", helper.GetAlbum(final_full_path))
        self.assertEqual(
            "title_prefix: m4a test",
            helper.GetTitle(final_full_path),
        )

    def testListTitleAndAlbumAfterNoTitleOrAlbum(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.mp3")
        final_full_path = pathlib.Path(podcast_folder, "final_test.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM),
            full_path,
        )

        helper.PrepareAudioAndMove(
            full_path, final_full_path, "podcast album", "title_prefix: ", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual("podcast album", helper.GetAlbum(final_full_path))
        self.assertEqual(
            "title_prefix: test.mp3",
            helper.GetTitle(final_full_path),
        )


if __name__ == "__main__":
    unittest.main()
