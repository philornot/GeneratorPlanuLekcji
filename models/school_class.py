# models/school_class.py
from dataclasses import dataclass, field
from typing import Dict, List

from .lesson import Lesson


@dataclass
class SchoolClass:
    """Reprezentuje klasę szkolną"""
    name: str  # np. "1A", "2B"
    year: int  # 1-4
    home_room: str  # sala wychowawcza
    class_teacher_id: str
    students_count: int = 30  # domyślnie 30 uczniów
    schedule: Dict[int, Dict[int, List[Lesson]]] = field(default_factory=lambda: {
        day: {hour: [] for hour in range(1, 10)}
        for day in range(5)
    })

    @property
    def required_hours(self) -> int:
        """Zwraca wymaganą liczbę godzin tygodniowo"""
        hours_per_year = {
            1: 31,
            2: 35,
            3: 31,
            4: 24
        }
        return hours_per_year[self.year]

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do planu klasy"""
        # Sprawdź czy nie ma konfliktu z innymi lekcjami
        for existing_lesson in self.schedule[lesson.day][lesson.hour]:
            if lesson.conflicts_with(existing_lesson):
                return False

        # Dodaj lekcję
        self.schedule[lesson.day][lesson.hour].append(lesson)
        return True

    def remove_lesson(self, lesson: Lesson) -> bool:
        """Usuwa lekcję z planu"""
        try:
            self.schedule[lesson.day][lesson.hour].remove(lesson)
            return True
        except ValueError:
            return False

    def get_day_hours(self, day: int) -> List[int]:
        """Zwraca godziny lekcyjne w danym dniu (bez religii)"""
        hours = []
        for hour in range(1, 10):
            lessons = [l for l in self.schedule[day][hour] if l.subject != 'Religia/Etyka']
            if lessons:
                hours.append(hour)
        return hours

    def get_subject_hours(self, subject: str) -> int:
        """Zlicza godziny danego przedmiotu w tygodniu"""
        count = 0
        for day in range(5):
            for hour in range(1, 10):
                for lesson in self.schedule[day][hour]:
                    if lesson.subject == subject:
                        count += 1
        return count

    def validate_schedule(self) -> List[str]:
        """Sprawdza czy plan jest zgodny z zasadami"""
        errors = []

        # Sprawdź ciągłość zajęć (brak okienek)
        for day in range(5):
            hours = sorted([
                hour for hour in range(1, 10)
                if self.schedule[day][hour] and
                   not any(l.subject == 'Religia/Etyka' for l in self.schedule[day][hour])
            ])

            if hours:  # Jeśli są jakieś lekcje w tym dniu
                first_hour = min(hours)
                last_hour = max(hours)

                # Sprawdź czy nie ma przerw między pierwszą a ostatnią lekcją
                for hour in range(first_hour, last_hour + 1):
                    if hour not in hours:
                        errors.append(f"Dzień {day}: znaleziono okienko na godzinie {hour}")

        return errors
