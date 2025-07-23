from abc import ABC, abstractmethod
from typing import Iterator

from models.movie_model import Movie


class BasePersistence(ABC):
    """
    persistence interface.
    """

    @abstractmethod
    def save_stream(self, movies: Iterator[Movie], batch_size: int = 1_000) -> int:
        """
        Persist an iterator of Movie objects in batches.
        Returns the total number of rows/objects written.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release any open resources (DB connections, file handles, etc.)."""
        pass