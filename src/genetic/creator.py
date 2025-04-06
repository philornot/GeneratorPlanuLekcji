# src/genetic/creator.py
from deap import base, creator, tools
from src.utils.logger import GPLLogger

logger = GPLLogger(__name__)

# Zmienne globalne do śledzenia stanu inicjalizacji
_initialized = False
_individual_class = None


def create_base_types() -> None:
    """
    Tworzy podstawowe typy używane w algorytmie genetycznym.
    Bezpieczne dla wielokrotnego wywołania.
    """
    global _initialized, _individual_class

    try:
        # Sprawdź, czy już zainicjalizowano
        if _initialized:
            return

        # Jeśli istnieją już te typy, usuń je
        if hasattr(creator, 'FitnessMax'):
            delattr(creator, 'FitnessMax')
        if hasattr(creator, 'Individual'):
            delattr(creator, 'Individual')

        # Tworzymy typy
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        # Zapisz referencję dla bezpieczeństwa
        _individual_class = creator.Individual
        _initialized = True

        logger.debug("Creator base types initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize creator base types: {str(e)}")
        raise


def get_individual_class():
    """Zwraca klasę Individual, inicjalizując jeśli potrzeba"""
    global _individual_class

    if not _initialized:
        create_base_types()

    if _individual_class is None:
        _individual_class = creator.Individual

    return _individual_class


# Inicjalizacja przy importowaniu
create_base_types()
