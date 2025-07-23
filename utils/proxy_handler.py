import os
import itertools
import requests
from typing import Dict, List, Optional
from .logging_config import setup_logger
from models.proxy_config import ProxyConfig


class ProxyHandler:
    """
    Unified proxy manager:
      - PROXY_TYPE=nordvpn    NordVPN only
      - PROXY_TYPE=custom     custom proxies only
      - PROXY_TYPE=both       NordVPN + custom proxies in rotation
    """

    def __init__(self, enabled: bool = False):
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

        self.enabled = enabled
        self.proxies: List[ProxyConfig] = []
        self._cycle = None
        self.current_proxy: Optional[ProxyConfig] = None

        self._initialize_proxy()

    def _initialize_proxy(self) -> None:
        if not self.enabled:
            self.logger.info("Proxy handling disabled")
            return

        proxy_type = os.getenv("PROXY_TYPE", "nordvpn").lower()

        if proxy_type == "both":
            self.proxies = self._build_nordvpn_proxy() + self._load_custom_proxies()
        elif proxy_type == "nordvpn":
            self.proxies = self._build_nordvpn_proxy()
        elif proxy_type == "custom":
            self.proxies = self._load_custom_proxies()
        else:
            self.logger.warning(f"Unknown PROXY_TYPE '{proxy_type}', disabling proxy")
            self.enabled = False
            return

        if not self.proxies:
            self.logger.warning("No proxies configured; proxy mode disabled")
            self.enabled = False
            return

        self._cycle = itertools.cycle(self.proxies)
        self.current_proxy = next(self._cycle)
        self.logger.info(f"Proxy rotation enabled with {len(self.proxies)} proxies")

    def _build_nordvpn_proxy(self) -> List[ProxyConfig]:
        """Return NordVPN proxy if TOKEN exists, else empty list."""
        if not os.getenv("NORDVPN_TOKEN"):
            return []
        return [
            ProxyConfig(
                address="nordvpn",
                port=1080,
                protocol="socks5h",
                username=os.getenv("NORDVPN_USER"),
                password=os.getenv("NORDVPN_PASSWORD"),
            )
        ]

    def _load_custom_proxies(self) -> List[ProxyConfig]:
        """Parse PROXY_1_*, PROXY_2_* … from environment."""
        configs: List[ProxyConfig] = []
        idx = 1
        while True:
            prefix = f"PROXY_{idx}_"
            address = os.getenv(f"{prefix}ADDRESS")
            if not address:
                break
            port = int(os.getenv(f"{prefix}PORT", "8080"))
            protocol = os.getenv(f"{prefix}PROTOCOL", "http")
            user = os.getenv(f"{prefix}USER") or None
            pwd = os.getenv(f"{prefix}PASSWORD") or None
            configs.append(
                ProxyConfig(
                    address=address,
                    port=port,
                    protocol=protocol,
                    username=user,
                    password=pwd,
                )
            )
            idx += 1
        return configs

    def get_current_proxy(self) -> Dict[str, str]:
        """Return current proxy in requests-friendly dict."""
        if not self.enabled or not self.current_proxy:
            return {}

        cfg = self.current_proxy
        auth = (
            f"{cfg.username}:{cfg.password}@"
            if cfg.username and cfg.password
            else ""
        )
        url = f"{cfg.protocol}://{auth}{cfg.address}:{cfg.port}"
        return {"http": url, "https": url}

    def health_check(self) -> bool:
        """Hit ipify to verify connectivity and log IP/location."""
        if not self.enabled:
            self.logger.warning("Health check skipped: proxy disabled")
            return False

        try:
            resp = requests.get(
                "https://api.ipify.org?format=json",
                proxies=self.get_current_proxy(),
                timeout=10,
            )
            resp.raise_for_status()
            ip = resp.json()["ip"]
            self.logger.info(f"Proxy health OK. Current IP: {ip}")

            if os.getenv("VERIFY_LOCATION", "false").lower() == "true":
                geo = requests.get(
                    f"http://ip-api.com/json/{ip}", timeout=5
                ).json()
                self.logger.info(
                    f"Location: {geo.get('country', '?')}, {geo.get('city', '?')}"
                )
            return True

        except Exception as exc:
            self.logger.error(f"Proxy health check failed: {exc}")
            return False

    def rotate_proxy(self) -> None:
        """Switch to the next proxy in the rotation list."""
        if not self.enabled or not self._cycle:
            return

        self.current_proxy = next(self._cycle)
        self.logger.info(
            f"Rotated to proxy {self.proxies.index(self.current_proxy) + 1}/"
            f"{len(self.proxies)}: {self.current_proxy.address}"
        )