# -*- coding: utf-8 -*-

import concurrent.futures
import datetime
import os
import pathlib
import queue
import subprocess
import sys
import typing

import android_phone
import archive
import audio_metadata
import backup
import command_args
import full_podcast_episode
import podcast_database
import podcast_show
import settings
import user_input

ROOT_DIR = os.path.dirname(__file__)


class UnknownPodcastFoldersError(Exception):
    pass


def find_unknown_folders(
    podcast_folder: pathlib.Path, expected_folders: typing.List[str]
) -> typing.List[pathlib.Path]:
    unknown_folders = []
    for item in podcast_folder.iterdir():
        if item.is_file():
            continue

        if item.name not in expected_folders:
            unknown_folders.append(pathlib.Path(item.name))

    return unknown_folders


def validate_podcast_folders(
    podcast_folder: pathlib.Path, podcast_shows: typing.List[podcast_show.PodcastShow]
) -> None:
    expected_folders = [x.podcast_folder.name for x in podcast_shows]
    unknown_folders = find_unknown_folders(podcast_folder, expected_folders)

    if unknown_folders:
        raise UnknownPodcastFoldersError(
            f"\n{len(unknown_folders)} unknown folders, please update user settings to know what to do.\n"
            "Unknown folders:\n" + "\n".join([str(x) for x in unknown_folders])
        )


def _generate_title(file: pathlib.Path, title_prefix: str) -> str:
    current_title = audio_metadata.get_title(file)
    if current_title:
        return title_prefix + current_title

    return title_prefix + os.path.basename(file)


def _work(q: queue.Queue[str], args: typing.List[str]) -> None:
    script = os.path.join(ROOT_DIR, "move_file.py")
    args = [sys.executable, script] + args
    work_env = dict(os.environ)
    work_env["PYTHONIOENCODING"] = "utf-8"

    with subprocess.Popen(
        args,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        env=work_env,
    ) as process:
        if process.stdout is None:
            raise Exception("stdout is missing")
        for stdout_line in iter(process.stdout.readline, ""):
            stdout_line = stdout_line.strip()
            if stdout_line:
                q.put(stdout_line)


def process_and_move_files_over(
    files: typing.List[full_podcast_episode.FullPodcastEpisode],
    destination: pathlib.Path,
    archive_folder: pathlib.Path,
    dry_run: bool,
) -> None:
    # Limit the number of workers to less than the number of CPUs so I can still use the computer while converting.
    cpus_available = os.cpu_count() or 1
    max_workers = max(cpus_available - 2, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file in files:
            q: queue.Queue[str] = queue.Queue()

            title_prefix = "%04d_" % (file.index) if file.index else ""
            title = _generate_title(file.path, title_prefix)

            album = file.path.parent.name

            file_destination = pathlib.Path(destination, file.path.name)
            args = [
                "--file-path=%s" % (file.path),
                "--file-destination=%s" % file_destination,
                "--title=%s" % (title),
                "--album=%s" % (album),
                "--speed=%f" % (file.speed),
            ]
            if file.archive == archive.Archive.YES:
                archive_destination = archive_folder.joinpath(
                    file.podcast_show_name, file.path.name
                )
                args += ["--archive-destination=%s" % (archive_destination)]
            if dry_run:
                args += ["--dry-run"]
            futures.append((file, q, executor.submit(_work, q, args)))
        for file, q, future in futures:
            while not future.done():
                while True:
                    try:
                        output = q.get_nowait()
                        print(output)
                    except queue.Empty:
                        break
            if future.exception():
                print("Hit an exception:\n\t%s" % (future.exception()))
            else:
                while not q.empty():
                    print(q.get())

        # Check to verify the file has been deleted if this wasn't a dry run.
        if not dry_run:
            all_files_delete = True
            for file in files:
                if file.path.exists():
                    all_files_delete = False
                    print(
                        "%s wasn't deleted, check if it was converted." % (file.path,)
                    )
            if not all_files_delete:
                raise Exception("Failed to delete all files")


def get_batch_of_podcast_files(
    database: podcast_database.PodcastDatabase,
    duration_limit: datetime.timedelta,
    num_oldest_files_to_get: int = 0,
    required_files: typing.Optional[
        typing.Dict[pathlib.Path, typing.List[pathlib.Path]]
    ] = None,
    user_prompt: user_input.PromptYesOrNo_Alias = user_input.prompt_yes_or_no,
) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
    """
    GetBatchofPodcastFiles returns |duration_limit| time of podcasts.
    It starts by adding the |num_oldest_files_to_get| oldest files, and then all
    the |required_files|, even if that exceeds the given duration duration.
    If we haven't passed the requested duration, it will add podcasts in
    priority order until it is just over the duration limit.
    """
    files = database.get_oldest_files(num_oldest_files_to_get)

    required_files = required_files if required_files else {}
    files.extend(
        database.get_specified_files(
            required_files, files_to_ignore=[x.path for x in files]
        )
    )

    time_so_far = sum((x.duration for x in files), datetime.timedelta())
    priority_duration = duration_limit - time_so_far

    files.extend(
        database.get_podcast_episodes_by_priority(
            priority_duration, user_prompt, files_to_ignore=[x.path for x in files]
        )
    )

    return files


def get_podcast_episodes_summary(
    podcast_episodes: typing.List[full_podcast_episode.FullPodcastEpisode],
) -> str:
    if not podcast_episodes:
        return "No Potential Files"

    total_duration = sum((x.duration for x in podcast_episodes), datetime.timedelta())

    summary_lines = ["Potential Files:"]

    summary_lines += [
        f"{x.podcast_show_name}: {x.path.name} {x.duration}" for x in podcast_episodes
    ]
    summary_lines += [
        f"{len(podcast_episodes)} files in total, duration of {total_duration}"
    ]

    return "\n".join(summary_lines)


# TODO: Test this function someday
def main(
    args: typing.Optional[typing.List[str]], user_settings: settings.Settings
) -> None:
    parsed_args = command_args.parse_args(args)

    validate_podcast_folders(user_settings.podcast_folder, user_settings.podcasts)

    database = podcast_database.PodcastDatabase(
        user_settings.podcast_folder,
        user_settings.podcasts,
        parsed_args.verbose,
    )
    database.load(user_settings.podcast_database)

    database.update_podcasts()
    if parsed_args.dry_run:
        print("Skipping database update for dry run")
    else:
        database.save(user_settings.podcast_database)
        database.update_remaining_time(user_settings.podcast_history)
        database.log_stats(user_settings.podcast_stats)

    phone = android_phone.AndroidPhone(
        user_settings.android_phone_id,
        user_settings.podcast_directory_on_phone,
        user_settings.android_history,
    )
    # We want to try connecting to the phone before continuing as we don't want
    # to start processing the files and only later realize the phone isn't connected.
    phone.connect_to_phone()

    time_in_hours = datetime.timedelta(
        hours=user_settings.time_of_podcasts_to_add_in_hours
    )
    unprocessed_files = get_batch_of_podcast_files(
        database,
        time_in_hours,
        user_settings.num_oldest_episodes_to_add,
        user_settings.specified_files,
    )

    # Print a summary of the collected files and see if the user wants to
    # continue.
    print(get_podcast_episodes_summary(unprocessed_files))
    result = user_input.prompt_yes_or_no(
        "Process files and move to '%s' before putting on phone: "
        % user_settings.processed_file_boarding_zone_folder
    )

    if not result:
        print("Done.")
        return

    # TODO: Raise an exception if it exists and is a file?
    if not user_settings.processed_file_boarding_zone_folder.exists():
        os.mkdir(user_settings.processed_file_boarding_zone_folder)

    process_and_move_files_over(
        unprocessed_files,
        user_settings.processed_file_boarding_zone_folder,
        user_settings.archive_folder,
        parsed_args.dry_run,
    )

    if phone.connect_to_phone():
        processed_files = [
            pathlib.Path(
                user_settings.processed_file_boarding_zone_folder,
                podcast.path.name,
            )
            for podcast in unprocessed_files
        ]
        copy_results = phone.copy_files_to_phone(processed_files)

        local_backup = backup.Local(
            user_settings.backup_folder, user_settings.backup_history
        )

        if copy_results.failed_to_copy:
            print(
                f"WARNING: NOT ADDING {len(copy_results.failed_to_copy)} FILES TO BACKUP"
            )
            print(
                f"THESE FILES WEREN'T COPIED OVER SUCCESSFULLY AND ARE BEING LEFT ALONE IN {user_settings.processed_file_boarding_zone_folder}"
            )
        local_backup.move_files_to_backup(copy_results.copied)

        try:
            files_on_phone = phone.get_podcast_episodes_on_phone()
        except android_phone.AndroidConnectionError as e:
            print(e)
            print("Failed to see android phone, skipping folder back sync")
        else:
            local_backup.remove_unneeded_backup_files(files_on_phone)


if __name__ == "__main__":
    if sys.version_info < (3, 0):
        raise Exception("Requires Python 3")
    main(sys.argv[1:], settings.DefaultSettings())
