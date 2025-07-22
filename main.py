#!/usr/bin/env python3
import os
import logging
from typing import List, Dict
from factories.scraper_factory import ScraperFactory
from factories.persistence_factory import PersistenceFactory
from utils.logging_config import setup_logger
from utils.request_handler import RequestHandler
from utils.proxy_handler import ProxyHandler
from models.movie_model import Movie

def main():
    logger = setup_logger(__name__)
    logger.info("Starting IMDB Top Movies Scraper")

    try:
        proxy_enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
        proxy_handler = ProxyHandler(enabled=proxy_enabled)
        
        if proxy_enabled and not proxy_handler.health_check():
            logger.warning("Proxy configurado pero no funciona, continuando sin proxy")
            request_handler = RequestHandler()
        else:
            request_handler = RequestHandler(proxy_handler=proxy_handler)

        scraper = ScraperFactory.create_scraper('imdb', request_handler=request_handler)

        persistence_type = os.getenv('PERSISTENCE_TYPE', 'csv')
        persistence = PersistenceFactory.create_persistence(persistence_type)
        logger.info(f"Modo de persistencia: {persistence_type}")

        imdb_url = os.getenv('IMDB_URL', 'https://www.imdb.com/chart/top/')
        imdb_url = 'https://caching.graphql.imdb.com/?operationName=Top250MoviesPagination&variables={"first":250,"isInPace":false,"locale":"es-MX"}&extensions={"persistedQuery":{"sha256Hash":"2db1d515844c69836ea8dc532d5bff27684fdce990c465ebf52d36d185a187b3","version":1}}'
        logger.info(f"Iniciando scraping de: {imdb_url}")
        
        movies_data = scraper.extract_data(imdb_url, use_proxy=False, verify_proxy=False)
        logger.info(f"Obtenidas {len(movies_data)} películas")

        movies = [Movie(**data) for data in movies_data]
        if persistence.save_bulk_movies(movies):
            logger.info("Datos guardados exitosamente")
        else:
            logger.error("Error al guardar datos")

        logger.info("\n=== Resumen del Scraping ===")
        for movie in movies[:5]:  # Mostrar solo las primeras 5 como ejemplo
            logger.info(f"• {movie.title} ({movie.year}) - Rating: {movie.rating}")

    except Exception as e:
        logger.error(f"Error en la ejecución principal: {str(e)}", exc_info=True)
        raise

    finally:
        # Limpieza
        if 'persistence' in locals():
            persistence.close()
        logger.info("Scraping completado")

if __name__ == '__main__':
    # Configuración básica para ejecución directa
    os.environ.setdefault('PROXY_ENABLED', 'false')
    os.environ.setdefault('PERSISTENCE_TYPE', 'csv')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    main()