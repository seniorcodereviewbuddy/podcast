import os

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "testdata")

# TODO: Should these all just be absolute paths, made with TEST_DATA_DIR above?
MP3_TEST_FILE = "mp3_test.mp3"
MP3_NO_TITLE_NO_ALBUM = "podcast_no_title_no_album.mp3"
MP3_DIFFERENT_TITLE_ENCODING = "podcast with greek encoding Ͱ.mp3"
MP3_WITH_EMOJI = "mp3_with_emoji_💡.mp3"
MP3_WITH_MULTIPLE_UTF8 = "mp3_Who’s_Kåre–Ó.mp3"
MP4_TEST_FILE = "mp4_test.mp4"
WEBM_TEST_FILE = "webm_test.webm"
M4A_TEST_FILE = "m4a_test.m4a"
M4A_NO_TITLE_NO_ALBUM = "podcast_no_title_no_album.m4a"
M4A_DIFFERENT_TITLE_ENCODING = "podcast with greek encoding Ͱ.m4a"

TEST_FILE_LENGTH_IN_SECONDS = 9
