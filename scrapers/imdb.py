import os
import json
from bs4 import BeautifulSoup
from typing import Dict, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logging_config import setup_logger
from .base_scraper import BaseScraper
from utils.request_handler import RequestHandler
from models.movie_model import Movie, Actor

class IMDBScraper(BaseScraper):
    def __init__(self, request_handler: RequestHandler = None):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.request_handler = request_handler or RequestHandler()
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

    def extract_data(
        self,
        url: str,
        use_proxy: bool = False,
        verify_proxy: bool = False,
    ) -> Iterator[Movie]:
        """
        Stream top-250 titles from the IMDB chart.
        Yields Movie objects one at a time.
        """
        self.logger.info(f"Scraping URL: {url}")

        try:
            response = self.request_handler.get(
                url,
                headers=self.api_headers,
                use_proxy=use_proxy,
                verify_proxy=verify_proxy,
            )
            edges = response.json()["data"]["chartTitles"]["edges"]
        except Exception as e:
            self.logger.error(f"Failed to fetch chart at {url}: {e}", exc_info=True)
            raise

        def _parse_node(movie_node: Dict) -> Movie:
            imdb_id = movie_node["node"]["id"]
            movie_url = f"https://www.imdb.com/title/{imdb_id}"
            movie = self._parse_movie_details(
                movie_url,
                use_proxy=use_proxy,
                verify_proxy=verify_proxy,
            )
            return movie

        max_workers = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {
                executor.submit(_parse_node, edge): edge
                for edge in edges
            }

            for future in as_completed(future_to_node):
                try:
                    yield future.result()
                except Exception as e:
                    node = future_to_node[future]
                    self.logger.error(
                        f"Error parsing {node['node']['id']}: {e}", exc_info=True
                    )
                    continue

    def _parse_movie_details(self, detail_url: str, use_proxy: bool, verify_proxy: bool) -> Dict:
        """Extract and parse movie data"""
        json_data = self._get_movie_details(detail_url, use_proxy, verify_proxy)
        try:
            movie_details = json_data["props"]["pageProps"]["mainColumnData"]
            _id = movie_details["id"]
            title = movie_details["originalTitleText"]["text"]
            release_year = movie_details["releaseDate"]["year"]
            rating = movie_details["ratingsSummary"]["aggregateRating"]
            runtime = movie_details["runtime"]["seconds"]
            actors = self._parse_actors(movie_details, _id)
            metascore = self.safe_get(json_data, "props", "pageProps", "aboveTheFoldData", "metacritic", "metascore", "score") 
            return Movie(
                movie_id=_id,
                title=title,
                year=release_year,
                rating=rating,
                duration=runtime // 60,
                actors=actors,
                metascore=metascore
            )
        except Exception as e:
            self.logger.error(f"Error parsing {detail_url} details {e}")

    def _get_movie_details(self, url: str, use_proxy: bool, verify_proxy: bool) -> Dict:
        """Obtain aditional movie details"""
        try:
            response = self.request_handler.get(url, headers=self.api_headers, use_proxy=use_proxy, verify_proxy=verify_proxy)
            soup = BeautifulSoup(response.text, 'html.parser')
            json_data = json.loads(soup.find("script", {"id":"__NEXT_DATA__"}).contents[0])
            return json_data
        except Exception as e:
            self.logger.warning(f"Error getting details for {url}: {str(e)}")

    def _parse_actors(self, movie_details: dict, movie_id: str) -> list[Actor]:
        actors = list()
        for actor in movie_details["cast"]["edges"]:
            actor_data = actor["node"]["name"]
            actors.append(
                Actor(
                    name=actor_data["nameText"]["text"],
                    movie_id=movie_id,
                    actor_id=actor_data["id"]
                )
            )
        return actors

    @staticmethod
    def safe_get(mapping, *keys):
        for k in keys:
            if not isinstance(mapping, dict):
                return None
            mapping = mapping.get(k)
        return mapping

