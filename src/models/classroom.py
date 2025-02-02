# src/models/classroom.py

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Classroom:
    id: int
    name: str
    capacity: int
    room_type: str = "regular"  # regular, lab_fizyczne, lab_chemiczne, sala_komputerowa, etc.
    equipment: List[str] = None  # lista dostępnego wyposażenia

    def __post_init__(self):
        if self.equipment is None:
            self.equipment = []

    def is_suitable_for_subject(self, subject: 'Subject') -> bool:
        """Sprawdza czy sala jest odpowiednia dla danego przedmiotu"""
        if not subject.requires_special_classroom:
            return True
        return subject.special_classroom_type == self.room_type