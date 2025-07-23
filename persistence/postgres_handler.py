import os
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Iterator

from models.movie_model import Movie, Actor
from .base_persistence import BasePersistence

import logging
logger = logging.getLogger(__name__)


class PostgresHandler(BasePersistence):
    """
    Streaming-only persistence that auto-creates the DB if missing
    and uses the IMDb ID as the primary key.
    """

    def __init__(self) -> None:
        self._ensure_database_exists()
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "imdb_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        self._initialize_schema()

    def _ensure_database_exists(self) -> None:
        """Create the target DB if it does not yet exist."""
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        db_name = os.getenv("POSTGRES_DB", "imdb_db")
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db_name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{db_name}"')
        cur.close()
        conn.close()

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
        # movies
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

        # actors
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

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")