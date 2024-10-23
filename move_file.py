import argparse
import os
import pathlib
import shutil
import sys
import typing

import helper


def _archive_file(
    file_source: pathlib.Path, archive_destination: pathlib.Path, dry_run: bool
) -> None:
    if not archive_destination:
        return

    if dry_run:
        print("Dry run, would have archived %s" % (file_source))
    else:
        os.makedirs(archive_destination.parent, exist_ok=True)
        print(
            "Making copy of %s in archive (%s)"
            % (file_source.name, archive_destination)
        )
        shutil.copyfile(file_source, archive_destination)


def _update_file_and_move_over(
    file_source: pathlib.Path,
    file_destination: pathlib.Path,
    title: str,
    album: str,
    speed: float,
    dry_run: bool,
) -> None:
    if dry_run:
        print("Dry run, would have moved %s to %s" % (file_source, file_destination))
        print("With album %s" % album)
    else:
        helper.prepare_audio_and_move(
            file_source, file_destination, title, album, speed
        )


def main(args: typing.Optional[typing.List[str]]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-path", type=pathlib.Path, required=True)
    parser.add_argument("--file-destination", type=pathlib.Path, required=True)
    parser.add_argument("--archive-destination", type=pathlib.Path, default=None)
    parser.add_argument("--album", type=str, required=True)
    parser.add_argument("--title", type=str, required=True)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parsed_args = parser.parse_args(args)

    _archive_file(
        parsed_args.file_path, parsed_args.archive_destination, parsed_args.dry_run
    )

    _update_file_and_move_over(
        parsed_args.file_path,
        parsed_args.file_destination,
        parsed_args.title,
        parsed_args.album,
        parsed_args.speed,
        parsed_args.dry_run,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
