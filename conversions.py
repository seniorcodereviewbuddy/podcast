import math
import os
import pathlib

import ffmpeg_helper

LOUDNESS_TARGET = -10.0


def ConvertMatchingFileTypesInFolder(
    folder: pathlib.Path, input_file_type: str, output_file_type: str
) -> None:
    for file in folder.iterdir():
        ext = file.suffix.lower()
        if ext.lower() == input_file_type:
            ffmpeg_helper.ConvertFile(file, file.with_suffix(output_file_type))
            # No need to keep the original file around now.
            os.remove(file)


def CreateAdjustedPodcastForPlayback(
    input_file: pathlib.Path, output_file: pathlib.Path, speed: float
) -> None:
    stream = ffmpeg_helper.ffmpeg.input(str(input_file))
    stream = ffmpeg_helper.ffmpeg.filter(
        stream, filter_name="loudnorm", i=LOUDNESS_TARGET
    )
    if not math.isclose(1.0, speed):
        stream = ffmpeg_helper.ffmpeg.filter(stream, filter_name="atempo", tempo=speed)

    stream = ffmpeg_helper.ffmpeg.output(stream, str(output_file))
    ffmpeg_helper.ffmpeg.run(stream, cmd=ffmpeg_helper.FFMPEG_EXE)
