import datetime
import pathlib
import typing

import archive
import full_podcast_episode
import podcast_episode
import podcast_preprocessing_base
import user_input

PRIORITY_RANGE = range(3)
P0, P1, P2 = PRIORITY_RANGE
PRIORITY_SKIP = -1

DEFAULT_SPEED = 1.55


class PodcastShow(object):
    def __init__(
        self,
        podcast_folder: pathlib.Path,
        priority: int,
        archive: archive.Archive = archive.Archive.NO,
        speed: float = DEFAULT_SPEED,
        preprocess: typing.Optional[
            podcast_preprocessing_base.PreProcess_TypeAlias
        ] = None,
    ):
        assert podcast_folder.is_absolute(), "podcast_folder must be an absolute path"
        self.podcast_folder = podcast_folder
        self.podcast_name = podcast_folder.name
        self.priority = priority
        self.archive = archive
        self.speed = speed
        self.preprocess = preprocess
        self.episodes: typing.List[podcast_episode.PodcastEpisode] = []
        self.next_index: typing.Optional[int] = None

    def __str__(self) -> str:
        return str(self.podcast_folder)

    def __cmp__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder < other.podcast_folder

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return False
        return self.podcast_folder == other.podcast_folder

    def __ne__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder != other.podcast_folder

    def __lt__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder < other.podcast_folder

    def __le__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder <= other.podcast_folder

    def __gt__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder > other.podcast_folder

    def __ge__(self, other: typing.Any) -> bool:
        if not isinstance(other, PodcastShow):
            return NotImplemented
        return self.podcast_folder >= other.podcast_folder

    def load(self, f: typing.TextIO) -> typing.Optional["PodcastShow"]:
        loading_path = f.readline().strip()
        if loading_path != self.podcast_folder.name:
            print(
                "Attempted to load podcast %s into %s"
                % (loading_path, self.podcast_folder.name)
            )
            return None

        next_index = f.readline().strip()
        if next_index == "None":
            self.next_index = None
        else:
            self.next_index = int(next_index)
        num_episodes = int(f.readline())
        self.episodes = [
            podcast_episode.PodcastEpisode.load(f) for x in range(num_episodes)
        ]

        return self

    def save(self, f: typing.TextIO) -> None:
        f.write(str(self.podcast_folder.name) + "\n")
        f.write(str(self.next_index) + "\n")
        f.write(str(len(self.episodes)) + "\n")
        for episode in self.episodes:
            episode.save(f)

    def scan_for_updates(self, allow_prompt: bool = True) -> typing.List[pathlib.Path]:
        print("Scanning for Updates for %s" % (self.podcast_folder))
        if self.preprocess:
            print("Executing preprocess for %s" % (self.podcast_folder))
            self.preprocess(
                self.podcast_folder,
                # TODO: this isn't getting tested, becuase this is asking for user inputs and it isn't being mocked out.
                podcast_preprocessing_base.prompt_for_delete,
            )

        files_present = frozenset(f.absolute() for f in self.podcast_folder.iterdir())
        # Remove the files that are no longer present.
        self.episodes = [
            episode for episode in self.episodes if episode.path in files_present
        ]

        known_files = frozenset(episode.path for episode in self.episodes)

        new_episodes = []
        for f in files_present.difference(known_files):
            full_path = self.podcast_folder.joinpath(f).absolute()
            if not podcast_episode.is_podcast_file(full_path):
                continue

            if "(2)" in str(f):
                raise Exception("Doubled file? %s" % (full_path))
            new_episodes.append(
                (
                    full_path,
                    podcast_episode.modified_time(full_path),
                )
            )

        new_episodes.sort(key=lambda x: x[1])

        for path, _time in new_episodes:
            self.add_episode(path, allow_prompt=allow_prompt)

        return [x[0] for x in new_episodes]

    def get_episode(
        self, path: pathlib.Path
    ) -> typing.Optional[full_podcast_episode.FullPodcastEpisode]:
        for episode in self.episodes:
            if episode.path == path:
                return self._episode_as_full_podcast_episode(episode)
        return None

    def add_episode(self, path: pathlib.Path, allow_prompt: bool = True) -> None:
        if self.next_index is None:
            if allow_prompt and not user_input.prompt_yes_or_no(
                "Initialize next_index to 1 for %s" % (self.podcast_folder)
            ):
                raise Exception()
            else:
                self.next_index = 1

        self.episodes.append(podcast_episode.PodcastEpisode.new(path, self.next_index))
        self.next_index += 1

    def _episodes_without_ignores(
        self, files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None
    ) -> list[podcast_episode.PodcastEpisode]:
        if not files_to_ignore:
            return self.episodes
        return [x for x in self.episodes if x.path not in files_to_ignore]

    def _episode_as_full_podcast_episode(
        self, episode: podcast_episode.PodcastEpisode
    ) -> full_podcast_episode.FullPodcastEpisode:
        return full_podcast_episode.FullPodcastEpisode(
            episode.index,
            episode.path,
            self.podcast_name,
            speed=self.speed,
            archive=self.archive,
            modification_time=datetime.datetime.fromtimestamp(
                episode.modification_time
            ),
            duration=datetime.timedelta(seconds=episode.duration),
        )

    def first_episode(
        self,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.Optional[full_podcast_episode.FullPodcastEpisode]:
        possible_episodes = self._episodes_without_ignores(files_to_ignore)
        if not possible_episodes:
            return None

        first_podcast = possible_episodes[0]
        for episode in possible_episodes[1:]:
            if first_podcast.modification_time > episode.modification_time:
                first_podcast = episode

        return self._episode_as_full_podcast_episode(first_podcast)

    def remaining_episodes(
        self,
        files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None,
    ) -> typing.List[full_podcast_episode.FullPodcastEpisode]:
        return [
            self._episode_as_full_podcast_episode(x)
            for x in self._episodes_without_ignores(files_to_ignore)
        ]

    def remaining_time(
        self, files_to_ignore: typing.Optional[typing.List[pathlib.Path]] = None
    ) -> int:
        duration = 0
        for episode in self._episodes_without_ignores(files_to_ignore):
            duration += episode.duration
        return duration
