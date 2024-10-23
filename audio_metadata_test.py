import contextlib
import pathlib
import shutil
import tempfile
import types
import typing
import unittest

import audio_metadata
import test_utils


class TestFileCopyContextManager(contextlib.AbstractContextManager[pathlib.Path]):
    def __init__(self, test_file: str):
        self.test_file = pathlib.Path(test_utils.TEST_DATA_DIR, test_file)
        self.temp_directory = tempfile.TemporaryDirectory()
        self.full_path = pathlib.Path(self.temp_directory.name, test_file)

        shutil.copyfile(self.test_file, self.full_path)

    def __del__(self) -> None:
        self.temp_directory.cleanup()

    def __enter__(self) -> pathlib.Path:
        return self.full_path

    def __exit__(
        self,
        exctype: typing.Optional[typing.Type[BaseException]],
        excinst: typing.Optional[BaseException],
        exctb: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        pass


class TestAudioMetadata(unittest.TestCase):
    def test_get_album_m_p3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = audio_metadata.get_album(full_path)
        self.assertEqual("Test Data Album", title)

    def test_get_album_m_p3_value_missing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.get_album(full_path)
        self.assertEqual(
            audio_metadata.NO_ALBUM_FOUND,
            title,
        )

    def test_get_album_m4_a(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = audio_metadata.get_album(full_path)
        self.assertEqual(
            "m4a test album",
            title,
        )

    def test_get_album_m4_a_value_missing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.get_album(full_path)
        self.assertEqual(
            audio_metadata.NO_ALBUM_FOUND,
            title,
        )

    def test_get_title_m_p3(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP3_TEST_FILE)
        title = audio_metadata.get_title(full_path)
        self.assertEqual("Test MP3", title)

    def test_get_title_m_p3_value_missing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.MP3_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.get_title(full_path)
        self.assertEqual(
            audio_metadata.NO_TITLE_FOUND,
            title,
        )

    def test_get_title_m4_a(self) -> None:
        full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.M4A_TEST_FILE)
        title = audio_metadata.get_title(full_path)
        self.assertEqual(
            "m4a test",
            title,
        )

    def test_get_title_m4_a_value_missing(self) -> None:
        full_path = pathlib.Path(
            test_utils.TEST_DATA_DIR, test_utils.M4A_NO_TITLE_NO_ALBUM
        )
        title = audio_metadata.get_title(full_path)
        self.assertEqual(
            audio_metadata.NO_TITLE_FOUND,
            title,
        )

    def test_set_metadata_m_p3_album_and_title(self) -> None:
        with TestFileCopyContextManager(test_utils.MP3_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, "NEW_TITLE", "NEW_ALBUM")

            self.assertEqual("NEW_ALBUM", audio_metadata.get_album(full_path))
            self.assertEqual("NEW_TITLE", audio_metadata.get_title(full_path))

    def test_set_metadata_m_p3_only_title(self) -> None:
        with TestFileCopyContextManager(test_utils.MP3_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, title="NEW_TITLE")

            self.assertEqual("Test Data Album", audio_metadata.get_album(full_path))
            self.assertEqual("NEW_TITLE", audio_metadata.get_title(full_path))

    def test_set_metadata_m_p3_only_album(self) -> None:
        with TestFileCopyContextManager(test_utils.MP3_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, album="NEW_ALBUM")

            self.assertEqual("NEW_ALBUM", audio_metadata.get_album(full_path))
            self.assertEqual("Test MP3", audio_metadata.get_title(full_path))

    def test_set_metadata_m_p3_no_values(self) -> None:
        with TestFileCopyContextManager(test_utils.MP3_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path)

            self.assertEqual("Test Data Album", audio_metadata.get_album(full_path))
            self.assertEqual("Test MP3", audio_metadata.get_title(full_path))

    def test_set_metadata_m4_a_album_and_title(self) -> None:
        with TestFileCopyContextManager(test_utils.M4A_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, "NEW_TITLE", "NEW_ALBUM")

            self.assertEqual("NEW_ALBUM", audio_metadata.get_album(full_path))
            self.assertEqual("NEW_TITLE", audio_metadata.get_title(full_path))

    def test_set_metadata_m4_a_only_title(self) -> None:
        with TestFileCopyContextManager(test_utils.M4A_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, title="NEW_TITLE")

            self.assertEqual("m4a test album", audio_metadata.get_album(full_path))
            self.assertEqual("NEW_TITLE", audio_metadata.get_title(full_path))

    def test_set_metadata_m4_a_only_album(self) -> None:
        with TestFileCopyContextManager(test_utils.M4A_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path, album="NEW_ALBUM")

            self.assertEqual("NEW_ALBUM", audio_metadata.get_album(full_path))
            self.assertEqual("m4a test", audio_metadata.get_title(full_path))

    def test_set_metadata_m4_a_no_values(self) -> None:
        with TestFileCopyContextManager(test_utils.M4A_TEST_FILE) as full_path:
            audio_metadata.set_metadata(full_path)

            self.assertEqual("m4a test album", audio_metadata.get_album(full_path))
            self.assertEqual("m4a test", audio_metadata.get_title(full_path))

    def test_set_metadata_invalid__file__type(self) -> None:
        with tempfile.TemporaryDirectory() as f:
            full_path = pathlib.Path(f, "test.txt")
            full_path.touch()

            with self.assertRaises(audio_metadata.FileTypeError):
                audio_metadata.set_metadata(full_path, title="new_title")


if __name__ == "__main__":
    unittest.main()
