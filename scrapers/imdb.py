import os
import json
from bs4 import BeautifulSoup
from utils.request_handler import RequestHandler
from typing import Dict, List
from .base_scraper import BaseScraper
from models.movie_model import Movie, Actor

class IMDBScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.max_retries = os.getenv("MAX_RETRIES", 3)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Alt-Used': 'www.imdb.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        self.api_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/graphql+json, application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.imdb.com/",
            "content-type": "application/json",
            "x-imdb-client-name": "imdb-web-next-localized",
            "x-imdb-user-language": "en-US",
            "x-imdb-user-country": "US",
            "x-imdb-weblab-treatment-overrides": "{}",
            "Origin": "https://www.imdb.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": ""
        }
        self.http_client = RequestHandler()

    def extract_data(self, url: str, use_proxy: bool, verify_proxy: bool) -> List[Dict]:
        """Extract titles from IMDB chart"""
        self.logger.info(f"Scraping URL: {url}")
        
        try:
            response = self.http_client.get(url, headers=self.api_headers, use_proxy=use_proxy, verify_proxy=verify_proxy)
            resp_json = response.json()
            
            movies = []
            for movie in resp_json["data"]["chartTitles"]["edges"]:
                movies.append(f"https://www.imdb.com/title/{movie['node']['id']}")
            
            return movies            
        except Exception as e:
            self.logger.error(f"Error al scrapear {url}: {str(e)}", exc_info=True)
            raise

    def _parse_movie_details(self, row) -> Dict:
        """Extrae datos de una fila de película"""
        title = row.find('h3').get_text(strip=True)
        year = row.find('span', class_='cli-title-metadata-item').get_text(strip=True)
        rating = row.find('span', class_='rating-group--imdb-rating').get_text(strip=True).split()[0]
        
        # Obtener URL de detalles para información adicional
        detail_url = "https://www.imdb.com" + row.find('a')['href']
        details = self._get_movie_details(detail_url)
        
        return {
            'title': title,
            'year': year,
            'rating': float(rating),
            'duration': details.get('duration'),
            'metascore': details.get('metascore'),
            'actors': details.get('actors', [])
        }

    def _get_movie_details(self, url: str, use_proxy: bool, verify_proxy: bool) -> Dict:
        """Obtiene detalles adicionales de la página de la película"""
        try:
            response = self.http_client.get(url, headers=self.api_headers, use_proxy=use_proxy, verify_proxy=verify_proxy)
            soup = BeautifulSoup(response.text, 'html.parser')
            json_data = json.loads(soup.find("script", {"id":"__NEXT_DATA__"}).contents[0])
            return {
                'duration': self._parse_duration(soup),
                'metascore': self._parse_metascore(soup),
                'actors': self._parse_actors(soup)
            }
        except Exception as e:
            self.logger.warning(f"Error obteniendo detalles: {str(e)}")
            return {}

    # Métodos auxiliares para parsear detalles específicos...
    def _parse_duration(self, soup):
        # Implementación específica
        pass
        
    def _parse_metascore(self, soup):
        # Implementación específica
        pass
        
    def _parse_actors(self, soup):
        # Implementación específica
        pass