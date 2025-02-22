"""
Moduł implementujący algorytm genetyczny do generowania planu lekcji.

Moduł zawiera komponenty:
- ScheduleGenerator: Główna klasa generatora planu
- GeneticOperators: Operatory genetyczne (krzyżowanie, mutacja)
- GeneticEvaluator: Ocena rozwiązań
- PopulationManager: Zarządzanie populacją i ewolucją
- GenerationStats: Statystyki procesu generowania

Przykład użycia:
    from src.genetic import ScheduleGenerator

    generator = ScheduleGenerator(school, params)
    schedule, history, stats = generator.generate()
"""
from src.genetic.genetic_evaluator import GeneticEvaluator
from src.genetic.genetic_generator import ScheduleGenerator
from src.genetic.genetic_operators import GeneticOperators
from src.genetic.genetic_population import PopulationManager
from src.genetic.genetic_utils import GenerationStats

__all__ = [
    'ScheduleGenerator',
    'GeneticOperators',
    'GeneticEvaluator',
    'PopulationManager',
    'GenerationStats'
]

# Wersja modułu
__version__ = '0.2.0'
