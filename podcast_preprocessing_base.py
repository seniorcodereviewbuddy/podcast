import pathlib
import typing

import user_input

DeletePrompt_TypeAlias = typing.Callable[[pathlib.Path], bool]
PreProcess_TypeAlias = typing.Callable[[pathlib.Path, DeletePrompt_TypeAlias], None]


def prompt_for_delete(file: pathlib.Path) -> bool:
    return user_input.prompt_yes_or_no("Do you want to delete %s" % file)


def PreProcessAddMP3Suffix(
    folder: pathlib.Path, delete_prompt: DeletePrompt_TypeAlias
) -> None:
    for file in folder.iterdir():
        # For some reason they stopped marking the files as mp3, even though they are.
        if not file.suffix:
            new_file = file.rename(file.with_suffix(".mp3"))
            print(f"Renamed %{file} to %{new_file}")
