# src/algorithms/genetic_generator.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from deap import base, tools

from src.genetic.creator import create_base_types, get_individual_class
from src.genetic.genetic_evaluator import GeneticEvaluator
from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_population import PopulationManager
from src.models.lesson import Lesson
from src.models.schedule import Schedule
from src.models.school import School
from src.utils.logger import GPLLogger
from src.utils.validators import ScheduleValidator


class ScheduleGenerator:
    def __init__(self, school: School, params: Dict):
        self.school = school
        self.params = params
        self.logger = GPLLogger(__name__)
        self.validator = ScheduleValidator()

        # Komponenty algorytmu genetycznego
        self.operators = GeneticOperators(school)  # Najpierw operators
        self.evaluator = GeneticEvaluator(school, self.operators, params)  # Potem evaluator z operators
        self.population_manager = PopulationManager(school)

        # Inicjalizacja DEAP
        self._setup_deap()

        # Wczytanie najlepszego znanego rozwiązania
        self.best_known_solution = self._load_best_solution()

    def _setup_deap(self):
        """Konfiguracja biblioteki DEAP"""
        try:
            self.logger.debug("Initializing DEAP toolbox")

            # Inicjalizacja typów bazowych
            create_base_types()  # Wywołaj to przed czymkolwiek innym

            self.toolbox = base.Toolbox()

            # Rejestracja funkcji
            self.toolbox.register(
                "lesson_slot",
                self.operators.random_lesson_slot
            )

            # Ważne - użyj get_individual_class zamiast creator.Individual
            individual_class = get_individual_class()
            self.toolbox.register(
                "individual",
                tools.initRepeat,
                individual_class,
                self.toolbox.lesson_slot,
                n=self._calculate_total_lessons()
            )

            self.toolbox.register(
                "population",
                tools.initRepeat,
                list,
                self.toolbox.individual
            )

            # Operatory genetyczne
            self.toolbox.register("evaluate", self.evaluator.evaluate_schedule)
            self.toolbox.register("mate", self.operators.crossover)
            self.toolbox.register("mutate", self.operators.mutation)
            self.toolbox.register("select", tools.selTournament, tournsize=3)

            self.logger.info("DEAP toolbox initialized successfully")

        except Exception as e:
            self.logger.error(f"Error setting up DEAP: {str(e)}")
            raise RuntimeError("Failed to initialize genetic algorithm components")

    def _calculate_total_lessons(self) -> int:
        """Oblicza całkowitą liczbę lekcji do zaplanowania"""
        try:
            total = 0
            for class_group in self.school.class_groups:
                class_total = sum(subject.hours_per_week for subject in class_group.subjects)
                self.logger.debug(
                    f"Class {class_group.name} needs {class_total} lessons per week",
                    cache_key=f"lessons_count_{class_group.name}"
                )
                total += class_total

            self.logger.info(f"Total lessons to schedule: {total}")
            return total

        except Exception as e:
            self.logger.error(f"Error calculating total lessons: {str(e)}")
            raise ValueError("Could not calculate required lessons")

    def _load_best_solution(self) -> Optional[List]:
        """Wczytuje najlepsze znane rozwiązanie"""
        try:
            path = Path('data/best_solution.json')
            if not path.exists():
                return None

            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded best known solution with fitness: {data['fitness']}")
                return data['solution']

        except Exception as e:
            self.logger.warning(f"Could not load best solution: {str(e)}")
            return None

    def _save_best_solution(self, solution: List, fitness: float):
        """Zapisuje najlepsze rozwiązanie"""
        try:
            path = Path('data/best_solution.json')
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'solution': solution,
                'fitness': fitness,
                'timestamp': datetime.now().isoformat()
            }

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Saved new best solution with fitness: {fitness}")

        except Exception as e:
            self.logger.error(f"Error saving best solution: {str(e)}")

    def _generate_basic_schedule(self):
        """
        Generuje podstawowy plan z minimum 1 lekcją dziennie na klasę.
        Zapewnia, że każda klasa ma przydzielone podstawowe przedmioty.

        Returns:
            Schedule: Podstawowy harmonogram z minimalnym zestawem lekcji
        """
        schedule = Schedule(school=self.school)
        self.logger.info("Generowanie podstawowego planu z minimum 1 lekcją dziennie na klasę")

        # Dla każdej klasy...
        for class_group in self.school.class_groups:
            # Lista kluczowych przedmiotów (z najwyższym priorytetem)
            core_subjects = ["matematyka", "polski", "angielski"]
            secondary_subjects = ["fizyka", "chemia", "biologia", "historia", "geografia"]
            other_subjects = [s.name for s in class_group.subjects
                              if s.name not in core_subjects and s.name not in secondary_subjects]

            # Utwórz listę priorytetów przedmiotów
            prioritized_subjects = core_subjects + secondary_subjects + other_subjects

            # ...i każdego dnia tygodnia...
            for day in range(5):
                # Wybierz przedmiot z listy priorytetów
                for subject_name in prioritized_subjects:
                    # Znajdź odpowiedni przedmiot w klasie
                    subject = next((s for s in class_group.subjects if s.name == subject_name), None)
                    if not subject:
                        continue

                    # Spróbuj dodać lekcję o różnych godzinach
                    for hour in range(8):  # 8 godzin lekcyjnych
                        if self._add_basic_lesson(schedule, class_group, day, hour, subject):
                            # Jeśli udało się dodać lekcję, przejdź do następnego dnia
                            break
                    else:
                        # Jeśli nie udało się dodać żadnej lekcji dla tego przedmiotu, spróbuj następny
                        continue

                    # Jeśli udało się dodać lekcję, przejdź do następnego dnia
                    break

        # Loguj statystyki podstawowego planu
        lesson_counts = {}
        for class_group in self.school.class_groups:
            count = len(schedule.get_class_lessons(class_group.name))
            lesson_counts[class_group.name] = count

        self.logger.info(f"Podstawowy plan zawiera {len(schedule.lessons)} lekcji")
        self.logger.info(f"Liczba lekcji per klasa: {lesson_counts}")

        return schedule

    def _add_basic_lesson(self, schedule, class_group, day, hour, subject):
        """
        Pomocnicza metoda do dodawania podstawowych lekcji.

        Args:
            schedule: Obiekt harmonogramu
            class_group: Obiekt klasy
            day: Dzień tygodnia (0-4)
            hour: Godzina lekcyjna (0-7)
            subject: Obiekt przedmiotu

        Returns:
            bool: True jeśli lekcja została dodana, False w przeciwnym razie
        """
        try:
            # Znajdź dostępnych nauczycieli dla tego przedmiotu
            available_teachers = [
                t for t in self.school.teachers.values()
                if subject.name in t.subjects
            ]

            if not available_teachers:
                return False

            # Znajdź odpowiednie sale
            suitable_rooms = [
                r for r in self.school.classrooms.values()
                if self.operators.is_room_suitable(Lesson(
                    subject=subject,
                    teacher=None,
                    classroom=r,
                    class_group=class_group.name,
                    day=day,
                    hour=hour
                ))
            ]

            if not suitable_rooms:
                return False

            # Sprawdź każdą kombinację nauczyciel-sala
            for teacher in available_teachers:
                for classroom in suitable_rooms:
                    # Sprawdź czy slot jest dostępny
                    if self.operators.is_slot_available(
                            day, hour, teacher, classroom, class_group.name
                    ):
                        # Utwórz lekcję
                        lesson = Lesson(
                            subject=subject,
                            teacher=teacher,
                            classroom=classroom,
                            class_group=class_group.name,
                            day=day,
                            hour=hour
                        )

                        # Dodaj lekcję do planu
                        added = schedule.add_lesson(lesson)
                        if added:
                            return True

            return False

        except Exception as e:
            self.logger.error(f"Błąd podczas dodawania podstawowej lekcji: {str(e)}")
            return False

    def generate(self, progress_callback=None):
        """Główna funkcja generująca plan"""
        self.logger.info("Starting schedule generation")

        try:
            # Sprawdzamy tylko, czy szkoła ma klasy
            if not self.school.class_groups:
                self.logger.error("No classes defined in school")
                raise ValueError("School has no classes defined")

            # Generowanie podstawowego planu
            basic_schedule = self._generate_basic_schedule()

            # Konwersja podstawowego planu do formatu osobnika
            basic_individual = self._convert_schedule_to_individual(basic_schedule)

            # Generowanie początkowej populacji
            population = self.population_manager.initialize_population(
                self.toolbox,
                self.params['population_size'],
                self.best_known_solution,
                basic_individual
            )

            self.population_manager.set_params(self.params)

            # Główna pętla ewolucyjna
            result = self.population_manager.evolve_population(
                population,
                self.toolbox,
                self.operators,
                self.params,
                progress_callback
            )

            best_schedule = self.operators.convert_to_schedule(result.best_individual)
            self._save_best_solution(result.best_individual, result.best_fitness)

            self.logger.info(
                f"Generation completed in {result.stats.total_time:.2f}s with "
                f"fitness: {result.best_fitness:.2f}"
            )

            return best_schedule, result.progress_history, result.stats

        except Exception as e:
            self.logger.error("Fatal error during schedule generation", exc_info=True)
            raise RuntimeError(f"Schedule generation failed: {str(e)}")

    def _convert_schedule_to_individual(self, schedule):
        """Konwertuje obiekt Schedule na format osobnika (chromosomu)"""
        individual = []

        for lesson in schedule.lessons:
            # Format: (day, hour, class_group, subject.name, teacher.id, classroom.id)
            lesson_tuple = (
                lesson.day,
                lesson.hour,
                lesson.class_group,
                lesson.subject.name,
                lesson.teacher.id,
                lesson.classroom.id
            )
            individual.append(lesson_tuple)

        # Uzupełnij do wymaganej długości
        required_lessons = self._calculate_total_lessons()
        if len(individual) < required_lessons:
            # Dodaj None dla brakujących lekcji
            individual.extend([None] * (required_lessons - len(individual)))

        return individual
