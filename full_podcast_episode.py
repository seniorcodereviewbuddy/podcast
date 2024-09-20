import datetime
import pathlib
import typing

import archive
import time_helper


class FullPodcastEpisode(object):
    def __init__(
        self,
        index: int,
        path: pathlib.Path,
        podcast_show_name: str,
        speed: float,
        archive: archive.Archive,
        modification_time: datetime.datetime,
        duration: datetime.timedelta,
    ):
        self.index = index
        self.path = path
        self.podcast_show_name = podcast_show_name
        self.speed = speed
        self.archive = archive
        self.modification_time = modification_time
        self.duration = duration

    def __str__(self) -> str:
        return (
            "FullPodcastEpisode(%s:(%s) with index %d from %s with speed %0.2f, archive %s and modification_time %s)"
            % (
                self.path,
                time_helper.SecondsToString(self.duration.seconds),
                self.index,
                self.podcast_show_name,
                self.speed,
                self.archive,
                self.modification_time,
            )
        )

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, FullPodcastEpisode):
            return False
        return (
            (self.index == other.index)
            and (self.path == other.path)
            and (self.podcast_show_name == other.podcast_show_name)
            and (self.speed == other.speed)
            and (self.archive == other.archive)
            and (self.modification_time == other.modification_time)
            and (self.duration == other.duration)
        )
