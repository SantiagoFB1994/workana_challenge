import logging
import time
import os
from curl_cffi import requests
from typing import Dict, Optional
from .proxy_handler import ProxyHandler

class RequestHandler:
    def __init__(self, proxy_handler: Optional[ProxyHandler] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.proxy_handler = proxy_handler

    def _get_request_params(self, headers, use_proxy: bool = True) -> Dict:
        """Prepare common request parameters"""
        params = {
            'headers': {**headers},
            'timeout': int(os.getenv('REQUEST_TIMEOUT', 30)),
        }

        if use_proxy and self.proxy_handler and self.proxy_handler.enabled:
            proxies = self.proxy_handler.get_current_proxy()
            
            # Special handling for SOCKS proxies
            if 'socks' in proxies.get('http', ''):
                proxies = {
                    'http': proxies['http'].replace('socks5', 'socks5h'),
                    'https': proxies['https'].replace('socks5', 'socks5h')
                }
            
            params['proxies'] = proxies
            self.logger.debug(f"Using proxy: {proxies.get('http')}")

        return params

    def get(self, url: str, headers: dict, use_proxy: bool, verify_proxy: bool ,max_retries: Optional[int] = None) -> requests.Response:
        """Make GET request with proxy handling"""
        max_retries = max_retries or int(os.getenv('MAX_RETRIES', 3))
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Verify proxy health before first attempt
                if attempt == 0 and use_proxy and self.proxy_handler and verify_proxy:
                    if not self.proxy_handler.health_check():
                        self.logger.warning("Proxy health check failed, attempting anyway...")

                params = self._get_request_params(headers, use_proxy=use_proxy)
                self.logger.debug(f"Attempt {attempt + 1} for {url}")

                response = requests.get(url, **params)
                response.raise_for_status()
                
                # Additional validation
                if not self._validate_response(response):
                    raise ValueError("Invalid response content")
                
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # Rotate proxy if enabled (only for custom proxies)
                if self.proxy_handler and self.proxy_handler.enabled:
                    self.proxy_handler.rotate_proxy()
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 10)  # Max 10 seconds
                    self.logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)

        self.logger.error(f"Failed after {max_retries} attempts for {url}")
        raise last_exception or requests.exceptions.RequestException("Request failed")

    def _validate_response(self, response: requests.Response) -> bool:
        """Validate response content"""
        if not response.text:
            self.logger.error("Empty response received")
            return False
            
        if "Access Denied" in response.text:
            self.logger.error("Detected access denial")
            return False
            
        return True