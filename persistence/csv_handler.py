import csv
from pathlib import Path
from datetime import datetime
from typing import Iterator

from models.movie_model import Movie, Actor
from .base_persistence import BasePersistence


class CSVHandler(BasePersistence):
    """
    Stream movies to CSV, one per line.
    """

    def __init__(self, output_dir: str = "data") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filename = self.output_dir / f"imdb_movies_{datetime.now():%Y%m%d_%H%M%S}.csv"

    # ------------------------------------------------------------------
    # streaming save
    # ------------------------------------------------------------------
    def save_stream(self, movies: Iterator[Movie], batch_size: int = 1_000) -> int:
        """
        Persist an iterator of Movie objects to CSV.
        Returns the total number of rows written.
        """
        fieldnames = ["movie_id", "title", "year", "rating", "duration", "metascore", "actors"]
        written = 0

        with self.filename.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            buf: list[Movie] = []
            for movie in movies:
                buf.append(movie)
                if len(buf) >= batch_size:
                    writer.writerows(self._rows_from_buffer(buf))
                    written += len(buf)
                    buf.clear()

            if buf:  # tail
                writer.writerows(self._rows_from_buffer(buf))
                written += len(buf)

        return written

    def _rows_from_buffer(self, buf: list[Movie]) -> list[dict]:
        return [
            {
                "movie_id": m.movie_id,
                "title": m.title,
                "year": m.year,
                "rating": m.rating,
                "duration": m.duration,
                "metascore": m.metascore,
                "actors": "|".join(a.actor_id for a in m.actors),
            }
            for m in buf
        ]

    def get_movies_by_year(self, year: int) -> Iterator[Movie]:
        raise NotImplementedError("CSV does not support queries")

    def close(self) -> None:
        pass