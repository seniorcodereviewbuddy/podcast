import pathlib

from mutagen.id3 import ID3, ID3NoHeaderError  # type: ignore
from mutagen.mp4 import MP4

MP3_ID3_ALBUM_TAG = "TALB"
MP3_ID3_TITLE_TAG = "TIT2"
M4A_ALBUM_TAG = "\xa9alb"
M4A_TITLE_TAG = "\xa9nam"

NO_TITLE_FOUND = ""
NO_ALBUM_FOUND = "(No Album Name Found)"


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
