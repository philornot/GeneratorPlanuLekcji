# main.py
import os
import time
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from generators import ScheduleGenerator, GeneratorConfig
from utils import ScheduleLogger


def create_output_dirs():
    """Tworzy wymagane katalogi"""
    dirs = ['output', 'logs', 'output/classes', 'output/teachers', 'output/rooms']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)


def generate_html(schedule, env):
    """Generuje pliki HTML dla wszystkich widoków"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generuj plany dla klas
    for class_name, school_class in schedule.classes.items():
        template = env.get_template('class_schedule.html')
        html = template.render(
            class_name=class_name,
            class_data=school_class.to_dict()
        )
        with open(f'output/classes/{class_name}_{timestamp}.html', 'w', encoding='utf-8') as f:
            f.write(html)

    # Generuj plany dla nauczycieli
    for teacher_id, teacher in schedule.teachers.items():
        template = env.get_template('teacher_schedule.html')
        html = template.render(teacher_data=teacher.to_dict())
        with open(f'output/teachers/{teacher_id}_{timestamp}.html', 'w', encoding='utf-8') as f:
            f.write(html)

    # Generuj plan całej szkoły
    template = env.get_template('school_schedule.html')
    html = template.render(schedule_data=schedule.to_dict())
    with open(f'output/school_schedule_{timestamp}.html', 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    # Inicjalizacja
    create_output_dirs()
    logger = ScheduleLogger()
    logger.log_info("Rozpoczynanie generowania planu lekcji")

    # Konfiguracja szablonów Jinja2
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=True
    )

    # Konfiguracja generatora
    config = GeneratorConfig(
        max_iterations=200,  # Mniej iteracji, ale bardziej efektywnych
        min_score=75.0,  # Nieco niższy próg akceptacji
        population_size=20,  # Większa populacja
        mutation_rate=0.3,  # Większa szansa na mutacje
        retry_count=5  # Więcej prób przy przydzielaniu lekcji
    )

    try:
        # Tworzenie i inicjalizacja generatora
        start_time = time.time()
        generator = ScheduleGenerator(config)
        generator.initialize_schedule()

        # Generowanie planu
        logger.log_info("Rozpoczynanie procesu generowania")
        success = generator.generate_schedule()

        if success:
            logger.log_info("Plan został wygenerowany pomyślnie")

            # Walidacja planu
            errors = generator.schedule.validate_schedule()
            if errors:
                logger.log_warning("Znaleziono błędy w planie:")
                for category, category_errors in errors.items():
                    for error in category_errors:
                        logger.log_warning(f"{category}: {error}")

            # Generowanie HTML
            generate_html(generator.schedule, env)

            # Podsumowanie
            end_time = time.time()
            duration = end_time - start_time
            schedule = generator.schedule

            logger.log_info(f"""
            Podsumowanie generowania:
            - Czas wykonania: {duration:.2f} sekund
            - Liczba klas: {len(schedule.classes)}
            - Liczba nauczycieli: {len(schedule.teachers)}
            - Liczba sal: {len(schedule.classrooms)}
            - Liczba lekcji: {len(schedule.lessons)}
            - Ocena planu: {schedule.calculate_schedule_score():.2f}/100
            """)
        else:
            logger.log_error("Nie udało się wygenerować planu spełniającego wszystkie kryteria")

    except Exception as e:
        logger.log_error(f"Wystąpił błąd: {str(e)}")
        raise


if __name__ == "__main__":
    main()
