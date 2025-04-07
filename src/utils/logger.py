# src/utils/logger.py

import logging
import logging.handlers
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# Importujemy colorama do kolorowania wyjścia
from colorama import init, Fore, Style

# Inicjalizacja colorama
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Niestandardowy formatter dodający kolory do całego logu"""

    # Mapowanie poziomów logowania na kolory
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def __init__(self, fmt: str, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Formatujemy rekord najpierw standardowo
        formatted_msg = super().format(record)

        # Dodajemy kolor do całej linii na podstawie poziomu logowania
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{formatted_msg}{Style.RESET_ALL}"

        return formatted_msg


class GPLLogger:
    """
    Zaawansowany logger z kolorowym formatowaniem, organizacją według poziomów,
    i osobnym folderem dla każdej sesji.
    """

    # Ustawienia domyślne
    DEFAULT_LOG_LEVEL = logging.DEBUG
    DEFAULT_CONSOLE_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Mapowanie poziomów logowania na nazwy plików
    LEVEL_FILES = {
        logging.DEBUG: "debug.log",
        logging.INFO: "info.log",
        logging.WARNING: "warning.log",
        logging.ERROR: "error.log",
        logging.CRITICAL: "critical.log"
    }

    # Mapowanie poziomów logowania na minimalne poziomy dla każdego pliku
    LEVEL_MINIMUMS = {
        logging.DEBUG: logging.DEBUG,  # debug.log zawiera wszystkie logi
        logging.INFO: logging.INFO,  # info.log zawiera INFO i wyżej
        logging.WARNING: logging.WARNING,  # warning.log zawiera WARNING i wyżej
        logging.ERROR: logging.ERROR,  # error.log zawiera ERROR i wyżej
        logging.CRITICAL: logging.CRITICAL  # critical.log zawiera tylko CRITICAL
    }

    # Root handler kontrolujący wszystkie logi
    _root_logger = None
    # Folder dla bieżącej sesji logowania
    _session_folder = None

    @classmethod
    def setup_root_logger(cls):
        """Konfiguruje główny logger i folder sesji"""
        if cls._root_logger is not None:
            return

        # Utwórz główny logger
        cls._root_logger = logging.getLogger()
        cls._root_logger.setLevel(logging.DEBUG)

        # Usuń istniejące handlery
        for handler in cls._root_logger.handlers[:]:
            cls._root_logger.removeHandler(handler)

        # Utwórz folder sesji z timestampem
        timestamp = datetime.now().strftime("session-log_%d-%m-%Y_%H-%M-%S")
        cls._session_folder = Path("logs") / f"{timestamp}"
        cls._session_folder.mkdir(parents=True, exist_ok=True)

        # Formattery dla plików i konsoli
        file_formatter = logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)
        console_formatter = ColoredFormatter(cls.LOG_FORMAT, cls.DATE_FORMAT)

        # Utwórz handlery dla każdego poziomu logowania
        for level, filename in cls.LEVEL_FILES.items():
            min_level = cls.LEVEL_MINIMUMS[level]

            file_handler = logging.FileHandler(
                cls._session_folder / filename,
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(min_level)
            file_handler.setFormatter(file_formatter)
            cls._root_logger.addHandler(file_handler)

        # Dodaj handler dla konsoli
        console_handler = logging.StreamHandler()
        console_handler.setLevel(cls.DEFAULT_CONSOLE_LEVEL)
        console_handler.setFormatter(console_formatter)
        cls._root_logger.addHandler(console_handler)

        # Utwórz plik z informacją o sesji
        with open(cls._session_folder / "session_info.txt", "w", encoding="utf-8") as f:
            f.write(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Platform: {sys.platform}\n")

    def __init__(self, name: str):
        """Inicjalizuje logger dla konkretnego modułu"""
        # Upewnij się, że główny logger jest skonfigurowany
        self.__class__.setup_root_logger()

        # Utwórz logger dla konkretnego modułu
        self.name = name
        self.logger = logging.getLogger(name)

        # Cache dla unikania duplikacji logów
        self._log_cache = set()

        # Lock dla bezpieczeństwa wątków
        self._lock = threading.RLock()

        # Loguj inicjalizację
        self.debug(f"Logger initialized: {name}")

    def debug(self, msg: str, *args, **kwargs):
        """Log na poziomie DEBUG"""
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log na poziomie INFO"""
        self._log('info', msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log na poziomie WARNING"""
        self._log('warning', msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log na poziomie ERROR"""
        self._log('error', msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log na poziomie CRITICAL"""
        self._log('critical', msg, *args, **kwargs)

    def exception(self, msg: str, *args, exc_info=True, **kwargs):
        """Log z informacją o wyjątku"""
        self._log('error', msg, *args, exc_info=exc_info, **kwargs)

    def _log(self, level: str, msg: str, *args, cache_key: Optional[str] = None, **kwargs):
        """
        Logowanie z cache'owaniem, aby uniknąć duplikacji
        """
        with self._lock:
            # Sprawdzenie cache'a
            if cache_key:
                if cache_key in self._log_cache:
                    return
                self._log_cache.add(cache_key)

            # W wątkach nie-głównych pozwalamy tylko na logi INFO i wyżej
            if threading.current_thread() != threading.main_thread():
                if level == 'debug':
                    return

            # Logowanie
            try:
                log_func = getattr(self.logger, level)
                log_func(msg, *args, **kwargs)
            except Exception as e:
                # Awaryjne wypisanie na konsolę w przypadku problemów
                print(f"Error logging message: {e}")
                print(f"Original message: {level.upper()} - {msg}")

    def set_level(self, level: Union[int, str]):
        """Zmienia poziom logowania dla tego loggera"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def clear_cache(self):
        """Czyści cache logów"""
        with self._lock:
            self._log_cache.clear()

    @classmethod
    def get_session_folder(cls) -> Path:
        """Zwraca ścieżkę do folderu bieżącej sesji"""
        if cls._session_folder is None:
            cls.setup_root_logger()
        return cls._session_folder


# Funkcja pomocnicza dla łatwego tworzenia loggera
def get_logger(name: str) -> GPLLogger:
    """Zwraca logger dla podanego modułu"""
    return GPLLogger(name)
