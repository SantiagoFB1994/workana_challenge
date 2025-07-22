import os
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from typing import List
from models.movie_model import Movie, Actor
from .base_persistence import BasePersistence

class PostgresHandler(BasePersistence):
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish connection with PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'imdb_db'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            self._initialize_schema()
        except Exception as e:
            self.logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise

    def _initialize_schema(self):
        """Create tables if they don't exist"""
        create_tables = [
            """
            CREATE TABLE IF NOT EXISTS movies (
                movie_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                year INTEGER NOT NULL,
                rating NUMERIC(3,1) NOT NULL,
                duration INTEGER,
                metascore NUMERIC(3,1),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS actors (
                actor_id SERIAL PRIMARY KEY,
                movie_id INTEGER REFERENCES movies(movie_id),
                name VARCHAR(255) NOT NULL,
                CONSTRAINT unique_actor_movie UNIQUE (movie_id, name)
            )
            """
        ]
        
        with self.conn.cursor() as cur:
            for table in create_tables:
                cur.execute(table)
            self.conn.commit()

    def save_movie(self, movie: Movie) -> bool:
        """Save a movie in PostgreSQL"""
        try:
            with self.conn.cursor() as cur:
                # Insert Movie
                cur.execute(
                    """
                    INSERT INTO movies (title, year, rating, duration, metascore)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING movie_id
                    """,
                    (movie.title, movie.year, movie.rating, movie.duration, movie.metascore)
                )
                movie_id = cur.fetchone()[0]
                
                # Insert actors
                if movie.actors:
                    actors_data = [(movie_id, actor.name) for actor in movie.actors]
                    execute_batch(
                        cur,
                        "INSERT INTO actors (movie_id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        actors_data
                    )
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error inserting movie: {str(e)}")
            self.conn.rollback()
            return False

    def save_bulk_movies(self, movies: List[Movie]) -> bool:
        """Save multiple movies"""
        try:
            with self.conn.cursor() as cur:
                # Insert movies
                movies_data = [
                    (m.title, m.year, m.rating, m.duration, m.metascore)
                    for m in movies
                ]
                execute_batch(
                    cur,
                    """
                    INSERT INTO movies (title, year, rating, duration, metascore)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING movie_id
                    """,
                    movies_data
                )
                
                # We asume all movies have actors
                actors_data = []
                for movie_id, movie in zip(cur.fetchall(), movies):
                    if movie.actors:
                        actors_data.extend([(movie_id[0], actor.name) for actor in movie.actors])
                
                if actors_data:
                    execute_batch(
                        cur,
                        "INSERT INTO actors (movie_id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        actors_data
                    )
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error during bulk insert: {str(e)}")
            self.conn.rollback()
            return False

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