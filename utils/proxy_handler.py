# utils/proxy_handler.py
import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
import requests

@dataclass
class ProxyConfig:
    address: str
    port: int
    protocol: str
    username: Optional[str] = None
    password: Optional[str] = None

class ProxyHandler:
    def __init__(self, enabled: bool = False):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enabled = enabled
        self.current_proxy = None
        self._initialize_proxy()

    def _initialize_proxy(self) -> None:
        """Initialize proxy configuration based on environment"""
        if not self.enabled:
            self.logger.info("Proxy handling disabled")
            return

        # Configuración para NordVPN en Docker
        if os.getenv('PROXY_TYPE', 'nordvpn').lower() == 'nordvpn':
            self.current_proxy = ProxyConfig(
                address='nordvpn',  # Nombre del servicio en docker-compose
                port=1080,
                protocol='socks5h',  # socks5h para resolver DNS via proxy
                username=os.getenv('NORDVPN_USER'),
                password=os.getenv('NORDVPN_PASSWORD')
            )
            self.logger.info("Configured NordVPN proxy in Docker network")
        else:
            # Configuración para proxies custom
            self.current_proxy = ProxyConfig(
                address=os.getenv('PROXY_ADDRESS_1'),
                port=int(os.getenv('PROXY_PORT_1', '8080')),
                protocol=os.getenv('PROXY_PROTOCOL_1', 'http'),
                username=os.getenv('PROXY_USER_1'),
                password=os.getenv('PROXY_PASSWORD_1')
            )
            self.logger.info(f"Configured custom proxy: {self.current_proxy.address}")

    def get_current_proxy(self) -> Dict[str, str]:
        """Get current proxy configuration in requests format"""
        if not self.enabled or not self.current_proxy:
            return {}

        proxy_url = f"{self.current_proxy.protocol}://"
        
        if self.current_proxy.username and self.current_proxy.password:
            proxy_url += f"{self.current_proxy.username}:{self.current_proxy.password}@"
        
        proxy_url += f"{self.current_proxy.address}:{self.current_proxy.port}"

        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def health_check(self) -> bool:
        """Verify proxy connection and log detailed info"""
        if not self.enabled:
            self.logger.warning("Health check skipped: Proxy disabled")
            return False

        try:
            # Primero verificamos conectividad básica
            test_url = "https://api.ipify.org?format=json"
            proxies = self.get_current_proxy()
            
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Proxy health check failed with status: {response.status_code}")
                return False

            # Verificación adicional de ubicación
            ip_data = response.json()
            self.logger.info(f"Proxy connection successful. Current IP: {ip_data['ip']}")
            
            # Opcional: Verificar ubicación geográfica
            if os.getenv('VERIFY_LOCATION', 'false').lower() == 'true':
                geo_url = f"http://ip-api.com/json/{ip_data['ip']}"
                geo_response = requests.get(geo_url, timeout=5)
                if geo_response.status_code == 200:
                    geo_data = geo_response.json()
                    self.logger.info(f"Location: {geo_data.get('country', 'Unknown')}, {geo_data.get('city', 'Unknown')}")
                    self.logger.debug(f"Full geo data: {geo_data}")
            
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Proxy health check failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during health check: {str(e)}")
            return False

    def rotate_proxy(self) -> None:
        """Rotate proxy (not applicable for NordVPN in Docker)"""
        if not self.enabled:
            return
            
        if os.getenv('PROXY_TYPE') == 'nordvpn':
            self.logger.warning("Proxy rotation not supported for NordVPN in this configuration")
            return
            
        # Implementación para rotación de proxies custom
        # (Mantener tu implementación actual si es necesario)
        self.logger.info("Proxy rotation would happen here for custom proxies")