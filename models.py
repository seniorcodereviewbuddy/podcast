"""SQLAlchemy models for podcast database persistence."""

import pathlib

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class ShowModel(Base):
    """SQLAlchemy model for podcast shows."""

    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folder_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    episodes: Mapped[list["EpisodeModel"]] = relationship(
        "EpisodeModel", back_populates="show", cascade="all, delete-orphan"
    )


class EpisodeModel(Base):
    """SQLAlchemy model for podcast episodes."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    show_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    episode_index: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    modification_time: Mapped[int] = mapped_column(Integer, nullable=False)

    show: Mapped["ShowModel"] = relationship("ShowModel", back_populates="episodes")

    __table_args__ = (UniqueConstraint("show_id", "path", name="uq_show_episode_path"),)


def get_engine(db_path: pathlib.Path) -> Engine:
    """Create a SQLAlchemy engine for the given database path.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        SQLAlchemy Engine instance.
    """
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(engine: Engine) -> None:
    """Initialize the database by creating all tables.

    Args:
        engine: SQLAlchemy Engine instance.
    """
    Base.metadata.create_all(engine)
