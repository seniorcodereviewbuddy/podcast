import math
import os
import pathlib
import shutil
import tempfile

from mutagen.id3 import ID3, TALB, TIT2, ID3NoHeaderError  # type: ignore
from mutagen.mp4 import MP4

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


def PrepareAudioAndMove(
    file: pathlib.Path, dest: pathlib.Path, album: str, title_prefix: str, speed: float
) -> None:
    tmpdir = tempfile.TemporaryDirectory()
    copy1 = pathlib.Path(tmpdir.name, file.name)
    shutil.copyfile(file, copy1)

    print("Preparing Audio file %s" % file)
    ext = copy1.suffix.lower()
    if ext == ".mp3":
        try:
            tags = ID3(str(copy1))  # type: ignore
        except ID3NoHeaderError:
            tags = ID3()  # type: ignore
        tags[audio_metadata.MP3_ID3_ALBUM_TAG] = TALB(encoding=3, text=album)  # type: ignore

        current_title = audio_metadata.GetTitle(file)
        if current_title:
            tags[audio_metadata.MP3_ID3_TITLE_TAG] = TIT2(encoding=3, text=title_prefix + current_title)  # type: ignore
        else:
            tags[audio_metadata.MP3_ID3_TITLE_TAG] = TIT2(encoding=3, text=title_prefix + os.path.basename(file))  # type: ignore

        tags.save(copy1)
    elif ext == ".m4a":
        m4a_file = MP4(str(copy1))  # type: ignore
        m4a_file[audio_metadata.M4A_ALBUM_TAG] = album

        current_title = audio_metadata.GetTitle(file)
        if current_title:
            if isinstance(current_title, list):
                current_title = current_title[0]
            m4a_file[audio_metadata.M4A_TITLE_TAG] = title_prefix + current_title
        else:
            m4a_file[audio_metadata.M4A_TITLE_TAG] = title_prefix + os.path.basename(
                file
            )
        m4a_file.save()  # type: ignore
    else:
        raise Exception("Unhandled filetype, path %s" % file)

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
