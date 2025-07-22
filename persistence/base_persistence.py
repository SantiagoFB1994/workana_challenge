from abc import ABC, abstractmethod
from typing import List
from models.movie_model import Movie

class BasePersistence(ABC):
    @abstractmethod
    def save_movie(self, movie: Movie) -> bool:
        """Save movie into storage"""
        pass
    
    @abstractmethod
    def save_bulk_movies(self, movies: List[Movie]) -> bool:
        """Save multiple movies to storage"""
        pass
    
    @abstractmethod
    def get_movies_by_year(self, year: int) -> List[Movie]:
        """Fetches movies by year"""
        pass
    
    @abstractmethod
    def close(self):
        """Close connections/files"""
        pass