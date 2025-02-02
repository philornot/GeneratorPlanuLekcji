# src/utils/logger.py

import logging
import sys
from datetime import datetime


def setup_logger(name: str) -> logging.Logger:
    """
    Konfiguruje i zwraca logger z określoną nazwą
    """
    # Tworzymy logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Format logów
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler do konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler do pliku
    file_handler = logging.FileHandler(
        f'logs/scheduler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
