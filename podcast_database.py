import datetime
import pathlib
import random
import typing

import full_podcast_episode
import podcast_show
import time_helper
import user_input


class DatabaseLoadingError(Exception):
    pass


class PodcastShowPathError(Exception):
    pass


class PodcastEpisodePathError(Exception):
    pass


class podcast_database(object):
    def __init__(
        self,
        root: pathlib.Path,
        podcast_shows: typing.List[podcast_show.PodcastShow],
        verbose: bool,
    ):
        self.root = root
        self.podcast_shows = podcast_shows
        self.verbose = verbose

        # Ensure there are no duplicates.
        duplicates = []
        podcast_show_set = set()
        for x in podcast_shows:
            if x.podcast_folder in podcast_show_set:
                duplicates.append(x.podcast_folder)
            else:
                podcast_show_set.add(x.podcast_folder)

        if duplicates:
            raise Exception("Found duplicate paths: %s" % (duplicates))

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def load(
        self,
        path: pathlib.Path,
        user_input_function: typing.Callable[[str], str] = input,
    ) -> int:
        if not path.is_file():
            self._log("%s isn't a file, not loading a database" % (path))
            return 0

        loaded = 0
        with open(path, "r", encoding="utf-8") as f:
            num_podcasts = int(f.readline())
            self._log("Loading %d podcasts from %s" % (num_podcasts, path))
            for p in range(num_podcasts):
                podcast_folder = pathlib.Path(f.readline().strip())
                match_found = False
                for possible_podcast in self.podcast_shows:
                    if possible_podcast.podcast_folder == podcast_folder:
                        possible_podcast.load(f)
                        loaded += 1
                        match_found = True
                        break

                if not match_found:
                    remove_keyword = "REMOVE"
                    no_match_found_message = (
                        "No match found for %s. Please type %s if you want to remove this podcast:\n"
                        % (podcast_folder, remove_keyword)
                    )
                    no_match_found_user_response = user_input_function(
                        no_match_found_message
                    )
                    if no_match_found_user_response == remove_keyword:
                        # Since this removed podcast is still in the database file, we load it to parse it from the file, but
                        # then don't save this data anywhere since we no longer want it.
                        podcast_show.PodcastShow(
                            podcast_folder, podcast_show.PRIORITY_SKIP
                        ).load(f)
                    else:
                        raise DatabaseLoadingError(
                            "Failed to load %s." % (podcast_folder)
                        )
        return loaded

    def save(self, path: pathlib.Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(len(self.podcast_shows)) + "\n")
            for pod in sorted(self.podcast_shows):
                f.write(str(pod.podcast_folder) + "\n")
                pod.save(f)

    def update_podcasts(self, allow_prompt: bool = True) -> None:
        # Drop all missing podcast shows.
        self.podcast_shows = [
            podcast_show
            for podcast_show in self.podcast_shows
            if pathlib.Path(self.root, podcast_show.podcast_folder).is_dir()
        ]

        for pod in self.podcast_shows:
            if pod.priority == podcast_show.PRIORITY_SKIP:
                print("Skipping %s" % (pod))
                continue
            pod.scan_for_updates(self.root, allow_prompt=allow_prompt)

    def _GetAllPodcastShowsSortedByPriority(
        self,
    ) -> typing.List[podcast_show.PodcastShow]:
        priority: typing.Dict[int, typing.List[podcast_show.PodcastShow]] = {}
        for cast in self.podcast_shows:
            if cast.priority not in priority:
                priority[cast.priority] = []
            priority[cast.priority].append(cast)

        podcast_shows = []
        for p in podcast_show.PRIORITY_RANGE:
            podcast_shows.extend(sorted(priority.get(p, [])))
        return podcast_shows

    def update_remaining_time(
        self,
        path: pathlib.Path,
        date: typing.Optional[datetime.datetime] = None,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> None:
        date = datetime.datetime.now() if date is None else date
        podcast_shows = self._GetAllPodcastShowsSortedByPriority()
        num_remaining_episodes = sum(
            len(x.remaining_episodes(files_to_ignore)) for x in podcast_shows
        )
        remaining_duration = sum(
            x.remaining_time(files_to_ignore) for x in podcast_shows
        )

        with open(path, "a", encoding="utf-8") as f:
            f.write(
                "As of %s, the podcast episode backlog is %d episodes with total duration %s\n"
                % (
                    date.strftime("%Y-%m-%d %H:%M:%S"),
                    num_remaining_episodes,
                    time_helper.seconds_to_string(remaining_duration),
                )
            )

    def log_stats(
        self,
        path: pathlib.Path,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> None:
        podcast_shows = self._GetAllPodcastShowsSortedByPriority()

        with open(path, "w", encoding="utf-8") as f:
            for x in podcast_shows:
                remaining_episodes = x.remaining_episodes(files_to_ignore)
                if not remaining_episodes:
                    continue
                total_duration = x.remaining_time(files_to_ignore)
                average_duration = total_duration / len(remaining_episodes)
                f.write(
                    "%s: total duration of %s, %d episodes, %s long on average\n"
                    % (
                        x.podcast_folder,
                        time_helper.seconds_to_string(total_duration),
                        len(remaining_episodes),
                        time_helper.seconds_to_string(average_duration),
                    )
                )

    def _GetFirstEpisodeForEachPodcast(
        self,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        first_episodes = [x.first_episode(files_to_ignore) for x in self.podcast_shows]
        return [x for x in first_episodes if x]

    # TODO: Can I merge this with above by defaulting to all priorities or something like that?
    def _GetFirstEpisodeForEachPodcastOfPriority(
        self,
        priority: int,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        first_episodes = [
            x.first_episode(files_to_ignore)
            for x in self.podcast_shows
            if x.priority == priority
        ]
        return [x for x in first_episodes if x]

    def get_podcast_episodes_by_priority(
        self,
        duration_limit: datetime.timedelta,
        user_prompt: user_input.PromptYesOrNo_Alias = user_input.PromptYesOrNo,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        random.seed(None)
        current_duration = datetime.timedelta()
        weekly_episodes: typing.List[full_podcast_episode.FullPodcastEpisode] = []
        current_priority = min(podcast_show.PRIORITY_RANGE)
        files_to_ignore = files_to_ignore or []

        while current_duration < duration_limit:
            next_podcasts = self._GetFirstEpisodeForEachPodcastOfPriority(
                current_priority,
                files_to_ignore=[x.path for x in weekly_episodes] + files_to_ignore,
            )
            if next_podcasts:
                picked_podcast = random.choice(next_podcasts)
                weekly_episodes.append(picked_podcast)
                current_duration += picked_podcast.duration
            else:
                current_priority += 1
                if current_priority not in podcast_show.PRIORITY_RANGE:
                    # No more priorities to examine, we are done.
                    break
                else:
                    # If there are no more podcasts for this priority, ask if we are done or should move to the next priority.
                    result = user_prompt(
                        "\nFinished adding podcasts with priority %d\nCurrently %d episodes with length %s\nContinue to priority %d?"
                        % (
                            current_priority - 1,
                            len(weekly_episodes),
                            current_duration,
                            current_priority,
                        )
                    )
                    if not result:
                        break

        return weekly_episodes

    def get_oldest_files(
        self,
        num_files_to_get: int,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        oldest_episodes: typing.List[full_podcast_episode.FullPodcastEpisode] = []
        files_to_ignore = [] if files_to_ignore is None else files_to_ignore
        for _ in range(num_files_to_get):
            oldest_episodes_left = self._GetFirstEpisodeForEachPodcast(
                files_to_ignore=files_to_ignore + [x.path for x in oldest_episodes]
            )
            if not oldest_episodes_left:
                print(
                    "Only found %d old episodes, when %d were requested."
                    % (len(oldest_episodes), num_files_to_get)
                )
                break

            current_oldest = oldest_episodes_left[0]
            for episode in oldest_episodes_left[1:]:
                if current_oldest.modification_time > episode.modification_time:
                    current_oldest = episode

            oldest_episodes.append(current_oldest)

        return oldest_episodes

    def get_specified_files(
        self,
        specified_files: typing.Dict[pathlib.Path, typing.List[pathlib.Path]],
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        files_to_ignore = [] if files_to_ignore is None else files_to_ignore

        files_to_get: typing.List[full_podcast_episode.FullPodcastEpisode] = []

        show_map = dict([(x.podcast_name, x) for x in self.podcast_shows])

        for show_name, episode_paths in specified_files.items():
            show = show_map.get(show_name.name)
            if not show:
                raise PodcastShowPathError(
                    "Given show path, %s, doesn't exist" % show_name.name
                )

            for episode_path in episode_paths:
                full_potential_path = pathlib.Path(
                    self.root, show.podcast_folder, episode_path
                )
                matching_episode = show.get_episode(full_potential_path)
                if not matching_episode:
                    raise PodcastEpisodePathError(
                        "File, %s, doesn't exists for show %s"
                        % (episode_path, show_name.name)
                    )

                if matching_episode.path not in files_to_ignore:
                    files_to_get.append(matching_episode)

        return files_to_get
