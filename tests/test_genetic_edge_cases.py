# tests/test_genetic_edge_cases.py
import pytest
from src.genetic.genetic_operators import GeneticOperators
from src.models.school import School


def test_mutation_with_none_elements():
    """Test obsługi None w operacji mutacji"""
    config = {
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

    school = School(config)
    operators = GeneticOperators(school)

    # Utwórz osobnika z elementem None
    individual_with_none = [None, (0, 1, "1A", "matematyka", 1, 1)]

    # Sprawdź, czy mutacja obsługuje poprawnie None
    result = operators.mutation(individual_with_none)
    # Test powinien przejść bez wyjątków
    assert result is not None

    # Dodatkowy test dla zupełnie pustej listy
    empty_individual = []
    result = operators.mutation(empty_individual)
    assert result is not None

    # Test dla osobnika zawierającego wyłącznie None
    none_individual = [None, None]
    result = operators.mutation(none_individual)
    assert result is not None