# models/schedule.py
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple

from config import REGULAR_SUBJECTS, WEEKLY_HOURS
from .lesson import Lesson
from .classroom import Classroom
from .school_class import SchoolClass
from .teacher import Teacher


@dataclass
class Schedule:
    """Reprezentuje cały plan lekcji szkoły"""
    classes: Dict[str, SchoolClass] = field(default_factory=dict)
    teachers: Dict[str, Teacher] = field(default_factory=dict)
    classrooms: Dict[str, Classroom] = field(default_factory=dict)
    lessons: List[Lesson] = field(default_factory=list)

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do planu"""
        # Sprawdź czy wszystkie wymagane komponenty istnieją
        if (lesson.class_name not in self.classes or
                lesson.teacher_id not in self.teachers or
                lesson.room_id not in self.classrooms):
            return False

        school_class = self.classes[lesson.class_name]
        teacher = self.teachers[lesson.teacher_id]
        classroom = self.classrooms[lesson.room_id]

        # Próba dodania lekcji do wszystkich komponentów
        if (school_class.add_lesson(lesson) and
                teacher.add_lesson(lesson) and
                classroom.add_lesson(lesson)):
            self.lessons.append(lesson)
            return True

        # Jeśli nie udało się dodać do któregoś komponentu, cofnij zmiany
        school_class.remove_lesson(lesson)
        teacher.remove_lesson(lesson)
        classroom.remove_lesson(lesson)
        return False

    def remove_lesson(self, lesson: Lesson) -> bool:
        """Usuwa lekcję z planu"""
        if lesson not in self.lessons:
            return False

        # Usuń lekcję ze wszystkich komponentów
        self.classes[lesson.class_name].remove_lesson(lesson)
        self.teachers[lesson.teacher_id].remove_lesson(lesson)
        self.classrooms[lesson.room_id].remove_lesson(lesson)
        self.lessons.remove(lesson)
        return True

    def get_conflicts(self) -> List[Tuple[Lesson, Lesson]]:
        """Znajduje konflikty między lekcjami"""
        conflicts = []
        for i, lesson1 in enumerate(self.lessons):
            for lesson2 in self.lessons[i + 1:]:
                if lesson1.conflicts_with(lesson2):
                    conflicts.append((lesson1, lesson2))
        return conflicts

    def validate_schedule(self) -> Dict[str, List[str]]:
        """Sprawdza poprawność całego planu"""
        errors = {}

        # Sprawdź plan każdej klasy
        for class_name, school_class in self.classes.items():
            class_errors = school_class.validate_schedule()
            if class_errors:
                errors[f"Klasa {class_name}"] = class_errors

        # Sprawdź plan każdego nauczyciela
        for teacher_id, teacher in self.teachers.items():
            teacher_errors = teacher.validate_schedule()
            if teacher_errors:
                errors[f"Nauczyciel {teacher_id}"] = teacher_errors

        # Sprawdź konflikty
        conflicts = self.get_conflicts()
        if conflicts:
            errors["Konflikty"] = [
                f"Konflikt: {l1.subject} ({l1.class_name}) i {l2.subject} ({l2.class_name})"
                for l1, l2 in conflicts
            ]

        return errors

    def calculate_schedule_score(self) -> float:
        """Oblicza ogólną ocenę planu (0-100)"""
        if not self.classes:
            return 0

        # Podstawowy wynik startowy
        score = 100.0

        # 1. Sprawdź zgodność z WEEKLY_HOURS (-40 punktów)
        for class_name, school_class in self.classes.items():
            required_hours = WEEKLY_HOURS[school_class.year]
            actual_hours = sum(1 for day in range(5) for hour in range(1, 10)
                               if school_class.schedule[day][hour])
            if actual_hours != required_hours:
                score -= 40 * abs(actual_hours - required_hours) / required_hours

        # 2. Sprawdź ciągłość (-30 punktów)
        for class_name, school_class in self.classes.items():
            for day in range(5):
                hours = sorted([hour for hour in range(1, 10)
                                if school_class.schedule[day][hour]])
                if hours:
                    for i in range(min(hours), max(hours)):
                        if i not in hours:
                            score -= 30

        # 3. Sprawdź zgodność z REGULAR_SUBJECTS (-20 punktów)
        for class_name, school_class in self.classes.items():
            year = school_class.year
            for subject, hours in REGULAR_SUBJECTS.items():
                required = hours[year]
                actual = sum(1 for day in range(5) for hour in range(1, 10)
                             for lesson in school_class.schedule[day][hour]
                             if lesson.subject == subject)
                if actual != required:
                    score -= 20 * abs(actual - required) / required

        # 4. Sprawdź obciążenie nauczycieli (-15 punktów)
        teacher_loads = [
            teacher.get_teaching_hours()
            for teacher in self.teachers.values()
        ]
        if teacher_loads:
            max_load = max(teacher_loads)
            min_load = min(teacher_loads)
            if max_load - min_load > 4:  # Dopuszczamy 4 godziny różnicy
                load_penalty = min(15, (max_load - min_load - 4) * 2)
                score -= load_penalty

        # 5. Sprawdź wykorzystanie sal (-15 punktów)
        room_usage = []
        for classroom in self.classrooms.values():
            for day in range(5):
                occupancy = classroom.get_occupancy(day)
                room_usage.append(occupancy)
        if room_usage:
            avg_usage = sum(room_usage) / len(room_usage)
            if avg_usage < 60:  # Oczekujemy minimum 60% wykorzystania
                usage_penalty = min(15, int((60 - avg_usage) / 4))
                score -= usage_penalty

        # 6. Nowa sekcja: Sprawdź okienka (-20 punktów)
        total_gaps = 0
        for class_name, school_class in self.classes.items():
            for day in range(5):
                hours = sorted([
                    hour for hour in range(1, 10)
                    if school_class.schedule[day][hour] and
                       not any(l.subject == 'Religia/Etyka' for l in school_class.schedule[day][hour])
                ])

                if hours:  # Jeśli są jakieś lekcje w tym dniu
                    first_hour = min(hours)
                    last_hour = max(hours)

                    # Policz okienka między pierwszą a ostatnią lekcją
                    for hour in range(first_hour, last_hour):
                        if hour not in hours:
                            total_gaps += 1

        if total_gaps > 0:
            gaps_penalty = min(20, total_gaps * 2)  # Maksymalnie 20 punktów kary
            score -= gaps_penalty

        return float(max(0.0, score))

    def get_available_slots(self,
                            class_name: str,
                            subject: str,
                            group: Optional[int] = None) -> List[Tuple[int, int]]:
        """Znajduje dostępne terminy dla lekcji"""
        available_slots = []
        school_class = self.classes[class_name]

        for day in range(5):
            for hour in range(1, 10):
                # Sprawdź czy termin jest wolny dla klasy
                is_available = True
                for existing_lesson in school_class.schedule[day][hour]:
                    if group is None or existing_lesson.group is None:
                        is_available = False
                        break
                    if existing_lesson.group == group:
                        is_available = False
                        break

                if is_available:
                    available_slots.append((day, hour))

        return available_slots

    def to_dict(self) -> dict:
        """Konwertuje plan do słownika (np. dla szablonu HTML)"""
        return {
            'classes': {
                name: school_class.to_dict()
                for name, school_class in self.classes.items()
            },
            'teachers': {
                teacher_id: teacher.to_dict()
                for teacher_id, teacher in self.teachers.items()
            },
            'classrooms': {
                room_id: classroom.to_dict()
                for room_id, classroom in self.classrooms.items()
            },
            'score': self.calculate_schedule_score(),
            'conflicts': len(self.get_conflicts())
        }