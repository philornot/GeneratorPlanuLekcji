# src/utils/logger.py

import logging
import sys
from datetime import datetime
from pathlib import Path


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

    # Utworzenie katalogu logs jeśli nie istnieje
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Handler do pliku
    log_file = logs_dir / f'scheduler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
