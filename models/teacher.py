# models/teacher.py
from dataclasses import dataclass, field
from typing import Dict, List, Set
from .lesson import Lesson


@dataclass
class Teacher:
    """Reprezentuje nauczyciela"""
    teacher_id: str
    subjects: Set[str]  # Przedmioty, których uczy
    available_days: Set[int]  # Dni tygodnia (0-4), w które jest dostępny
    is_full_time: bool  # Czy pracuje na pełny etat
    name: str  # Imię i nazwisko
    schedule: Dict[int, Dict[int, List[Lesson]]] = field(default_factory=lambda: {
        day: {hour: [] for hour in range(1, 10)}
        for day in range(5)
    })

    @classmethod
    def create_full_time(cls, teacher_id: str, subjects: Set[str], name: str) -> 'Teacher':
        """Tworzy nauczyciela na pełny etat"""
        return cls(
            teacher_id=teacher_id,
            subjects=subjects,
            available_days={0, 1, 2, 3, 4},  # Dostępny codziennie
            is_full_time=True,
            name=name
        )

    @classmethod
    def create_part_time(cls, teacher_id: str, subjects: Set[str], name: str, days_count: int) -> 'Teacher':
        """Tworzy nauczyciela na część etatu"""
        if days_count not in {2, 3}:
            raise ValueError("Nauczyciel na część etatu musi być dostępny 2 lub 3 dni")

        return cls(
            teacher_id=teacher_id,
            subjects=subjects,
            available_days=set(),  # Dni będą przydzielone później
            is_full_time=False,
            name=name
        )

    def validate_subjects(self) -> bool:
        """Sprawdza czy przedmioty są powiązane jeśli uczy więcej niż jednego"""
        if len(self.subjects) <= 1:
            return True

        related_pairs = [
            {'Matematyka', 'Fizyka'},
            {'Biologia', 'Chemia'}
            # Można dodać więcej par
        ]

        return any(self.subjects.issubset(pair) for pair in related_pairs)

    def set_available_days(self, days: Set[int]) -> bool:
        """Ustawia dni dostępności dla nauczyciela na część etatu"""
        if self.is_full_time:
            return False

        expected_days = 3 if len(self.available_days) == 3 else 2
        if len(days) != expected_days:
            return False

        if not all(0 <= day <= 4 for day in days):
            return False

        self.available_days = days
        return True

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do planu nauczyciela"""
        # Sprawdź czy nauczyciel jest dostępny tego dnia
        if lesson.day not in self.available_days:
            return False

        # Sprawdź czy przedmiot jest nauczany przez nauczyciela
        if lesson.subject not in self.subjects:
            return False

        # Sprawdź czy nie ma konfliktu z innymi lekcjami
        if self.schedule[lesson.day][lesson.hour]:
            return False

        self.schedule[lesson.day][lesson.hour].append(lesson)
        return True

    def remove_lesson(self, lesson: Lesson) -> bool:
        """Usuwa lekcję z planu"""
        try:
            self.schedule[lesson.day][lesson.hour].remove(lesson)
            return True
        except ValueError:
            return False

    def get_teaching_hours(self) -> int:
        """Zwraca liczbę godzin nauczanych w tygodniu"""
        return sum(
            1 for day in range(5)
            for hour in range(1, 10)
            if self.schedule[day][hour]
        )

    def validate_schedule(self) -> List[str]:
        """Sprawdza czy plan jest zgodny z zasadami"""
        errors = []

        # Sprawdź dostępność w dniach
        for day in range(5):
            if day not in self.available_days:
                lessons = sum(1 for hour in range(1, 10) if self.schedule[day][hour])
                if lessons > 0:
                    errors.append(f"Dzień {day}: zaplanowane lekcje w dzień niedostępności")

        # Sprawdź liczbę godzin
        total_hours = self.get_teaching_hours()
        if self.is_full_time:
            if total_hours < 18:  # Minimum dla pełnego etatu
                errors.append(f"Za mało godzin dla pełnego etatu ({total_hours}/18)")
        else:
            max_hours = 10 if len(self.available_days) == 2 else 15
            if total_hours > max_hours:
                errors.append(f"Za dużo godzin dla części etatu ({total_hours}/{max_hours})")

        return errors

    def to_dict(self) -> dict:
        """Konwertuje nauczyciela do słownika (np. dla szablonu HTML)"""
        return {
            'teacher_id': self.teacher_id,
            'name': self.name,
            'subjects': list(self.subjects),
            'is_full_time': self.is_full_time,
            'available_days': list(self.available_days),
            'schedule': {
                day: {
                    hour: [lesson.to_dict() for lesson in lessons]
                    for hour, lessons in hours.items()
                }
                for day, hours in self.schedule.items()
            },
            'teaching_hours': self.get_teaching_hours()
        }

    def is_available(self, day: int, hour: int) -> bool:
        """Sprawdza czy nauczyciel jest dostępny w danym terminie"""
        return day in self.available_days and not self.schedule[day][hour]