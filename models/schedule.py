# models/schedule.py
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
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

        # 1. Sprawdź czy wszystkie wymagane lekcje są przydzielone (-30 punktów)
        required_lessons = 0
        actual_lessons = len(self.lessons)
        for class_name, school_class in self.classes.items():
            required_lessons += school_class.required_hours

        if actual_lessons < required_lessons:
            lesson_penalty = 30 * (required_lessons - actual_lessons) / required_lessons
            score -= lesson_penalty

        # 2. Sprawdź konflikty (-20 punktów)
        conflicts = len(self.get_conflicts())
        if conflicts > 0:
            conflict_penalty = min(20, conflicts * 2)
            score -= conflict_penalty

        # 3. Sprawdź poprawność planów klas (-20 punktów)
        class_errors = 0
        for school_class in self.classes.values():
            class_errors += len(school_class.validate_schedule())
        if class_errors > 0:
            class_penalty = min(20, class_errors)
            score -= class_penalty

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