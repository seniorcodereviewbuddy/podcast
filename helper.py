import math
import os
import pathlib
import shutil
import tempfile

from mutagen.id3 import ID3, TALB, TIT2, ID3NoHeaderError  # type: ignore
from mutagen.mp4 import MP4

import ffmpeg_helper

MP3_ID3_ALBUM_TAG = "TALB"
MP3_ID3_TITLE_TAG = "TIT2"
M4A_ALBUM_TAG = "\xa9alb"
M4A_TITLE_TAG = "\xa9nam"

NO_TITLE_FOUND = ""
NO_ALBUM_FOUND = "(No Album Name Found)"


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


def _GetAlbumFromMP3(file: pathlib.Path) -> str:
    try:
        tags = ID3(str(file))  # type: ignore
    except ID3NoHeaderError:
        tags = ID3()  # type: ignore
    if MP3_ID3_ALBUM_TAG not in tags:
        return "(No Album Name Found)"
    album = tags[MP3_ID3_ALBUM_TAG].text
    assert isinstance(album, list), "album expected to be returned as list"
    return str(album[0])


def _GetAlbumFromM4A(file: pathlib.Path) -> str:
    m4a_file = MP4(str(file))  # type: ignore
    if M4A_ALBUM_TAG not in m4a_file:
        return NO_ALBUM_FOUND
    album = m4a_file[M4A_ALBUM_TAG]
    assert isinstance(album, list), "album expected to be returned as list"
    return str(album[0])


def GetAlbum(file: pathlib.Path) -> str:
    ext = file.suffix.lower()
    if ext == ".mp3":
        return _GetAlbumFromMP3(file)
    elif ext == ".m4a":
        return _GetAlbumFromM4A(file)

    raise Exception("Unhandled filetype, path %s" % file)


def GetTitle(file: pathlib.Path) -> str:
    ext = file.suffix.lower()
    if ext == ".mp3":
        try:
            tags = ID3(str(file))  # type: ignore
        except ID3NoHeaderError:
            tags = ID3()  # type: ignore

        if MP3_ID3_TITLE_TAG in tags and len(tags[MP3_ID3_TITLE_TAG].text) > 0:
            return str(tags[MP3_ID3_TITLE_TAG].text[0])

        return NO_TITLE_FOUND
    elif ext == ".m4a":
        m4a_file = MP4(str(file))  # type: ignore
        current_title = m4a_file.get(M4A_TITLE_TAG, NO_TITLE_FOUND)  # type: ignore
        if isinstance(current_title, list):
            current_title = current_title[0]
        return str(current_title)

    raise Exception("Unhandled filetype, path %s" % file)


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
        tags[MP3_ID3_ALBUM_TAG] = TALB(encoding=3, text=album)  # type: ignore

        current_title = GetTitle(file)
        if current_title:
            tags[MP3_ID3_TITLE_TAG] = TIT2(encoding=3, text=title_prefix + current_title)  # type: ignore
        else:
            tags[MP3_ID3_TITLE_TAG] = TIT2(encoding=3, text=title_prefix + os.path.basename(file))  # type: ignore

        tags.save(copy1)
    elif ext == ".m4a":
        m4a_file = MP4(str(copy1))  # type: ignore
        m4a_file[M4A_ALBUM_TAG] = album

        current_title = GetTitle(file)
        if current_title:
            if isinstance(current_title, list):
                current_title = current_title[0]
            m4a_file[M4A_TITLE_TAG] = title_prefix + current_title
        else:
            m4a_file[M4A_TITLE_TAG] = title_prefix + os.path.basename(file)
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
