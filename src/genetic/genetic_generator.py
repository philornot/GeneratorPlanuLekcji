# src/algorithms/genetic_generator.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from deap import base, tools, creator

from src.genetic.genetic_evaluator import GeneticEvaluator
from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_population import PopulationManager
from src.genetic.genetic_utils import GenerationStats
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
        self.evaluator = GeneticEvaluator(school, params)
        self.operators = GeneticOperators(school)
        self.population_manager = PopulationManager(school)

        # Inicjalizacja DEAP
        self._setup_deap()

        # Wczytanie najlepszego znanego rozwiązania
        self.best_known_solution = self._load_best_solution()

    def _setup_deap(self):
        """Konfiguracja biblioteki DEAP"""
        try:
            self.logger.debug("Initializing DEAP toolbox")

            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            creator.create("Individual", list, fitness=creator.FitnessMax)

            self.toolbox = base.Toolbox()

            # Rejestracja funkcji
            self.toolbox.register(
                "lesson_slot",
                self.operators.random_lesson_slot
            )
            self.toolbox.register(
                "individual",
                tools.initRepeat,
                creator.Individual,
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

    def generate(self, progress_callback=None) -> Tuple[Schedule, List[Dict], GenerationStats]:
        """Główna funkcja generująca plan"""
        self.logger.info("Starting schedule generation")

        try:
            # Sprawdzamy tylko, czy szkoła ma klasy
            if not self.school.class_groups:
                self.logger.error("No classes defined in school")
                raise ValueError("School has no classes defined")

            # Generowanie początkowej populacji
            population = self.population_manager.initialize_population(
                self.toolbox,
                self.params['population_size'],
                self.best_known_solution
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
