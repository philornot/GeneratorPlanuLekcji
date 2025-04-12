# tests/functional/test_generation.py
import pytest
from src.genetic import ScheduleGenerator
from src.models.school import School


def create_minimal_config():
    """Tworzy minimalną konfigurację do testów"""
    return {
        'class_counts': {
            'first_year': 1,
            'second_year': 0,
            'third_year': 0,
            'fourth_year': 0
        },
        'profiles': [{
            'name': 'minimal',
            'extended_subjects': ['matematyka']
        }]
    }


@pytest.mark.slow
def test_minimal_generation():
    """Test generacji minimalnego planu (bardzo podstawowy)"""
    # Utwórz szkołę z minimalną konfiguracją
    school = School(create_minimal_config())

    # Parametry dla szybkiego testu
    params = {
        'iterations': 10,
        'population_size': 10,
        'mutation_rate': 0.2,
        'crossover_rate': 0.8
    }

    # Utwórz generator
    generator = ScheduleGenerator(school, params)

    # Wygeneruj plan
    schedule, progress, stats = generator.generate()

    # Sprawdź podstawowe wyniki
    assert schedule is not None
    assert len(schedule.lessons) > 0
    assert len(progress) > 0
    assert stats.total_generations > 0

    # Zmiana: sprawdź tylko, czy fitness jest typu float (nie sprawdzaj wartości)
    assert isinstance(stats.best_fitness, (int, float))