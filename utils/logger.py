# utils/logger.py
import logging
import os
from datetime import datetime


class ScheduleLogger:
    def __init__(self, log_file: str = 'logs/schedule_generator.log'):
        # Upewnij się, że katalog logs istnieje
        os.makedirs('logs', exist_ok=True)

        # Skonfiguruj logger
        self.logger = logging.getLogger('ScheduleGenerator')
        self.logger.setLevel(logging.DEBUG)

        # Usuń poprzednie handlery (jeśli istnieją)
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Handler do pliku
        file_handler = logging.FileHandler(log_file, mode='w')  # 'w' nadpisuje plik
        file_handler.setLevel(logging.DEBUG)

        # Handler do konsoli
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Format logów
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Dodaj handlery do loggera
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Zapisz czas rozpoczęcia
        self.start_time = datetime.now()
        self.logger.info(f"Zapisano czas rozpoczęcia: {self.start_time}")

    def log_error(self, message: str):
        """Loguje błąd"""
        self.logger.error(message)

    def log_warning(self, message: str):
        """Loguje ostrzeżenie"""
        self.logger.warning(message)

    def log_info(self, message: str):
        """Loguje informację"""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Loguje informację debugowania"""
        self.logger.debug(message)

    def log_validation_errors(self, class_name: str, errors: list):
        """Loguje błędy walidacji dla danej klasy"""
        if errors:
            self.logger.error(f"Znaleziono błędy w planie klasy {class_name}:")
            for error in errors:
                self.logger.error(f"  - {error}")

    def log_generation_stats(self, generated_classes: int, total_errors: int):
        """Loguje statystyki generowania planu"""
        duration = datetime.now() - self.start_time
        self.logger.info(f"""
Zakończono generowanie planu:
- Wygenerowano planów: {generated_classes}
- Liczba błędów: {total_errors}
- Czas generowania: {duration}
        """.strip())
