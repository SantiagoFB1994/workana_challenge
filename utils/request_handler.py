# request_handler.py
import time
import os
from curl_cffi import requests
from typing import Dict, Optional
from utils.logging_config import setup_logger
from .proxy_handler import ProxyHandler


class RequestHandler:
    def __init__(self, proxy_handler: Optional[ProxyHandler] = None):
        self.logger = setup_logger(__name__)
        self.proxy_handler = proxy_handler
        self._current_ip: Optional[str] = None  # cached IP

    def _resolve_ip(self, use_proxy: bool) -> str:
        """Query ipify once per proxy change."""
        if use_proxy and self.proxy_handler and self.proxy_handler.enabled:
            try:
                resp = requests.get(
                    "https://api.ipify.org?format=json",
                    proxies=self.proxy_handler.get_current_proxy(),
                    timeout=5,
                    impersonate="chrome110",
                )
                return resp.json().get("ip", "unknown")
            except Exception:
                return "unknown"
        else:
            try:
                resp = requests.get(
                    "https://api.ipify.org?format=json",
                    timeout=5,
                )
                return resp.json().get("ip", "unknown")
            except Exception:
                return "unknown"

    def _get_or_update_ip(self, use_proxy: bool) -> str:
        """Return cached IP or fetch new one."""
        if self._current_ip is None:
            self._current_ip = self._resolve_ip(use_proxy)
        return self._current_ip

    def _get_request_params(self, headers, use_proxy: bool = True) -> Dict:
        params = {
            "headers": {**headers},
            "timeout": int(os.getenv("REQUEST_TIMEOUT", 30)),
        }
        if use_proxy and self.proxy_handler and self.proxy_handler.enabled:
            proxies = self.proxy_handler.get_current_proxy()
            if "socks" in proxies.get("http", ""):
                proxies = {
                    "http": proxies["http"].replace("socks5", "socks5h"),
                    "https": proxies["https"].replace("socks5", "socks5h"),
                }
            params["proxies"] = proxies
        return params

    def get(
        self,
        url: str,
        headers: dict,
        use_proxy: bool,
        verify_proxy: bool,
        max_retries: Optional[int] = None,
    ) -> requests.Response:
        max_retries = max_retries or int(os.getenv("MAX_RETRIES", 3))
        last_exception = None

        for attempt in range(max_retries):
            try:
                if attempt > 0 and self.proxy_handler and self.proxy_handler.enabled:
                    self.proxy_handler.rotate_proxy()
                    self._current_ip = None

                ip = self._get_or_update_ip(use_proxy)
                proxy_url = (
                    self.proxy_handler.get_current_proxy().get("http", "direct")
                    if use_proxy and self.proxy_handler and self.proxy_handler.enabled
                    else "direct"
                )

                if attempt == 0 and use_proxy and self.proxy_handler and verify_proxy:
                    if not self.proxy_handler.health_check():
                        self.logger.warning("Proxy health check failed, continuing anyway...")

                params = self._get_request_params(headers, use_proxy=use_proxy)
                response = requests.get(url, **params)
                self.logger.info(
                    f"GET {response.status_code} [IP:{ip}] [Proxy:{proxy_url}] -> {url}"
                )
                response.raise_for_status()

                if not self._validate_response(response):
                    raise ValueError("Invalid response content")

                return response

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 10)
                    self.logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)

        self.logger.error(f"Failed after {max_retries} attempts for {url}")
        raise last_exception or requests.exceptions.RequestException("Request failed")

    def _validate_response(self, response: requests.Response) -> bool:
        if not response.text:
            self.logger.error("Empty response received")
            return False
        return True