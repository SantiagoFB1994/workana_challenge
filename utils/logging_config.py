import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name='imdb_scraper'):
    """
    Compact logger config:
    - Console output (INFO+)
    - Rotating file handler output (DEBUG+)
    """
    
    # Log directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (DEBUG +)
    log_file = log_dir / f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5*1024*1024,
        backupCount=3,  
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger