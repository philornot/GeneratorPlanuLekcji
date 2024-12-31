# main.py updates
import os
import time
from datetime import datetime

from generators import ScheduleGenerator, GeneratorConfig
from utils import ScheduleLogger
from utils.pdf_generator import SchedulePDFGenerator


def create_output_dirs():
    """Tworzy wymagane katalogi"""
    dirs = ['output', 'logs']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)


def generate_outputs(schedule, start_time, iterations):
    """Generuje wszystkie wymagane wyjścia"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execution_time = time.time() - start_time
    logger = ScheduleLogger()

    # Generuj PDF
    pdf_generator = SchedulePDFGenerator()
    pdf_path = f'output/schedule_{timestamp}.pdf'
    pdf_generator.generate_pdf(
        schedule,
        pdf_path,
        generation_time,
        execution_time,
        iterations
    )
    logger.log_info(f"Wygenerowano PDF: {pdf_path}")


def main():
    # Inicjalizacja
    create_output_dirs()
    logger = ScheduleLogger()

    # Konfiguracja generatora
    config = GeneratorConfig()

    try:
        # Tworzenie i inicjalizacja generatora
        start_time = time.time()
        generator = ScheduleGenerator(config)
        generator.initialize_schedule()

        # Generowanie planu
        logger.log_info("Rozpoczynanie procesu generowania")
        success, iterations = generator.generate_schedule()  # Zmiana tutaj

        if success:
            logger.log_info("Plan został wygenerowany pomyślnie")
            generate_outputs(generator.schedule, start_time, iterations)  # Zmiana tutaj
        else:
            logger.log_error("Nie udało się wygenerować planu spełniającego wszystkie kryteria")

    except Exception as e:
        logger.log_error(f"Wystąpił błąd: {str(e)}")
        raise


if __name__ == "__main__":
    main()
