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

        # Sprawdź liczbę godzin dziennie
        for day in range(5):
            hours = self.get_day_hours(day)
            if len(hours) < 5:
                errors.append(f"Dzień {day}: za mało lekcji (minimum 5)")
            elif len(hours) > 8:
                errors.append(f"Dzień {day}: za dużo lekcji (maksimum 8)")

        # Sprawdź ciągłość zajęć (brak okienek)
        for day in range(5):
            hours = self.get_day_hours(day)
            if hours:
                for i in range(min(hours), max(hours)):
                    if i not in hours:
                        errors.append(f"Dzień {day}: okienko na lekcji {i}")

        # Sprawdź ograniczenia przedmiotów
        restricted_subjects = {'Matematyka', 'Fizyka'}
        for day in range(5):
            hours = self.get_day_hours(day)
            if hours:
                first_hour = min(hours)
                last_hour = max(hours)
                for subject in restricted_subjects:
                    for hour in [first_hour, last_hour]:
                        if any(l.subject == subject for l in self.schedule[day][hour]):
                            errors.append(
                                f"Dzień {day}: {subject} nie może być na "
                                f"{'pierwszej' if hour == first_hour else 'ostatniej'} lekcji"
                            )

        # Sprawdź maksymalną liczbę godzin pod rząd
        max_consecutive = {
            'Matematyka': 2,
            'Polski': 2,
            'Informatyka': 2,
            'Wychowanie fizyczne': 1
        }
        for day in range(5):
            for subject, max_hours in max_consecutive.items():
                consecutive = 0
                for hour in range(1, 10):
                    if any(l.subject == subject for l in self.schedule[day][hour]):
                        consecutive += 1
                        if consecutive > max_hours:
                            errors.append(
                                f"Dzień {day}: za dużo godzin {subject} pod rząd"
                            )
                    else:
                        consecutive = 0

        return errors
