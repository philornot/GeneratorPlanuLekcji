# src/models/schedule.py
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set

from src.models.classroom import Classroom
from src.models.lesson import Lesson
from src.models.school import School
from src.models.teacher import Teacher
from src.utils.logger import GPLLogger

logger = GPLLogger(__name__)


@dataclass
class Schedule:
    lessons: List[Lesson] = field(default_factory=list)
    class_groups: Set[str] = field(default_factory=set)
    school: 'School' = None  # Dodajemy atrybut school

    def __init__(self, school: 'School' = None):
        self.lessons = []
        self.class_groups = set()
        self.school = school
        self.logger = GPLLogger(__name__)

    def get_class_lessons(self, class_name: str) -> List[Lesson]:
        """Zwraca wszystkie lekcje dla danej klasy"""
        return [lesson for lesson in self.lessons if lesson.class_group == class_name]

    def get_used_teachers(self) -> Set[Teacher]:
        """Zwraca zbiór wszystkich nauczycieli wykorzystanych w planie"""
        return {lesson.teacher for lesson in self.lessons}

    def get_class_hours(self, class_group: str) -> Dict[str, int]:
        """Zwraca liczbę godzin dla danej klasy z podziałem na przedmioty"""
        subject_hours = defaultdict(int)
        for lesson in self.get_class_lessons(class_group):
            subject_hours[lesson.subject.name] += 1
        return dict(subject_hours)

    def get_teacher_hours(self, teacher: Teacher) -> Dict[str, int]:
        """Zwraca liczbę godzin nauczyciela (dziennie i tygodniowo)"""
        daily_hours = defaultdict(int)
        weekly_total = 0
        for lesson in self.lessons:
            if lesson.teacher == teacher:
                daily_hours[lesson.day] += 1
                weekly_total += 1

        return {
            'daily': dict(daily_hours),
            'weekly': weekly_total
        }

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do planu, jeśli nie powoduje konfliktów"""
        if not isinstance(lesson, Lesson):
            logger.error(f"Próba dodania nieprawidłowej lekcji: {lesson}")
            return False

        if self.school is None:
            logger.error("Próba dodania lekcji do planu bez zainicjalizowanego obiektu school")
            return False

        if not self._check_conflicts(lesson):
            self.lessons.append(lesson)
            self.class_groups.add(lesson.class_group)
            return True

        return False

    @staticmethod
    def _conflict_reason(new_lesson: Lesson, existing_lesson: Lesson) -> str:
        """Zwraca powód konfliktu między lekcjami"""
        if new_lesson.day != existing_lesson.day or new_lesson.hour != existing_lesson.hour:
            return "Brak konfliktu - różne godziny"

        if new_lesson.teacher == existing_lesson.teacher:
            return f"Ten sam nauczyciel: {new_lesson.teacher.name}"

        if new_lesson.class_group == existing_lesson.class_group:
            return f"Ta sama klasa: {new_lesson.class_group}"

        if new_lesson.classroom == existing_lesson.classroom:
            return f"Ta sama sala: {new_lesson.classroom.name}"

        return "Nieznany konflikt"

    def _check_conflicts(self, new_lesson: Lesson) -> bool:
        """Sprawdza, czy nowa lekcja nie powoduje konfliktów"""
        day, hour = new_lesson.day, new_lesson.hour

        # Sprawdź tylko lekcje o tej samej godzinie
        for lesson in self.lessons:
            if lesson.day == day and lesson.hour == hour:
                if (lesson.teacher == new_lesson.teacher or
                        lesson.classroom == new_lesson.classroom or
                        lesson.class_group == new_lesson.class_group):
                    return True

        return False

    def to_dict(self) -> Dict:
        """Konwertuje plan do słownika do zapisu w JSON"""
        return {
            'lessons': [
                {
                    'day': lesson.day,
                    'hour': lesson.hour,
                    'subject': lesson.subject.name,
                    'teacher_id': lesson.teacher.id,
                    'classroom_id': lesson.classroom.id,
                    'class_group': lesson.class_group
                }
                for lesson in self.lessons
            ],
            'class_groups': list(self.class_groups),
            'metrics': {
                'total_lessons': len(self.lessons),
                'unique_teachers': len(self.get_used_teachers()),
                'class_count': len(self.class_groups)
            }
        }

    def get_all_teachers(self) -> Set[Teacher]:
        """Returns all teachers used in the schedule"""
        return self.get_used_teachers()  # Reuse existing method

    def get_all_classrooms(self) -> Set[Classroom]:
        """Returns all classrooms used in the schedule"""
        return {lesson.classroom for lesson in self.lessons}

    def get_classroom_usage(self, classroom: Classroom) -> float:
        """Calculates classroom usage percentage"""
        usage = sum(1 for lesson in self.lessons if lesson.classroom == classroom)
        total_slots = 40  # 8 hours * 5 days
        return (usage / total_slots) * 100
