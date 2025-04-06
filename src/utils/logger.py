# src/utils/logger.py

import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union

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


class ThreadSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Bezpieczny dla wątków handler rotacji plików"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    def emit(self, record):
        """Thread-safe emitowanie rekordów do pliku"""
        with self._lock:
            try:
                super().emit(record)
            except Exception as e:
                # Unikamy zawieszania programu przy problemach z plikami
                print(f"Błąd zapisywania logu do pliku: {e}")

    def doRollover(self):
        """Bezpieczniejsza implementacja rotacji plików"""
        with self._lock:
            try:
                # Obsługa problemów z otwartym plikiem na Windows
                if sys.platform == 'win32':
                    try:
                        # Zamykamy plik przed rotacją
                        if self.stream:
                            self.stream.close()
                            self.stream = None

                        # Próbujemy zmienić nazwę pliku
                        if os.path.exists(self.baseFilename + ".1"):
                            try:
                                os.remove(self.baseFilename + ".1")
                            except:
                                pass

                        if os.path.exists(self.baseFilename):
                            try:
                                os.rename(self.baseFilename, self.baseFilename + ".1")
                            except:
                                pass

                        # Tworzymy nowy plik
                        self.mode = 'w'
                        self.stream = self._open()
                        return
                    except Exception as e:
                        print(f"Błąd rotacji logu: {e}")

                # Standardowa rotacja dla innych platform
                super().doRollover()
            except Exception as e:
                print(f"Błąd rotacji logu: {e}")


class GPLLogger:
    """
    Zaawansowany logger z kolorowym formatowaniem i obsługą wielowątkowości.

    Przykłady użycia:
    ```
    logger = GPLLogger(__name__)
    logger.info("Rozpoczynam operację")
    logger.debug("Wartość zmiennej x = %s", x)
    logger.warning("Uwaga, wykryto potencjalny problem")
    logger.error("Wystąpił błąd: %s", e)
    ```
    """

    # Ustawienia domyślne
    DEFAULT_LOG_LEVEL = logging.DEBUG
    DEFAULT_CONSOLE_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Słownik logerów (singleton per name)
    _instances: Dict[str, 'GPLLogger'] = {}

    def __new__(cls, name: str, *args, **kwargs):
        """Implementacja wzorca Singleton per name"""
        if name not in cls._instances:
            cls._instances[name] = super(GPLLogger, cls).__new__(cls)
        return cls._instances[name]

    def __init__(self, name: str, log_dir: str = 'logs',
                 log_level: int = DEFAULT_LOG_LEVEL,
                 console_level: int = DEFAULT_CONSOLE_LEVEL,
                 format: str = LOG_FORMAT,
                 date_format: str = DATE_FORMAT):

        # Unikamy ponownej inicjalizacji
        if hasattr(self, 'initialized') and self.initialized:
            return

        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Usuwamy istniejące handlery (aby uniknąć duplikacji)
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Utworzenie katalogu logów
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)

        # Format logu
        self.log_format = format
        self.date_format = date_format

        # Tworzymy formattery
        file_formatter = logging.Formatter(format, date_format)
        console_formatter = ColoredFormatter(format, date_format)

        # Tworzymy handlery
        self._setup_file_handler(file_formatter, log_level)
        self._setup_console_handler(console_formatter, console_level)

        # Cache dla unikania duplikacji logów
        self._log_cache = set()

        # Lock dla bezpieczeństwa wątków
        self._lock = threading.RLock()

        # Oznaczamy jako zainicjalizowany
        self.initialized = True

        # Log potwierdzający inicjalizację
        self.debug(f"Logger initialized: {name}")

    def _setup_file_handler(self, formatter: logging.Formatter, level: int):
        """Konfiguruje handler dla zapisywania do pliku"""
        log_file = self.log_dir / f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log'

        # Używamy naszego bezpiecznego handlera
        file_handler = ThreadSafeRotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self, formatter: logging.Formatter, level: int):
        """Konfiguruje handler dla wyświetlania na konsoli"""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)

        self.logger.addHandler(console_handler)

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

    def exception(self, msg: str, *args, exc_info=True, **kwargs):
        """Log z informacją o wyjątku"""
        self._log('error', msg, *args, exc_info=exc_info, **kwargs)

    def _log(self, level: str, msg: str, *args, cache_key: Optional[str] = None, **kwargs):
        """
        Logowanie z cache'owaniem aby uniknąć duplikacji
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
        """Zmienia poziom logowania"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def clear_cache(self):
        """Czyści cache logów"""
        with self._lock:
            self._log_cache.clear()


# Funkcja pomocnicza dla łatwego tworzenia loggera
def get_logger(name: str) -> GPLLogger:
    """Zwraca logger dla podanego modułu"""
    return GPLLogger(name)
