import pathlib
import shutil
import tempfile
import unittest

import conversions
import test_utils


class TestConversions(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def CreateTestFileCopies(
        self, test_file: str, number_of_copies: int = 5
    ) -> list[pathlib.Path]:
        test_file_full_path = pathlib.Path(test_utils.TEST_DATA_DIR, test_file)

        copies = []
        suffix = test_file.split(".")[-1]
        for x in range(number_of_copies):
            path = pathlib.Path(self.tempdir.name, f"test-{x}.{suffix}")
            shutil.copyfile(
                test_file_full_path,
                path,
            )
            copies.append(path)

        return copies

    def test_ConvertMatchingFileTypesInFolder_MP4sToMP3s(self) -> None:
        files = self.CreateTestFileCopies(test_utils.MP4_TEST_FILE)

        conversions.ConvertMatchingFileTypesInFolder(
            pathlib.Path(self.tempdir.name), ".mp4", ".mp3"
        )

        for file in files:
            self.assertFalse(file.exists())
            self.assertTrue(file.with_suffix(".mp3").exists())

    def test_ConvertMatchingFileTypesInFolder_WebmToM4A(self) -> None:
        files = self.CreateTestFileCopies(test_utils.WEBM_TEST_FILE)

        conversions.ConvertMatchingFileTypesInFolder(
            pathlib.Path(self.tempdir.name), ".webm", ".mp3"
        )

        for file in files:
            self.assertFalse(file.exists())
            self.assertTrue(file.with_suffix(".mp3").exists())

    def test_ConvertMatchingFileTypesInFolder_WebmToM4A_SomeOtherFilesPresent(
        self,
    ) -> None:
        matching_files = self.CreateTestFileCopies(test_utils.WEBM_TEST_FILE)

        unmatching_file = pathlib.Path(self.tempdir.name, "unmatched-mp4.mp4")
        shutil.copyfile(
            pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP4_TEST_FILE),
            unmatching_file,
        )

        conversions.ConvertMatchingFileTypesInFolder(
            pathlib.Path(self.tempdir.name), ".webm", ".mp3"
        )

        for file in matching_files:
            self.assertFalse(file.exists())
            self.assertTrue(file.with_suffix(".mp3").exists())

        # Ensure the unmatched file wasn't converted.
        self.assertTrue(unmatching_file.exists())
        self.assertFalse(unmatching_file.with_suffix(".mp3").exists())

    def test_ConvertMatchingFileTypesInFolder_NoMatches(self) -> None:
        files = self.CreateTestFileCopies(test_utils.MP4_TEST_FILE)

        conversions.ConvertMatchingFileTypesInFolder(
            pathlib.Path(self.tempdir.name), ".webm", ".mp3"
        )

        for file in files:
            self.assertTrue(file.exists())
            self.assertFalse(file.with_suffix(".mp3").exists())


if __name__ == "__main__":
    unittest.main()
