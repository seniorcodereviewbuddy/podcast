import datetime
import pathlib
import re
import subprocess
import typing

import audio_metadata
import podcast_episode
import user_input


class AndroidConnectionError(Exception):
    pass


def IsPhoneConnected(phone_name: str) -> bool:
    process = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    regex_for_attached_phone = phone_name + r"\s+device"
    return (
        process.returncode == 0
        and re.search(regex_for_attached_phone, process.stdout) is not None
    )


class AndroidPhone(object):
    def __init__(
        self,
        phone_name: str,
        podcast_directory: pathlib.Path,
        history_file: pathlib.Path,
    ):
        self.phone_name = phone_name
        self.podcast_directory = podcast_directory
        self.history_file = history_file

    def ConnectedToPhone(self, retry: bool = True) -> bool:
        while True:
            if IsPhoneConnected(self.phone_name):
                return True
            else:
                if retry and user_input.PromptYesOrNo(
                    "Didn't find phone (%s), try again?" % (self.phone_name)
                ):
                    continue
                else:
                    return False

    class CopyFilesToPhoneResults(typing.NamedTuple):
        copied: set[pathlib.Path]
        failed_to_copy: set[pathlib.Path]

    def CopyFilesToPhone(
        self, files: typing.List[pathlib.Path]
    ) -> CopyFilesToPhoneResults:
        date = datetime.datetime.now()
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(
                "Copying %d files to android at %s\n"
                % (len(files), date.strftime("%Y-%m-%d %H:%M:%S"))
            )
            for file in files:
                filename = file.name
                podcast = audio_metadata.GetAlbum(file)
                title = audio_metadata.GetTitle(file)
                modified_time = podcast_episode.ModifiedTime(file)
                readable_modified_time = datetime.datetime.fromtimestamp(
                    modified_time, tz=datetime.timezone.utc
                )
                f.write(
                    '  filename: "%s", podcast: "%s", title: "%s", download time: "%s"\n'
                    % (filename, podcast, title, readable_modified_time)
                )

        copied = set()
        failed_to_copy = set()
        for file in files:
            full_destination = pathlib.Path(self.podcast_directory, file.name)
            process_args: typing.List[str] = [
                "adb",
                "-s",
                self.phone_name,
                "push",
                str(file),
                full_destination.as_posix(),
            ]
            process = subprocess.run(process_args)
            if process.returncode == 0:
                print("Successfully copied %s to phone" % (file,))
                copied.add(file)
            else:
                failed_to_copy.add(file)

        if failed_to_copy:
            separated_files = "\n".join(map(str, failed_to_copy))
            print(
                f"Failed to copy {len(failed_to_copy)} files to phone.\n{separated_files}"
            )

        return AndroidPhone.CopyFilesToPhoneResults(copied, failed_to_copy)

    def GetPodcastEpisodesOnPhone(self) -> set[str]:
        process = subprocess.run(
            [
                "adb",
                "-s",
                self.phone_name,
                "shell",
                "ls",
                self.podcast_directory.as_posix(),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )

        if process.returncode != 0:
            raise AndroidConnectionError(
                "Failed to query podcast episodes on phone.\n"
                "Android output below:\n\n" + process.stdout
            )

        stripped_output = process.stdout.strip()

        # If the output is empty, there weren't any files.
        if not stripped_output:
            return set()

        return set(stripped_output.split("\n"))
