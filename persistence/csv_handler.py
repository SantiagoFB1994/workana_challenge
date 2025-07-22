import csv
import os
from typing import List
from datetime import datetime
from models.movie_model import Movie
from .base_persistence import BasePersistence

class CSVHandler(BasePersistence):
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = os.path.join(
            self.output_dir,
            f"imdb_movies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self._write_header = not os.path.exists(self.filename)

    def save_movie(self, movie: Movie) -> bool:
        """Save a movie to CSV"""
        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self._get_fieldnames())
                
                if self._write_header:
                    writer.writeheader()
                    self._write_header = False
                
                writer.writerow(self._movie_to_row(movie))
            return True
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            return False

    def save_bulk_movies(self, movies: List[Movie]) -> bool:
        """Save multiple movies to CSV"""
        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self._get_fieldnames())
                
                if self._write_header:
                    writer.writeheader()
                    self._write_header = False
                
                for movie in movies:
                    writer.writerow(self._movie_to_row(movie))
            return True
        except Exception as e:
            print(f"Error duting bulk save CSV: {str(e)}")
            return False

    def _movie_to_row(self, movie: Movie) -> dict:
        """Convert movie objent to dict for CSV"""
        row = movie.to_dict()
        row['actors'] = '|'.join(row['actors'])
        return row

    def _get_fieldnames(self) -> list:
        return ['title', 'year', 'rating', 'duration', 'metascore', 'actors']

    def get_movies_by_year(self, year: int) -> List[Movie]:
        """Not implemented for CSV"""
        raise NotImplementedError("CSV does not support searches by year for movies")

    def close(self):
        """No resources to be liberated"""
        pass