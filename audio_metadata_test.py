import pathlib
import unittest

import audio_metadata
import test_utils


class TestAudioMetadata(unittest.TestCase):
    def testGetAlbumMP3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = audio_metadata.GetAlbum(full_path)
        self.assertEqual("Test Data Album", title)

    def testGetAlbumMP3ValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.GetAlbum(full_path)
        self.assertEqual(
            audio_metadata.NO_ALBUM_FOUND,
            title,
        )

    def testGetAlbumM4A(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = audio_metadata.GetAlbum(full_path)
        self.assertEqual(
            "m4a test album",
            title,
        )

    def testGetAlbumM4AValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.GetAlbum(full_path)
        self.assertEqual(
            audio_metadata.NO_ALBUM_FOUND,
            title,
        )

    def testGetTitleMP3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = audio_metadata.GetTitle(full_path)
        self.assertEqual("Test MP3", title)

    def testGetTitleMP3ValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.GetTitle(full_path)
        self.assertEqual(
            audio_metadata.NO_TITLE_FOUND,
            title,
        )

    def testGetTitleM4A(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = audio_metadata.GetTitle(full_path)
        self.assertEqual(
            "m4a test",
            title,
        )

    def testGetTitleM4AValueMissing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.GetTitle(full_path)
        self.assertEqual(
            audio_metadata.NO_TITLE_FOUND,
            title,
        )


if __name__ == "__main__":
    unittest.main()
