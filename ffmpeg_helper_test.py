import pathlib
import shutil
import tempfile
import unittest

import ffmpeg_helper
import test_utils


class TestFFMPEGHelper(unittest.TestCase):
    def testConvertFileMP4toM4A(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            full_path = pathlib.Path(directory, "test.mp4")
            shutil.copyfile(
                pathlib.Path(test_utils.TEST_DATA_DIR, test_utils.MP4_TEST_FILE),
                full_path,
            )

            converted_file = pathlib.Path(directory, "test.m4a")
            self.assertFalse(converted_file.exists())
            ffmpeg_helper.ConvertFile(full_path, converted_file)
            self.assertTrue(converted_file.exists())


if __name__ == "__main__":
    unittest.main()
