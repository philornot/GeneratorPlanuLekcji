# tests/test_genetic.py
import pytest
from src.genetic.genetic_utils import calculate_population_diversity, GenerationStats
from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_evaluator import GeneticEvaluator
from datetime import datetime


def test_generation_stats():
    """Test statystyk generacji"""
    stats = GenerationStats(
        total_time=120.5,
        avg_generation_time=0.5,
        min_generation_time=0.2,
        max_generation_time=0.8,
        total_generations=100,
        best_fitness=95.5,
        avg_fitness=80.2,
        timestamp=datetime.now()
    )

    # Test konwersji do słownika i z powrotem
    stats_dict = stats.to_dict()
    assert isinstance(stats_dict, dict)

    restored_stats = GenerationStats.from_dict(stats_dict)
    assert restored_stats.total_time == stats.total_time
    assert restored_stats.avg_generation_time == stats.avg_generation_time
    assert restored_stats.best_fitness == stats.best_fitness


def test_calculate_population_diversity():
    """Test obliczania różnorodności populacji"""
    # Pusta populacja
    assert calculate_population_diversity([]) == 0.0

    # Identyczne osobniki
    identical_population = [
        [(0, 1, "1A", "matematyka", 1, 1)],
        [(0, 1, "1A", "matematyka", 1, 1)]
    ]
    assert calculate_population_diversity(identical_population) == 0.5  # 1 unikalny / 2

    # Różne osobniki
    diverse_population = [
        [(0, 1, "1A", "matematyka", 1, 1)],
        [(0, 2, "1A", "matematyka", 1, 1)],
        [(0, 3, "1A", "matematyka", 1, 1)]
    ]
    assert calculate_population_diversity(diverse_population) == 1.0  # 3 unikalne / 3


def test_genetic_operators(simple_school):
    """Test operatorów genetycznych"""
    operators = GeneticOperators(simple_school)

    # Test dostosowania współczynników adaptacyjnych
    initial_mutation_rate = operators.adaptive_rates['mutation']['current']
    initial_crossover_rate = operators.adaptive_rates['crossover']['current']

    # Niski stopień różnorodności powinien zwiększyć mutację
    operators.update_adaptive_rates(0.1)
    assert operators.adaptive_rates['mutation']['current'] > initial_mutation_rate

    # Wysoki stopień różnorodności powinien zmniejszyć mutację
    operators.adaptive_rates['mutation']['current'] = initial_mutation_rate  # reset
    operators.update_adaptive_rates(0.9)
    assert operators.adaptive_rates['mutation']['current'] < initial_mutation_rate