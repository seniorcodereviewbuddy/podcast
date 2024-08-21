import argparse
import os
import pathlib
import shutil
import sys
import typing

import helper


def _MoveFileOverImpl(
    podcast: str,
    file: pathlib.Path,
    destination: pathlib.Path,
    archive_folder: pathlib.Path,
    title_prefix: str,
    speed: float,
    dry_run: bool,
) -> None:
    # Make copies of important episodes.
    if archive_folder:
        if dry_run:
            print("Dry run, would have archived %s" % (file))
        else:
            podcast_archive_folder = pathlib.Path(archive_folder, podcast)
            os.makedirs(podcast_archive_folder, exist_ok=True)
            filename = file.name
            archive_destination = pathlib.Path(podcast_archive_folder, filename)
            print("Making copy of %s in archive (%s)" % (filename, archive_destination))
            shutil.copyfile(file, archive_destination)

    dest = pathlib.Path(destination, file.name)
    album = file.parent.name
    if dry_run:
        print("Dry run, would have moved %s to %s" % (file, dest))
        print("With album %s" % album)
    else:
        helper.PrepareAudioAndMove(file, dest, album, title_prefix, speed)


def main(args: typing.Optional[typing.List[str]]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--podcast-show-name", type=str, required=True)
    parser.add_argument("--file-path", type=pathlib.Path, required=True)
    parser.add_argument("--destination", type=pathlib.Path, required=True)
    parser.add_argument("--archive-folder", type=pathlib.Path, default=None)
    parser.add_argument("--title-prefix", type=str, default="")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parsed_args = parser.parse_args(args)

    _MoveFileOverImpl(
        parsed_args.podcast_show_name,
        parsed_args.file_path,
        parsed_args.destination,
        parsed_args.archive_folder,
        parsed_args.title_prefix,
        parsed_args.speed,
        parsed_args.dry_run,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
