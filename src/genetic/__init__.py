"""
Moduł implementujący algorytm genetyczny do generowania planu lekcji.
"""

# Wersja modułu
__version__ = '0.2.0'

# Najpierw importujemy komponenty bez zależności
from src.genetic.genetic_utils import GenerationStats
from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_evaluator import GeneticEvaluator
from src.genetic.genetic_population import PopulationManager
from src.genetic.genetic_generator import ScheduleGenerator

__all__ = [
    'GenerationStats',
    'GeneticOperators',
    'GeneticEvaluator',
    'PopulationManager',
    'ScheduleGenerator'
]