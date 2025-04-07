# src/genetic/genetic_utils.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class GenerationStats:
    """Statystyki procesu generowania planu"""
    total_time: float  # Całkowity czas w sekundach
    avg_generation_time: float  # Średni czas na generację
    min_generation_time: float  # Najkrótszy czas generacji
    max_generation_time: float  # Najdłuższy czas generacji
    total_generations: int  # Liczba wykonanych generacji
    best_fitness: float  # Najlepszy znaleziony wynik
    avg_fitness: float  # Średni wynik końcowej populacji
    timestamp: datetime  # Czas zakończenia generowania

    def to_dict(self) -> Dict:
        """Konwertuje statystyki do słownika"""
        return {
            'total_time': self.total_time,
            'avg_generation_time': self.avg_generation_time,
            'min_generation_time': self.min_generation_time,
            'max_generation_time': self.max_generation_time,
            'total_generations': self.total_generations,
            'best_fitness': self.best_fitness,
            'avg_fitness': self.avg_fitness,
            'timestamp': self.timestamp.isoformat()
        }

    @staticmethod
    def from_dict(data: Dict) -> 'GenerationStats':
        """Tworzy obiekt z słownika"""
        return GenerationStats(
            total_time=data['total_time'],
            avg_generation_time=data['avg_generation_time'],
            min_generation_time=data['min_generation_time'],
            max_generation_time=data['max_generation_time'],
            total_generations=data['total_generations'],
            best_fitness=data['best_fitness'],
            avg_fitness=data['avg_fitness'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class GenerationResult:
    """Wynik pojedynczej generacji"""
    best_individual: List  # Najlepszy osobnik
    best_fitness: float  # Jego ocena
    avg_fitness: float  # Średnia ocena populacji
    generation: int  # Numer generacji
    time: float  # Czas generacji w sekundach


@dataclass
class EvolutionResult:
    """Kompletny wynik ewolucji"""
    best_individual: List  # Najlepsze znalezione rozwiązanie
    best_fitness: float  # Jego ocena
    progress_history: List[Dict]  # Historia postępu
    stats: GenerationStats  # Statystyki końcowe


def calculate_population_diversity(population: List) -> float:
    """
    Oblicza różnorodność populacji.

    Args:
        population: Lista osobników

    Returns:
        float: Wartość 0-1, gdzie 1 oznacza maksymalną różnorodność
    """
    if not population:
        return 0.0

    # Zamieniamy każdy element osobnika na tuple, żeby był hashowalny
    unique_individuals = set()

    for ind in population:
        if ind is None:
            continue

        # Bezpieczne tworzenie tupli z osobnika, obsługując None
        try:
            ind_tuple = tuple(
                tuple(lesson) if lesson is not None else None
                for lesson in ind
            )
            unique_individuals.add(ind_tuple)
        except TypeError:
            # Jeśli wystąpi błąd podczas tworzenia tuple, pomiń tego osobnika
            continue

    return len(unique_individuals) / len(population) if population else 0.0


def format_time(seconds: float) -> str:
    """
    Formatuje czas w sekundach do czytelnej postaci.

    Args:
        seconds: Liczba sekund

    Returns:
        str: Sformatowany czas, np. "1h 23m 45s"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs:.1f}s")

    return " ".join(parts)