# models/school_class.py
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
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
            1: 25,
            2: 32,
            3: 35,
            4: 28
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
            lessons = [l for l in self.schedule[day][hour] if l.subject != 'Religia']
            if lessons:
                hours.append(hour)
        return hours

    def get_group_hours(self, day: int, group: Optional[int]) -> List[int]:
        """Zwraca godziny lekcyjne dla danej grupy w danym dniu"""
        hours = []
        for hour in range(1, 10):
            for lesson in self.schedule[day][hour]:
                if lesson.group == group or lesson.group is None:
                    hours.append(hour)
                    break
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

        # Sprawdź ciągłość zajęć dla każdej grupy
        for day in range(5):
            for group in [1, 2]:
                hours = self.get_group_hours(day, group)
                if hours:
                    for i in range(min(hours), max(hours)):
                        if i not in hours:
                            errors.append(f"Dzień {day}, grupa {group}: okienko na lekcji {i}")

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
            'WF': 1
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

    def calculate_schedule_score(self) -> float:
        """Oblicza punktację dla planu lekcji (0-100)"""
        score = 100.0

        # Kary za rozpoczynanie/kończenie o nieergonomicznych godzinach
        for day in range(5):
            hours = self.get_day_hours(day)
            if hours:
                if min(hours) == 1:  # Rozpoczęcie o 8:00
                    score -= 2
                if max(hours) >= 8:  # Kończenie po 14:40
                    score -= 3 * (max(hours) - 7)

        # Kary za nierównomierne rozłożenie "ciężkich" przedmiotów
        heavy_subjects = {'Matematyka', 'Fizyka', 'Chemia'}
        for day in range(5):
            heavy_count = sum(
                1 for hour in range(1, 10)
                for lesson in self.schedule[day][hour]
                if lesson.subject in heavy_subjects
            )
            if heavy_count > 2:
                score -= (heavy_count - 2) * 5

        return max(0, score)

    def to_dict(self) -> dict:
        """Konwertuje klasę do słownika (np. dla szablonu HTML)"""
        return {
            'name': self.name,
            'year': self.year,
            'home_room': self.home_room,
            'class_teacher_id': self.class_teacher_id,
            'students_count': self.students_count,
            'schedule': {
                day: {
                    hour: [lesson.to_dict() for lesson in lessons]
                    for hour, lessons in hours.items()
                }
                for day, hours in self.schedule.items()
            },
            'score': self.calculate_schedule_score()
        }