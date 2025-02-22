# src/models/teacher.py

from dataclasses import dataclass
from typing import List

from src.utils.logger import GPLLogger

logger = GPLLogger(__name__)


@dataclass
class Teacher:
    id: int
    name: str
    subjects: List[str]  # lista przedmiotów, które może uczyć
    max_hours_per_day: int = 8
    max_hours_per_week: int = 40

    def __post_init__(self):
        logger.debug(f"Created teacher: {self.name} with subjects: {self.subjects}")

    def can_teach(self, subject: str) -> bool:
        """Sprawdza czy nauczyciel może uczyć danego przedmiotu"""
        return subject in self.subjects

    def __hash__(self):
        """Używamy id jako hash, bo jest unikalne"""
        return hash(self.id)

    def __eq__(self, other):
        """Porównujemy nauczycieli po id"""
        if not isinstance(other, Teacher):
            return NotImplemented
        return self.id == other.id
