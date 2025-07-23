import os
import logging
import psycopg2
from psycopg2.extras import execute_batch
from typing import Iterator

from models.movie_model import Movie, Actor, List
from .base_persistence import BasePersistence

logger = logging.getLogger(__name__)


class PostgresHandler(BasePersistence):
    """
    Streaming-only persistence that uses the **IMDb ID** as the primary key.
    """

    def __init__(self) -> None:
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "imdb_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    movie_id   TEXT PRIMARY KEY,
                    title      VARCHAR(255) NOT NULL,
                    year       INTEGER      NOT NULL,
                    rating     NUMERIC(3,1) NOT NULL,
                    duration   INTEGER,
                    metascore  NUMERIC(4,1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS actors (
                    movie_id  TEXT REFERENCES movies(movie_id) ON DELETE CASCADE,
                    actor_id  TEXT NOT NULL,
                    name      VARCHAR(255) NOT NULL,
                    PRIMARY KEY (movie_id, actor_id)
                )
                """
            )
        self.conn.commit()

    def save_stream(self, movies: Iterator[Movie], batch_size: int = 1_000) -> int:
        cur = self.conn.cursor()
        buf: list[Movie] = []
        saved = 0

        try:
            for movie in movies:
                buf.append(movie)
                if len(buf) >= batch_size:
                    self._flush_batch(cur, buf)
                    saved += len(buf)
                    buf.clear()

            if buf:
                self._flush_batch(cur, buf)
                saved += len(buf)

            return saved
        finally:
            cur.close()

    def _flush_batch(self, cur, buf: list[Movie]) -> None:
        # 1. movies
        movie_rows = [(m.movie_id, m.title, m.year, m.rating, m.duration, m.metascore) for m in buf]
        execute_batch(
            cur,
            """
            INSERT INTO movies (movie_id, title, year, rating, duration, metascore)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (movie_id) DO NOTHING
            """,
            movie_rows,
        )

        # 2. actors
        actor_rows = [
            (m.movie_id, a.actor_id, a.name)
            for m in buf
            for a in (m.actors or [])
        ]
        if actor_rows:
            execute_batch(
                cur,
                """
                INSERT INTO actors (movie_id, actor_id, name)
                VALUES (%s, %s, %s)
                ON CONFLICT (movie_id, actor_id) DO NOTHING
                """,
                actor_rows,
            )
        self.conn.commit()


    def get_movies_by_year(self, year: int) -> List[Movie]:
        """Fetch movies by year"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT m.movie_id, m.title, m.year, m.rating, m.duration, m.metascore,
                           array_agg(a.name) as actors
                    FROM movies m
                    LEFT JOIN actors a ON m.movie_id = a.movie_id
                    WHERE m.year = %s
                    GROUP BY m.movie_id
                    """,
                    (year,)
                )
                
                movies = []
                for row in cur.fetchall():
                    movie = Movie(
                        movie_id=row[0],
                        title=row[1],
                        year=row[2],
                        rating=row[3],
                        duration=row[4],
                        metascore=row[5],
                        actors=[Actor(name=name) for name in (row[6] if row[6] else [])]
                    )
                    movies.append(movie)
                
                return movies
                
        except Exception as e:
            self.logger.error(f"Error getting movies: {str(e)}")
            return []

    def close(self):
        """Close connection with PostgreSQL"""
        if self.conn:
            self.conn.close()
            self.logger.info("PostgreSQL connection closed")