import os
import pathlib

import ffmpeg_helper


# TODO: Add tests, and make one function that just takes the pattern of files to convert.
def ConvertAllMP4ToMP3(folder: pathlib.Path) -> None:
    # Convert all mp4 to mp3
    for file in folder.iterdir():
        ext = file.suffix.lower()
        if ext.lower() == ".mp4":
            ffmpeg_helper.ConvertFile(file, file.with_suffix(".mp3"))
            # No need to keep the original file around now
            os.remove(file)


def ConvertAllWEBMToMP3(folder: pathlib.Path) -> None:
    # Convert all webm to mp3
    for file in folder.iterdir():
        ext = file.suffix.lower()
        if ext.lower() == ".webm":
            ffmpeg_helper.ConvertFile(file, file.with_suffix(".mp3"))
            # No need to keep the original file around now
            os.remove(file)
