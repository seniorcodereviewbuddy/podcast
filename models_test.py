"""Tests for SQLAlchemy models."""

import pathlib
import tempfile
import unittest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models


class TestModels(unittest.TestCase):
    """Test SQLAlchemy models."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.db_path = pathlib.Path(self._temp_dir.name) / "test.sqlite"
        self.engine = models.get_engine(self.db_path)
        models.init_db(self.engine)

    def tearDown(self) -> None:
        # Dispose of the engine to release all database connections
        # This is required on Windows to allow file deletion
        self.engine.dispose()
        self._temp_dir.cleanup()

    def test_create_show(self) -> None:
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name="test_podcast")
            session.add(show)
            session.commit()

            self.assertIsNotNone(show.id)
            self.assertEqual("test_podcast", show.folder_name)

    def test_create_episode(self) -> None:
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name="test_podcast")
            session.add(show)
            session.flush()

            episode_path = "/path/to/episode.mp3"
            episode_index = 1
            duration = 3600
            modification_time = 1234567890

            episode = models.EpisodeModel(
                show_id=show.id,
                path=episode_path,
                episode_index=episode_index,
                duration=duration,
                modification_time=modification_time,
            )
            session.add(episode)
            session.commit()

            self.assertIsNotNone(episode.id)
            self.assertEqual(show.id, episode.show_id)
            self.assertEqual(episode_path, episode.path)
            self.assertEqual(episode_index, episode.episode_index)
            self.assertEqual(duration, episode.duration)
            self.assertEqual(modification_time, episode.modification_time)

    def test_show_episode_relationship(self) -> None:
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name="test_podcast")
            session.add(show)
            session.flush()

            episode1 = models.EpisodeModel(
                show_id=show.id,
                path="/path/to/other_episode.mp3",
                episode_index=2,
                duration=399,
                modification_time=77,
            )
            episode2 = models.EpisodeModel(
                show_id=show.id,
                path="/path/to/last_episode.mp3",
                episode_index=3,
                duration=450,
                modification_time=88,
            )
            session.add_all([episode1, episode2])
            session.commit()

            self.assertEqual(set([episode1, episode2]), set(show.episodes))

    def test_cascade_delete(self) -> None:
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name="test_podcast")
            session.add(show)
            session.flush()

            episode = models.EpisodeModel(
                show_id=show.id,
                path="/path/to/episode.mp3",
                episode_index=5,
                duration=100,
                modification_time=66,
            )
            session.add(episode)
            session.commit()

            # Get the IDs before deletion
            show_id = show.id
            episode_id = episode.id

            # Delete the show
            session.delete(show)
            session.commit()

            # Verify both show and episode are gone
            self.assertIsNone(session.get(models.ShowModel, show_id))
            self.assertIsNone(session.get(models.EpisodeModel, episode_id))

    def test_unique_folder_name(self) -> None:
        with Session(self.engine) as session:
            show1 = models.ShowModel(folder_name="duplicate_name")
            session.add(show1)
            session.commit()

            show2 = models.ShowModel(folder_name="duplicate_name")
            session.add(show2)
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_unique_show_episode_path(self) -> None:
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name="test_podcast")
            session.add(show)
            session.flush()

            path = "/path/to/episode_seven.mp3"
            episode1 = models.EpisodeModel(
                show_id=show.id,
                path=path,
                episode_index=99,
                duration=50,
                modification_time=12,
            )
            session.add(episode1)
            session.commit()

            # Try to add another episode with the same path
            episode2 = models.EpisodeModel(
                show_id=show.id,
                path=path,
                episode_index=2,
                duration=1800,
                modification_time=1234567900,
            )
            session.add(episode2)
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_query_shows_presists(self) -> None:
        show1_name = "podcast_a"
        show2_name = "podcast_b"
        with Session(self.engine) as session:
            show1 = models.ShowModel(folder_name=show1_name)
            show2 = models.ShowModel(folder_name=show2_name)
            session.add_all([show1, show2])
            session.commit()

        with Session(self.engine) as session:
            shows = (
                session.query(models.ShowModel)
                .order_by(models.ShowModel.folder_name)
                .all()
            )
            self.assertEqual(2, len(shows))
            self.assertEqual(show1_name, shows[0].folder_name)
            self.assertEqual(show2_name, shows[1].folder_name)

    def test_query_show_by_folder_name(self) -> None:
        folder_name = "my_podcast"
        with Session(self.engine) as session:
            show = models.ShowModel(folder_name=folder_name)
            session.add(show)
            session.commit()

        with Session(self.engine) as session:
            found_show = (
                session.query(models.ShowModel)
                .filter_by(folder_name=folder_name)
                .first()
            )
            self.assertIsNotNone(found_show)
            assert found_show is not None  # for type narrowing
            self.assertEqual(folder_name, found_show.folder_name)

            # Query for non-existent show
            not_found = (
                session.query(models.ShowModel)
                .filter_by(folder_name="nonexistent")
                .first()
            )
            self.assertIsNone(not_found)


if __name__ == "__main__":
    unittest.main()
