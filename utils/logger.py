# utils/logger.py
import os
import sys
from datetime import datetime

from loguru import logger


class ScheduleLogger:
    def __init__(self, log_file: str = 'logs/schedule_generator.log'):
        # Upewnij się, że katalog logs istnieje
        os.makedirs('logs', exist_ok=True)

        # Usuń domyślny sink
        logger.remove()

        # Klasa do zliczania duplikatów
        class DuplicateCounter:
            def __init__(self):
                self.last_message = None
                self.count = 0
                self.shown = 0

        counter = DuplicateCounter()

        def duplicate_filter(record):
            if counter.last_message == record["message"]:
                counter.count += 1
                if counter.shown < 3:
                    counter.shown += 1
                    if counter.shown == 3 and counter.count > 3:
                        # Modyfikuj trzeci log, aby pokazać liczbę dodatkowych wystąpień
                        extra = counter.count - 3
                        record["message"] += f" [{extra} {'raz' if extra == 1 else 'razy'} więcej...]"
                    return counter.shown <= 3
                return False
            else:
                # Nowa wiadomość - reset liczników
                counter.last_message = record["message"]
                counter.count = 1
                counter.shown = 1
                return True

        # Format logów
        format_str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level: <8}</level> - {message}"

        # Handler do pliku
        logger.add(
            log_file,
            format=format_str,
            filter=duplicate_filter,
            mode='w',  # nadpisuje plik
            level="DEBUG",
            enqueue=True  # zapewnia bezpieczeństwo wątków
        )

        # Handler do konsoli
        logger.add(
            sys.stderr,
            format=format_str,
            filter=duplicate_filter,
            level="DEBUG",
            enqueue=True
        )

        # Zapisz czas rozpoczęcia
        self.start_time = datetime.now()

    def log_error(self, message: str):
        """Loguje błąd"""
        logger.error(message)

    def log_warning(self, message: str):
        """Loguje ostrzeżenie"""
        logger.warning(message)

    def log_info(self, message: str):
        """Loguje informację"""
        logger.info(message)

    def log_debug(self, message: str):
        """Loguje informację debugowania"""
        logger.debug(message)

    def log_validation_errors(self, class_name: str, errors: list):
        """Loguje błędy walidacji dla danej klasy"""
        if errors:
            logger.error(f"Znaleziono błędy w planie klasy {class_name}:")
            for error in errors:
                logger.error(f"  - {error}")

    def log_generation_stats(self, generated_classes: int, total_errors: int):
        """Loguje statystyki generowania planu"""
        duration = datetime.now() - self.start_time
        logger.info(f"""
Zakończono generowanie planu:
- Wygenerowano planów: {generated_classes}
- Liczba błędów: {total_errors}
- Czas generowania: {duration}
        """.strip())
