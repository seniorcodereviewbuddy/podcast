import argparse
import os
import pathlib
import shutil
import sys
import typing

import helper


def _ArchiveFile(
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


def _UpdateFileandMoveOver(
    file_source: pathlib.Path,
    file_destination: pathlib.Path,
    title_prefix: str,
    speed: float,
    dry_run: bool,
) -> None:
    album = file_source.parent.name
    if dry_run:
        print("Dry run, would have moved %s to %s" % (file_source, file_destination))
        print("With album %s" % album)
    else:
        helper.PrepareAudioAndMove(
            file_source, file_destination, album, title_prefix, speed
        )


def main(args: typing.Optional[typing.List[str]]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-path", type=pathlib.Path, required=True)
    parser.add_argument("--file-destination", type=pathlib.Path, required=True)
    parser.add_argument("--archive-destination", type=pathlib.Path, default=None)
    parser.add_argument("--title-prefix", type=str, default="")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parsed_args = parser.parse_args(args)

    _ArchiveFile(
        parsed_args.file_path, parsed_args.archive_destination, parsed_args.dry_run
    )

    _UpdateFileandMoveOver(
        parsed_args.file_path,
        parsed_args.file_destination,
        parsed_args.title_prefix,
        parsed_args.speed,
        parsed_args.dry_run,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
