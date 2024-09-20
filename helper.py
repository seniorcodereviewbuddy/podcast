import math
import os
import pathlib
import shutil
import tempfile

import audio_metadata
import ffmpeg_helper


def SecondsToString(seconds: float) -> str:
    days, remainder = divmod(seconds, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    duration_string = ""
    if days > 0:
        duration_string += "%dd" % days
    if hours > 0:
        duration_string += "%dh" % hours
    if minutes > 0:
        duration_string += "%dm" % minutes
    if seconds > 0:
        duration_string += "%ds" % seconds

    if not duration_string:
        duration_string = "0s"

    return duration_string


def _GenerateTitle(file: pathlib.Path, title_prefix: str) -> str:
    current_title = audio_metadata.GetTitle(file)
    if current_title:
        return title_prefix + current_title

    return title_prefix + os.path.basename(file)


def PrepareAudioAndMove(
    file: pathlib.Path, dest: pathlib.Path, album: str, title_prefix: str, speed: float
) -> None:
    tmpdir = tempfile.TemporaryDirectory()
    copy1 = pathlib.Path(tmpdir.name, file.name)
    shutil.copyfile(file, copy1)

    print("Preparing Audio file %s" % file)
    new_title = _GenerateTitle(file, title_prefix)
    audio_metadata.SetMetadata(copy1, title=new_title, album=album)

    stream = ffmpeg_helper.ffmpeg.input(str(copy1))
    stream = ffmpeg_helper.ffmpeg.filter(stream, filter_name="loudnorm", i=-10.0)
    if not math.isclose(1.0, speed):
        stream = ffmpeg_helper.ffmpeg.filter(stream, filter_name="atempo", tempo=speed)

    copy2 = pathlib.Path(tmpdir.name, "2-" + file.name)
    stream = ffmpeg_helper.ffmpeg.output(stream, str(copy2))
    ffmpeg_helper.ffmpeg.run(stream, cmd=ffmpeg_helper.FFMPEG_EXE)

    print("Moving %s to %s" % (file, dest))
    shutil.move(copy2, dest)
    os.remove(file)
    print("Done")
