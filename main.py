import os
import itertools
from factories.scraper_factory import ScraperFactory
from factories.persistence_factory import PersistenceFactory
from utils.logging_config import setup_logger
from utils.request_handler import RequestHandler
from utils.proxy_handler import ProxyHandler

def main():
    logger = setup_logger(__name__)
    logger.info("Starting IMDB Top Movies Scraper")

    try:
        proxy_enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
        proxy_handler = ProxyHandler(enabled=proxy_enabled)
        request_handler = RequestHandler(
            proxy_handler if proxy_enabled and proxy_handler.health_check() else None
        )

        scraper = ScraperFactory.create_scraper('imdb', request_handler=request_handler)

        csv_handler   = PersistenceFactory.create_persistence('csv')
        pg_handler    = PersistenceFactory.create_persistence('postgres')

        imdb_url = os.getenv(
            'IMDB_URL',
            'https://caching.graphql.imdb.com/?operationName=Top250MoviesPagination&variables={"first":250,"isInPace":false,"locale":"es-MX"}&extensions={"persistedQuery":{"sha256Hash":"2db1d515844c69836ea8dc532d5bff27684fdce990c465ebf52d36d185a187b3","version":1}}'
        )
        logger.info(f"Scraping {imdb_url}")

        batch_size = int(os.getenv("BATCH_SIZE", 1_000))
        movies_stream = scraper.extract_data(imdb_url, use_proxy=False, verify_proxy=False)

        # tee the stream so we write CSV and Postgres without double scraping
        csv_stream, pg_stream = itertools.tee(movies_stream)

        csv_count  = csv_handler.save_stream(csv_stream,  batch_size=batch_size)
        pg_count   = pg_handler.save_stream(pg_stream,   batch_size=batch_size)

        logger.info(f"CSV  : wrote {csv_count} rows")
        logger.info(f"Postgres: wrote {pg_count} rows")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        try:
            pg_handler.close()
        except Exception:
            pass
        logger.info("Scraping finished")

if __name__ == '__main__':
    os.environ.setdefault('PROXY_ENABLED', 'false')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    main()