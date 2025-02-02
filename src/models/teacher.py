# src/models/teacher.py

from dataclasses import dataclass
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


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