import logging
import os
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def setup_logger(name: str = "imdb_scraper") -> logging.Logger:
    """
    Configure a logger whose level is controlled by the env variable LOG_LEVEL
    (default = INFO).  Console uses the same level; file always logs DEBUG+.
    """
    log_level = _LEVEL_MAP.get(os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console (same level as env)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Rotating file (always DEBUG so nothing is lost)
    log_file = log_dir / f"{name}_{datetime.now():%Y%m%d}.log"
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger