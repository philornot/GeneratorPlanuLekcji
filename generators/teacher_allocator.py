# generators/teacher_allocator.py
from typing import Dict, List, Set, Optional
from models.teacher import Teacher
from models.lesson import Lesson
from models.schedule import Schedule
from utils.logger import ScheduleLogger
import random


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

        # Próbuj przydzielić nauczycieli do wszystkich lekcji
        success = True
        for lesson in lessons:
            if not self._allocate_teacher_to_lesson(lesson, subject_teachers):
                self.logger.log_error(f"Nie można przydzielić nauczyciela do lekcji: {lesson.subject} "
                                      f"dla klasy {lesson.class_name}")
                success = False
                break

        if success:
            self.logger.log_info("Przydział nauczycieli zakończony sukcesem")
        else:
            self.logger.log_error("Nie udało się przydzielić wszystkich nauczycieli")

        return success

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

    def _allocate_teacher_to_lesson(self, lesson: Lesson, subject_teachers: Dict[str, List[Teacher]]) -> bool:
        if lesson.subject not in subject_teachers:
            self.logger.log_error(f"Brak nauczycieli dla przedmiotu: {lesson.subject}")
            return False

        def oblicz_punktacje_nauczyciela(nauczyciel: Teacher) -> float:
            obecne_godziny = nauczyciel.get_teaching_hours()
            docelowe_godziny = 18 if nauczyciel.is_full_time else 12
            return abs(docelowe_godziny - obecne_godziny)

        dostepni_nauczyciele = []
        for teacher in subject_teachers[lesson.subject]:
            if (lesson.day in teacher.available_days and
                    not teacher.schedule[lesson.day][lesson.hour]):
                hours = teacher.get_teaching_hours()
                max_hours = 18 if teacher.is_full_time else 12
                if hours < max_hours:
                    dostepni_nauczyciele.append(teacher)

        if not dostepni_nauczyciele:
            return False

        # Wybierz nauczyciela z punktacją najbliższą docelowej liczbie godzin
        wybrany_nauczyciel = min(dostepni_nauczyciele, key=oblicz_punktacje_nauczyciela)
        lesson.teacher_id = wybrany_nauczyciel.teacher_id
        wybrany_nauczyciel.add_lesson(lesson)

        return True

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