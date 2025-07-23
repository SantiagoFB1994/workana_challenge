from abc import ABC, abstractmethod
from typing import Dict

class BaseScraper(ABC):
    @abstractmethod
    def extract_data(self, url: str) -> Dict:
        """Main method for data extraction"""
        pass

    @abstractmethod
    def _parse_movie_details(self, html: str) -> Dict:
        """Extract movie details"""
        pass

    @staticmethod
    def validate_movie_data(data: Dict) -> bool:
        """Validate extracted data from movies"""
        required_fields = ['id', 'title', 'year', 'rating', 'duration']
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_actor_data(data: Dict) -> bool:
        """Validate extracted actor data"""
        required_fields = ['id', 'name', 'movie_id', 'is_main_actor']
        return all(field in data for field in required_fields)