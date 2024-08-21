import itertools
import os
import pathlib
import shutil
import tempfile
import unittest

import backup
import test_utils


def AlwaysSayYes(x: str) -> bool:
    return True


class TestBackup(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tempfile.TemporaryDirectory()

        self.backup_folder = pathlib.Path(self.root.name, "backup")
        self.backup_folder.mkdir()

        self.backup_history = tempfile.NamedTemporaryFile(delete=False)
        self.backup_history.close()
        self.backup_history_path = pathlib.Path(self.backup_history.name)

    def tearDown(self) -> None:
        self.root.cleanup()

    def _FilesInBackupFolder(self) -> set[str]:
        return set(os.listdir(self.backup_folder))

    def _LoadFolderWithTestFiles(self, folder: pathlib.Path) -> set[str]:
        files = set(
            [
                test_utils.MP3_TEST_FILE,
                test_utils.MP3_DIFFERENT_TITLE_ENCODING,
                test_utils.MP3_WITH_MULTIPLE_UTF8,
                test_utils.MP3_WITH_EMOJI,
                test_utils.M4A_NO_TITLE_NO_ALBUM,
            ]
        )
        for file in files:
            dest = pathlib.Path(folder, file)
            shutil.copyfile(pathlib.Path(test_utils.TEST_DATA_DIR, file), dest)
        return files

    def testMoveFilesToBackup_NoFiles(self) -> None:
        self.assertCountEqual([], self._FilesInBackupFolder())

        local_backup = backup.Local(self.backup_folder, self.backup_history_path)
        local_backup.MoveFilesToBackup(set())

        self.assertCountEqual([], self._FilesInBackupFolder())

    def testMoveFilesToBackup_WithFiles(self) -> None:
        self.prebackup_folder = pathlib.Path(self.root.name, "prebackup")
        self.prebackup_folder.mkdir()

        files = self._LoadFolderWithTestFiles(self.prebackup_folder)
        files_full_path = set([pathlib.Path(self.prebackup_folder, x) for x in files])

        def FilesInPrebackupFolder() -> set[str]:
            return set(os.listdir(self.prebackup_folder))

        self.assertCountEqual([], self._FilesInBackupFolder())
        self.assertCountEqual(files, FilesInPrebackupFolder())

        local_backup = backup.Local(self.backup_folder, self.backup_history_path)
        local_backup.MoveFilesToBackup(files_full_path)

        self.assertCountEqual(files, self._FilesInBackupFolder())
        self.assertCountEqual([], FilesInPrebackupFolder())

    def testRemoveUnneededBackupFiles_Empty(self) -> None:
        local_backup = backup.Local(self.backup_folder, self.backup_history_path)

        local_backup.RemoveUnneededBackupFiles(set(), user_prompt=AlwaysSayYes)

    def testRemoveUnneededBackupFiles_AllFilesKept(self) -> None:
        local_backup = backup.Local(self.backup_folder, self.backup_history_path)

        files = self._LoadFolderWithTestFiles(self.backup_folder)

        local_backup.RemoveUnneededBackupFiles(files, user_prompt=AlwaysSayYes)

        self.assertCountEqual(files, self._FilesInBackupFolder())

    def testRemoveUnneededBackupFiles_AllFilesRemoved(self) -> None:
        local_backup = backup.Local(self.backup_folder, self.backup_history_path)

        self._LoadFolderWithTestFiles(self.backup_folder)

        local_backup.RemoveUnneededBackupFiles(set(), user_prompt=AlwaysSayYes)

        self.assertCountEqual([], self._FilesInBackupFolder())

    def testRemoveUnneededBackupFiles_SomeFilesRemoved(self) -> None:
        local_backup = backup.Local(self.backup_folder, self.backup_history_path)

        initial_files = self._LoadFolderWithTestFiles(self.backup_folder)

        final_files = set(itertools.islice(initial_files, len(initial_files) // 2))

        local_backup.RemoveUnneededBackupFiles(final_files, user_prompt=AlwaysSayYes)

        self.assertCountEqual(final_files, self._FilesInBackupFolder())


if __name__ == "__main__":
    unittest.main()
