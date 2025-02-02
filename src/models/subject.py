# src/models/subject.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Subject:
    id: int
    name: str
    hours_per_week: int
    requires_special_classroom: bool = False
    special_classroom_type: Optional[str] = None

    def __str__(self):
        return f"{self.name} ({self.hours_per_week}h/tydzień)"

    def __hash__(self):
        """Używamy id jako hash"""
        return hash(self.id)

    def __eq__(self, other):
        """Porównujemy przedmioty po id"""
        if not isinstance(other, Subject):
            return NotImplemented
        return self.id == other.id
