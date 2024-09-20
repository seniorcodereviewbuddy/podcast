import os
import pathlib
import shutil
import tempfile

import audio_metadata
import conversions


def _GenerateTitle(file: pathlib.Path, title_prefix: str) -> str:
    current_title = audio_metadata.GetTitle(file)
    if current_title:
        return title_prefix + current_title

    return title_prefix + os.path.basename(file)


def PrepareAudioAndMove(
    file: pathlib.Path, dest: pathlib.Path, album: str, title_prefix: str, speed: float
) -> None:
    print("Preparing Audio file %s" % file)

    with tempfile.TemporaryDirectory() as tmpdir:
        working_copy = pathlib.Path(tmpdir, file.name)
        conversions.CreateAdjustedPodcastForPlayback(file, working_copy, speed)

        new_title = _GenerateTitle(file, title_prefix)
        audio_metadata.SetMetadata(working_copy, title=new_title, album=album)

        # We don't copy the file to the destination until all the processing is
        # done to prevent the output folder from having incomplete files, or
        # files that are still being processed.
        print("Moving %s to %s" % (file, dest))
        shutil.move(working_copy, dest)
        os.remove(file)

    print("Done")
