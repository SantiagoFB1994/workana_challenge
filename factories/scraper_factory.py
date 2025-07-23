from scrapers.base_scraper import BaseScraper
from scrapers.imdb import IMDBScraper
from typing import Any

class ScraperFactory:
    @staticmethod
    def create_scraper(
        site: str,
        request_handler: Any = None,
        **kwargs
    ) -> BaseScraper:
        scrapers = {
            'imdb': IMDBScraper,
            # 'rottentomatoes': RottenTomatoesScraper,
        }

        site = site.lower()
        if site not in scrapers:
            raise ValueError(
                f"Site not supported: {site}. "
                f"Available options: {list(scrapers.keys())}"
            )

        # Instantiate and inject dependencies
        scraper_cls = scrapers[site]
        return scraper_cls(
            request_handler=request_handler,
            **kwargs
        )