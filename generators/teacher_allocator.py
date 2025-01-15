# generators/teacher_allocator.py
import random
from typing import Dict, List, Optional

from models.lesson import Lesson
from models.schedule import Schedule
from models.teacher import Teacher
from utils.logger import ScheduleLogger


class TeacherAllocator:
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.logger = ScheduleLogger()

    def allocate_teachers(self) -> bool:
        """Główna metoda przydzielająca nauczycieli do lekcji"""
        self.logger.log_info("Rozpoczynanie przydziału nauczycieli")

        # Przygotuj mapę dostępnych nauczycieli per przedmiot
        subject_teachers = self._get_subject_teachers()

        # Sortuj lekcje według trudności przydzielenia (najpierw najtrudniejsze)
        lessons = self._sort_lessons_by_difficulty()

        # Nowa lista lekcji z przypisanymi nauczycielami
        updated_lessons = []

        for lesson in lessons:
            new_lesson = self._allocate_teacher_to_lesson(lesson, subject_teachers)
            if new_lesson:
                updated_lessons.append(new_lesson)
            else:
                self.logger.log_error(f"Nie można przydzielić nauczyciela do lekcji: {lesson}")
                return False

        # Użyj nowej metody update_lessons
        self.schedule.update_lessons(updated_lessons)

        self.logger.log_info("Przydział nauczycieli zakończony sukcesem")

        return True

    def _get_subject_teachers(self) -> Dict[str, List[Teacher]]:
        """Tworzy mapę przedmiotów do nauczycieli, którzy mogą je uczyć"""
        subject_teachers = {}
        for teacher in self.schedule.teachers.values():
            for subject in teacher.subjects:
                if subject not in subject_teachers:
                    subject_teachers[subject] = []
                subject_teachers[subject].append(teacher)
        return subject_teachers

    def _sort_lessons_by_difficulty(self) -> List[Lesson]:
        """Sortuje lekcje według trudności przydzielenia nauczyciela"""
        lessons = list(self.schedule.lessons)

        def get_difficulty(lesson: Lesson) -> float:
            # Czynniki zwiększające trudność:
            # 1. Mniej nauczycieli danego przedmiotu
            # 2. Więcej zajętych godzin w danym terminie
            # 3. Przedmioty wymagające specjalnych kwalifikacji

            teacher_count = len([t for t in self.schedule.teachers.values()
                                 if lesson.subject in t.subjects])

            time_conflicts = sum(1 for l in self.schedule.lessons
                                 if l.day == lesson.day and l.hour == lesson.hour)

            special_subjects = {'Informatyka', 'WF', 'Angielski'}
            special_modifier = 1.5 if lesson.subject in special_subjects else 1.0

            return (1.0 / teacher_count) * time_conflicts * special_modifier

        lessons.sort(key=get_difficulty, reverse=True)
        return lessons

    @staticmethod
    def _allocate_teacher_to_lesson(lesson: Lesson, subject_teachers: Dict[str, List[Teacher]]) -> Optional[
        Lesson]:
        if lesson.subject not in subject_teachers:
            return None

        available_teachers = []
        for teacher in subject_teachers[lesson.subject]:
            if (lesson.day in teacher.available_days or
                    len([d for d in teacher.available_days if abs(d - lesson.day) <= 1]) > 0):

                current_hours = teacher.get_teaching_hours()
                max_hours = 20 if teacher.is_full_time else 15

                if current_hours < max_hours:
                    available_teachers.append((teacher, current_hours))

        if not available_teachers:
            return None

        available_teachers.sort(key=lambda x: x[1])
        chosen_teacher = random.choice(available_teachers[:3])[0]

        # Tworzenie nowej lekcji z przypisanym nauczycielem
        new_lesson = Lesson(
            subject=lesson.subject,
            teacher_id=chosen_teacher.teacher_id,
            room_id=lesson.room_id,
            day=lesson.day,
            hour=lesson.hour,
            class_name=lesson.class_name
        )

        chosen_teacher.add_lesson(new_lesson)
        return new_lesson

    def validate_allocation(self) -> List[str]:
        """Sprawdza poprawność przydziału nauczycieli"""
        errors = []

        # Sprawdź czy wszystkie lekcje mają przydzielonych nauczycieli
        for lesson in self.schedule.lessons:
            if not lesson.teacher_id:
                errors.append(f"Lekcja bez nauczyciela: {lesson.subject} dla {lesson.class_name}")

        # Sprawdź limity godzin nauczycieli
        for teacher in self.schedule.teachers.values():
            hours = teacher.get_teaching_hours()
            max_hours = 18 if teacher.is_full_time else 12

            if hours > max_hours:
                errors.append(f"Nauczyciel {teacher.name} ma za dużo godzin: {hours}/{max_hours}")
            elif teacher.is_full_time and hours < 18:
                errors.append(f"Nauczyciel {teacher.name} ma za mało godzin: {hours}/18")

        # Sprawdź czy nie ma konfliktów w planie nauczycieli
        for teacher in self.schedule.teachers.values():
            for day in range(5):
                for hour in range(1, 10):
                    lessons = [l for l in teacher.schedule[day][hour]]
                    if len(lessons) > 1:
                        errors.append(f"Nauczyciel {teacher.name} ma konflikt w dniu {day}, "
                                      f"godzina {hour}")

        return errors