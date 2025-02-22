# src/genetic/creator.py
from deap import base, creator
from typing import Any, Type


def create_base_types() -> None:
    """
    Tworzy podstawowe typy używane w algorytmie genetycznym.
    Usuwa poprzednie definicje, jeśli istnieją i tworzy nowe.
    """
    # Usuwamy poprzednie definicje, jeśli istnieją
    if hasattr(creator, 'FitnessMax'):
        del creator.FitnessMax
    if hasattr(creator, 'Individual'):
        del creator.Individual

    # Tworzymy typ fitness maksymalizujący (wagi dodatnie)
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))

    # Tworzymy typ osobnika dziedziczącego po liście
    creator.create("Individual", list, fitness=creator.FitnessMax)


def get_fitness_class() -> Type[Any]:
    """Zwraca klasę FitnessMax"""
    if not hasattr(creator, 'FitnessMax'):
        create_base_types()
    return creator.FitnessMax


def get_individual_class() -> Type[Any]:
    """Zwraca klasę Individual"""
    if not hasattr(creator, 'Individual'):
        create_base_types()
    return creator.Individual


# Wywołujemy create_base_types przy importowaniu modułu
create_base_types()
