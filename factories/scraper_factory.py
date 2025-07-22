from typing import Type
from scrapers.base_scraper import BaseScraper
from utils.request_handler import RequestHandler
from scrapers.imdb import IMDBScraper

class ScraperFactory:
    """Factory to create scraper instances acording to website"""
    
    @staticmethod
    def create_scraper(site: str, request_handler: RequestHandler) -> Type[BaseScraper]:
        """
        Create an instance of the scraper for the specified site
        
        Args:
            site: Site identifier ('imdb', 'rottentomatoes', etc.)
            
        Returns:
            Scraper instance
            
        Raises:
            ValueError: if site is not supported
        """
        scrapers = {
            'imdb': IMDBScraper,
            # More scrapers can be added in the future
            # 'rottentomatoes': RottenTomatoesScraper,
        }
        
        if site.lower() not in scrapers:
            raise ValueError(f"Site not supported: {site}. Available options: {list(scrapers.keys())}")
            
        return scrapers[site.lower()]()