# src/genetic/creator.py
from typing import Any, Type

from deap import base, creator

from src.utils.logger import GPLLogger

logger = GPLLogger(__name__)


def create_base_types() -> None:
    """
    Tworzy podstawowe typy używane w algorytmie genetycznym.
    Dodatkowo sprawdza poprawność konfiguracji.
    """
    try:
        # Usuwamy poprzednie definicje, jeśli istnieją
        if hasattr(creator, 'FitnessMax'):
            del creator.FitnessMax
        if hasattr(creator, 'Individual'):
            del creator.Individual

        # Tworzymy typ fitness maksymalizujący (wagi dodatnie)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))

        # Sprawdź, czy typ został utworzony poprawnie
        if not hasattr(creator, 'FitnessMax'):
            raise RuntimeError("Failed to create FitnessMax type")

        # Sprawdź, czy wagi zostały ustawione poprawnie
        if not creator.FitnessMax.weights == (1.0,):
            raise ValueError(f"Invalid weights: {creator.FitnessMax.weights}")

        # Tworzymy typ osobnika dziedziczącego po liście
        creator.create("Individual", list, fitness=creator.FitnessMax)

        # Sprawdź, czy typ został utworzony poprawnie
        if not hasattr(creator, 'Individual'):
            raise RuntimeError("Failed to create Individual type")

        # Sprawdź, czy Individual dziedziczy po liście
        if not issubclass(creator.Individual, list):
            raise TypeError("Individual must inherit from list")

    except Exception as e:
        logger.error(f"Error creating base types: {str(e)}")
        raise RuntimeError(f"Failed to initialize genetic algorithm types: {str(e)}")


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
