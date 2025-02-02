# src/models/subject.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Subject:
    id: int
    name: str
    hours_per_week: int  # wymagana liczba godzin tygodniowo
    requires_special_classroom: bool = False  # czy wymaga specjalnej sali
    special_classroom_type: Optional[str] = None  # typ wymaganej sali (np. "lab_fizyczne")

    def __str__(self):
        return f"{self.name} ({self.hours_per_week}h/tydzień)"