# src/genetic/genetic_population.py

import random
import time
from datetime import datetime
from typing import List, Dict, Optional

import numpy as np
from deap import creator, base
from deap import tools

from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_utils import GenerationStats, EvolutionResult, calculate_population_diversity
from src.models.school import School
from src.utils.logger import GPLLogger


def _should_stop(record: Dict, generation: int) -> bool:
    """Sprawdza, czy należy zatrzymać ewolucję"""
    # Zatrzymaj, jeśli osiągnięto bardzo dobry wynik
    if record['max'] >= 95:
        return True

    # Zatrzymaj, jeśli nie ma postępu przez wiele generacji
    if (generation > 20 and
            abs(record['max'] - record['avg']) < 0.1 and
            record['std'] < 0.1):
        return True

    return False


class PopulationManager:
    """Zarządza populacją i procesem ewolucji"""

    def __init__(self, school: School):
        self.school = school
        self.logger = GPLLogger(__name__)
        self.params = {}

        # Statystyki
        self.stats = tools.Statistics(lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

        # Hall of Fame — przechowuje najlepsze znalezione rozwiązania
        self.hall_of_fame = tools.HallOfFame(5)

    def set_params(self, params: Dict):
        """Ustawia parametry ewolucji"""
        self.params = params

    def initialize_population(
            self,
            toolbox: 'base.Toolbox',
            pop_size: int,
            best_known: Optional[List] = None
    ) -> List:
        """
        Inicjalizuje początkową populację.

        Args:
            toolbox: Toolbox z DEAP
            pop_size: Rozmiar populacji
            best_known: Najlepsze znane rozwiązanie (opcjonalne)

        Returns:
            Lista osobników początkowej populacji
        """
        try:
            self.logger.info(f"Initializing population of size {pop_size}")

            # Generuj populację
            population = toolbox.population(n=pop_size - 1 if best_known else pop_size)

            # Dodaj najlepsze znane rozwiązanie, jeśli istnieje
            if best_known:
                self.logger.info("Adding best known solution to initial population")
                population.append(creator.Individual(best_known))

            # Oceń początkową populację
            invalid_ind = [ind for ind in population if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            self.logger.info("Initial population evaluated")
            return population

        except Exception as e:
            self.logger.error(f"Error initializing population: {str(e)}")
            raise

    def evolve_population(
            self,
            population: List,
            toolbox: 'base.Toolbox',
            operators: 'GeneticOperators',
            params: Dict,
            progress_callback=None
    ) -> EvolutionResult:
        """
        Przeprowadza proces ewolucji populacji.

        Args:
            population: Początkowa populacja
            toolbox: Toolbox z DEAP
            operators: Operatory genetyczne
            params: Parametry algorytmu
            progress_callback: Funkcja do raportowania postępu

        Returns:
            EvolutionResult z wynikami ewolucji
        """
        try:
            generation_times = []
            progress_history = []
            start_time = time.time()

            # Parametry
            n_generations = params.get('iterations', 1000)

            # Główna pętla ewolucyjna
            for gen in range(n_generations):
                gen_start = time.time()

                # Aktualizacja współczynników adaptacyjnych
                diversity = calculate_population_diversity(population)
                operators.update_adaptive_rates(diversity)

                # Selekcja rodziców
                offspring = self._select_parents(population, toolbox)

                # Krzyżowanie
                offspring = self._apply_crossover(offspring, operators)

                # Mutacja
                offspring = self._apply_mutation(offspring, operators)

                # Ocena nowego pokolenia
                offspring = self._evaluate_offspring(offspring, toolbox)

                # Aktualizacja populacji
                population[:] = offspring

                # Aktualizacja hall of fame
                self.hall_of_fame.update(population)

                # Zbieranie statystyk
                record = self.stats.compile(population)
                gen_time = time.time() - gen_start
                generation_times.append(gen_time)

                # Zapisywanie postępu
                progress = self._record_progress(
                    gen, record, gen_time, progress_callback
                )
                progress_history.append(progress)

                # Sprawdzenie warunku zatrzymania
                if _should_stop(record, gen):
                    self.logger.info(
                        f"Stopping early at generation {gen} - achieved desired fitness"
                    )
                    break

            # Przygotowanie wyników
            total_time = time.time() - start_time
            stats = GenerationStats(
                total_time=total_time,
                avg_generation_time=np.mean(generation_times),
                min_generation_time=min(generation_times),
                max_generation_time=max(generation_times),
                total_generations=len(generation_times),
                best_fitness=self.hall_of_fame[0].fitness.values[0],
                avg_fitness=record['avg'],
                timestamp=datetime.now()
            )

            return EvolutionResult(
                best_individual=self.hall_of_fame[0],
                best_fitness=self.hall_of_fame[0].fitness.values[0],
                progress_history=progress_history,
                stats=stats
            )

        except Exception as e:
            self.logger.error(f"Error during evolution: {str(e)}")
            raise

    def _select_parents(self, population: List, toolbox: 'base.Toolbox') -> List:
        """Wybiera rodziców do następnego pokolenia"""
        try:
            offspring = toolbox.select(population, len(population))
            offspring = list(map(toolbox.clone, offspring))
            return offspring
        except Exception as e:
            self.logger.error(f"Error selecting parents: {str(e)}")
            raise

    def _apply_crossover(self, offspring: List, operators: 'GeneticOperators') -> List:
        """Aplikuje operator krzyżowania"""
        try:
            for i in range(1, len(offspring), 2):
                if random.random() < operators.adaptive_rates['crossover']['current']:
                    offspring[i - 1], offspring[i] = operators.crossover(
                        offspring[i - 1],
                        offspring[i]
                    )
                    del offspring[i - 1].fitness.values
                    del offspring[i].fitness.values
            return offspring
        except Exception as e:
            self.logger.error(f"Error applying crossover: {str(e)}")
            raise

    def _apply_mutation(self, offspring: List, operators: 'GeneticOperators') -> List:
        """Aplikuje operator mutacji"""
        try:
            for i in range(len(offspring)):
                if random.random() < operators.adaptive_rates['mutation']['current']:
                    offspring[i] = operators.mutation(offspring[i])
                    del offspring[i].fitness.values
            return offspring
        except Exception as e:
            self.logger.error(f"Error applying mutation: {str(e)}")
            raise

    def _evaluate_offspring(self, offspring: List, toolbox: 'base.Toolbox') -> List:
        """Ocenia nowe pokolenie"""
        try:
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            return offspring
        except Exception as e:
            self.logger.error(f"Error evaluating offspring: {str(e)}")
            raise

    def _record_progress(
            self,
            gen: int,
            record: Dict,
            gen_time: float,
            callback=None
    ) -> Dict:
        """Zapisuje postęp generacji"""
        progress = {
            'generation': gen,
            'best_fitness': record['max'],
            'avg_fitness': record['avg'],
            'std_fitness': record['std'],
            'min_fitness': record['min'],
            'generation_time': gen_time,
            'progress_percent': (gen + 1) / self.params['iterations'] * 100
        }

        if callback:
            callback(progress)

        self.logger.info(
            f"Gen {gen}: Best={record['max']:.2f}, "
            f"Avg={record['avg']:.2f}, "
            f"Time={gen_time:.4f}s"
        )

        return progress
