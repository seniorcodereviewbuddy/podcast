import pathlib

import ffmpeg  # noqa:F401

__all__ = ["ffmpeg"]

FFMPEG_EXE = "ffmpeg.exe"


def ConvertFile(input_file: pathlib.Path, output_file: pathlib.Path) -> None:
    print("Converting %s to %s" % (input_file, output_file))
    stream = ffmpeg.input(str(input_file))
    stream = ffmpeg.output(stream, str(output_file))
    ffmpeg.run(stream, cmd=FFMPEG_EXE)
    print("Done conversion")
