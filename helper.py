import os
import pathlib
import shutil
import tempfile

import audio_metadata
import conversions


def PrepareAudioAndMove(
    file: pathlib.Path, dest: pathlib.Path, title: str, album: str, speed: float
) -> None:
    print("Preparing Audio file %s" % file)

    with tempfile.TemporaryDirectory() as tmpdir:
        working_copy = pathlib.Path(tmpdir, file.name)
        conversions.create_adjusted_podcast_for_playback(file, working_copy, speed)

        audio_metadata.set_metadata(working_copy, title=title, album=album)

        # We don't copy the file to the destination until all the processing is
        # done to prevent the output folder from having incomplete files, or
        # files that are still being processed.
        print("Moving %s to %s" % (file, dest))
        shutil.move(working_copy, dest)
        os.remove(file)

    print("Done")
