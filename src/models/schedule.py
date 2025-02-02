# src/models/schedule.py

from dataclasses import dataclass, field
from typing import List, Dict, Set
from collections import defaultdict
import json

from src.models.lesson import Lesson
from src.models.teacher import Teacher


@dataclass
class Schedule:
    lessons: List[Lesson] = field(default_factory=list)
    class_groups: Set[str] = field(default_factory=set)

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do planu jeśli nie powoduje konfliktów"""
        if not self._check_conflicts(lesson):
            self.lessons.append(lesson)
            self.class_groups.add(lesson.class_group)
            return True
        return False

    def _check_conflicts(self, new_lesson: Lesson) -> bool:
        """Sprawdza czy nowa lekcja nie powoduje konfliktów"""
        return any(new_lesson.conflicts_with(lesson) for lesson in self.lessons)

    def get_teacher_hours(self, teacher: Teacher) -> Dict[str, int]:
        """Zwraca liczbę godzin nauczyciela (dziennie i tygodniowo)"""
        daily_hours = defaultdict(int)
        for lesson in self.lessons:
            if lesson.teacher == teacher:
                daily_hours[lesson.day] += 1

        return {
            'daily': dict(daily_hours),
            'weekly': sum(daily_hours.values())
        }

    def get_class_hours(self, class_group: str) -> Dict[str, int]:
        """Zwraca liczbę godzin dla danej klasy z podziałem na przedmioty"""
        subject_hours = defaultdict(int)
        for lesson in self.lessons:
            if lesson.class_group == class_group:
                subject_hours[lesson.subject.name] += 1
        return dict(subject_hours)

    def to_dict(self) -> dict:
        """Konwertuje plan do formatu JSON"""
        return {
            'lessons': [
                {
                    'subject': lesson.subject.name,
                    'teacher': lesson.teacher.name,
                    'classroom': lesson.classroom.name,
                    'class_group': lesson.class_group,
                    'day': lesson.day,
                    'hour': lesson.hour
                }
                for lesson in self.lessons
            ]
        }