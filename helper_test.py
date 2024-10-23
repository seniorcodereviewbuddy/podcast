import os
import pathlib
import shutil
import tempfile
import unittest

import audio_metadata
import helper
import test_utils


class TestHelper(unittest.TestCase):
    def test_prepare_audio_and_move_mp3(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.mp3")
        final_full_path = pathlib.Path(podcast_folder, "test_finally.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE), full_path
        )

        helper.prepare_audio_and_move(
            full_path, final_full_path, "new_title", "podcast album", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual("new_title", audio_metadata.get_title(final_full_path))
        self.assertEqual("podcast album", audio_metadata.get_album(final_full_path))

    def test_list_title_and_album(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.m4a")
        final_full_path = pathlib.Path(podcast_folder, "test_finally.m4a")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE),
            full_path,
        )

        helper.prepare_audio_and_move(
            full_path, final_full_path, "new_title", "podcast album", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual(
            "new_title",
            audio_metadata.get_title(final_full_path),
        )
        self.assertEqual("podcast album", audio_metadata.get_album(final_full_path))

    def test_list_title_and_album_after_no_title_or_album(self) -> None:
        root = tempfile.mkdtemp()
        podcast_folder = pathlib.Path(root, "podcast")
        os.mkdir(podcast_folder)

        full_path = pathlib.Path(podcast_folder, "test.mp3")
        final_full_path = pathlib.Path(podcast_folder, "final_test.mp3")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM),
            full_path,
        )

        helper.prepare_audio_and_move(
            full_path, final_full_path, "new_title", "podcast album", 1.0
        )
        self.assertFalse(os.path.exists(full_path))
        self.assertTrue(os.path.exists(final_full_path))
        self.assertEqual(
            "new_title",
            audio_metadata.get_title(final_full_path),
        )
        self.assertEqual("podcast album", audio_metadata.get_album(final_full_path))


if __name__ == "__main__":
    unittest.main()
