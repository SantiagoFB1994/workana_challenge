from dataclasses import dataclass
from typing import Optional

@dataclass
class ProxyConfig:
    address: str
    port: int
    protocol: str
    username: Optional[str] = None
    password: Optional[str] = None
