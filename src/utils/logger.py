# src/utils/logger.py

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


class GPLLogger:
    def __init__(self, name: str, log_dir: str = 'logs'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Utworzenie katalogu logów
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Format logów z dodatkowymi metadanymi
        self.formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
        )

        # Handler plików z rotacją
        log_file = self.log_dir / f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(self.formatter)
        file_handler.setLevel(logging.DEBUG)

        # Handler konsoli
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        console_handler.setLevel(logging.INFO)

        # Dodanie handlerów
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Cache dla unikania duplikacji logów
        self._log_cache = set()

    def debug(self, msg: str, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._log('error', msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._log('critical', msg, *args, **kwargs)

    def _log(self, level: str, msg: str, *args, cache_key: Optional[str] = None, **kwargs):
        """
        Logowanie z cache'owaniem aby uniknąć duplikacji
        """
        if cache_key:
            if cache_key in self._log_cache:
                return
            self._log_cache.add(cache_key)

        log_func = getattr(self.logger, level)
        log_func(msg, *args, **kwargs)