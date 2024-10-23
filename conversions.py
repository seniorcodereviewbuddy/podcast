import math
import os
import pathlib

import ffmpeg

FFMPEG_EXE = "ffmpeg.exe"

LOUDNESS_TARGET = -10.0


def _ConvertFile(input_file: pathlib.Path, output_file: pathlib.Path) -> None:
    print("Converting %s to %s" % (input_file, output_file))
    stream = ffmpeg.input(str(input_file))
    stream = ffmpeg.output(stream, str(output_file))
    ffmpeg.run(stream, cmd=FFMPEG_EXE)

    # No need to keep the original file around now as it's been converted.
    os.remove(input_file)

    print("Done conversion")


def convert_matching_file_types_in_folder(
    folder: pathlib.Path, input_file_type: str, output_file_type: str
) -> None:
    for file in folder.iterdir():
        ext = file.suffix.lower()
        if ext.lower() == input_file_type:
            _ConvertFile(file, file.with_suffix(output_file_type))


def create_adjusted_podcast_for_playback(
    input_file: pathlib.Path, output_file: pathlib.Path, speed: float
) -> None:
    stream = ffmpeg.input(str(input_file))
    stream = ffmpeg.filter(stream, filter_name="loudnorm", i=LOUDNESS_TARGET)
    if not math.isclose(1.0, speed):
        stream = ffmpeg.filter(stream, filter_name="atempo", tempo=speed)

    stream = ffmpeg.output(stream, str(output_file))
    ffmpeg.run(stream, cmd=FFMPEG_EXE)
