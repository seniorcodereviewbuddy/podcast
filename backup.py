import datetime
import pathlib
import typing

import user_input


class Local:
    def __init__(self, backup_folder: pathlib.Path, backup_history: pathlib.Path):
        self.backup_folder = backup_folder
        self.backup_history = backup_history

    def move_files_to_backup(self, files: set[pathlib.Path]) -> None:
        with open(self.backup_history, "a", encoding="utf-8") as f:
            for file in files:
                dest = pathlib.Path(self.backup_folder, file.name)
                file.rename(dest)
                f.write(f"Copied {file} to backup folder")

    def remove_unneeded_backup_files(
        self,
        current_files_to_backup: typing.Set[str],
        user_prompt: user_input.PromptYesOrNo_Alias = user_input.prompt_yes_or_no,
    ) -> None:
        for file in self.backup_folder.iterdir():
            if not file.is_file():
                continue

            if file.name not in current_files_to_backup:
                if user_prompt(
                    f"{file.name} is no longer in the source, delete from backup"
                ):
                    with open(self.backup_history, "a", encoding="utf-8") as f:
                        date = datetime.datetime.now()
                        f.write(
                            "Deleting %s at %s\n"
                            % (file, date.strftime("%Y-%m-%d %H:%M:%S"))
                        )

                    file.unlink()
