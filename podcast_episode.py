import pathlib
import stat
import typing

import pyglet

import models
import time_helper


class PodcastEpisodeLoadingError(Exception):
    pass


# TODO: This is only called in PodcastShow, so maybe it should live there. It doesn't seem to really be episode specific.
def is_podcast_file(file: pathlib.Path) -> bool:
    ext = file.suffix.lower()
    # Ignore file with extensions we don't care about.
    if ext in (".db", ".jpg", ".jpeg", ".partial", ".png"):
        return False

    # Raise exceptions for unknown file types.
    if ext not in (".mp3", ".m4a"):
        raise Exception(
            "Unknown file type, %s, for file path %s.\nPlease update script to handle"
            % (ext, file)
        )

    return file.is_file()


def modified_time(file: pathlib.Path) -> int:
    return int(file.stat()[stat.ST_MTIME])


class PodcastEpisode(object):
    def __init__(
        self, path: pathlib.Path, index: int, duration: int, modification_time: int
    ) -> None:
        self.path = path
        self.index = index
        self.duration = duration
        self.modification_time = modification_time

    def __str__(self) -> str:
        return "%s:(%s)" % (self.path, time_helper.seconds_to_string(self.duration))

    @classmethod
    def new(cls, path: pathlib.Path, index: int) -> "PodcastEpisode":
        try:
            source = pyglet.media.load(str(path))
        except EOFError as e:
            print("Encountered an EOFError trying to load %s" % (path))
            raise e
        if source.duration is None:
            raise Exception("File with unknown duration, %s", path)
        duration = int(source.duration)
        modification_time = modified_time(path)

        return PodcastEpisode(path, index, duration, modification_time)

    @classmethod
    def load(cls, f: typing.TextIO) -> "PodcastEpisode":
        path = pathlib.Path(f.readline().strip())
        try:
            index = int(f.readline().strip())
        except ValueError as e:
            raise PodcastEpisodeLoadingError(
                "Failed to load index for episode, %s" % (e)
            )

        try:
            duration = int(f.readline())
        except ValueError as e:
            raise PodcastEpisodeLoadingError(
                "Failed to load duration for episode, %s" % (e)
            )

        try:
            modification_time = int(f.readline())
        except ValueError as e:
            raise PodcastEpisodeLoadingError(
                "Failed to load modification_time for episode, %s" % (e)
            )

        return PodcastEpisode(path, index, duration, modification_time)

    def save(self, f: typing.TextIO) -> None:
        f.write(str(self.path) + "\n")
        f.write(str(self.index) + "\n")
        f.write(str(self.duration) + "\n")
        f.write(str(self.modification_time) + "\n")

    def to_model(self, show_id: int) -> models.EpisodeModel:
        """Convert this episode to a SQLAlchemy model for database persistence.

        Args:
            show_id: The database ID of the parent show.

        Returns:
            An EpisodeModel instance ready to be added to a session.
        """
        return models.EpisodeModel(
            show_id=show_id,
            path=str(self.path),
            episode_index=self.index,
            duration=self.duration,
            modification_time=self.modification_time,
        )

    @classmethod
    def from_model(cls, episode_model: models.EpisodeModel) -> "PodcastEpisode":
        """Create a PodcastEpisode from a SQLAlchemy model.

        Args:
            episode_model: The EpisodeModel from the database.

        Returns:
            A PodcastEpisode instance.
        """
        return cls(
            path=pathlib.Path(episode_model.path),
            index=episode_model.episode_index,
            duration=episode_model.duration,
            modification_time=episode_model.modification_time,
        )
