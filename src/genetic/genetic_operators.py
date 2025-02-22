# src/algorithms/genetic/genetic_operators.py

import random
from collections import defaultdict
from typing import List, Tuple, Optional

from deap import creator

from src.models.lesson import Lesson
from src.models.schedule import Schedule
from src.models.school import School
from src.utils.logger import GPLLogger


class GeneticOperators:
    def __init__(self, school: School):
        self.school = school
        self.logger = GPLLogger(__name__)

        self.DAYS = 5
        self.HOURS_PER_DAY = 8

        # Parametry adaptacyjne
        self.adaptive_rates = {
            'mutation': {
                'min_rate': 0.05,
                'max_rate': 0.4,
                'current': 0.2
            },
            'crossover': {
                'min_rate': 0.7,
                'max_rate': 0.95,
                'current': 0.85
            }
        }

    def random_lesson_slot(self) -> Tuple[int, int, str, str, int, int]:
        """
        Generuje losowy slot lekcyjny.

        Returns:
            Tuple zawierający (dzień, godzina, klasa, przedmiot, id_nauczyciela, id_sali)

        Raises:
            ValueError: Gdy nie udało się wygenerować poprawnego slotu
        """
        max_attempts = 50

        for attempt in range(max_attempts):
            try:
                day = random.randint(0, self.DAYS - 1)
                hour = random.randint(0, self.HOURS_PER_DAY - 1)

                class_group = random.choice(self.school.class_groups)
                subject = random.choice(class_group.subjects)

                available_teachers = [
                    t for t in self.school.teachers.values()
                    if subject.name in t.subjects
                ]
                suitable_rooms = [
                    r for r in self.school.classrooms.values()
                    if r.is_suitable_for_subject(subject)
                ]

                if not available_teachers or not suitable_rooms:
                    continue

                teacher = random.choice(available_teachers)
                classroom = random.choice(suitable_rooms)

                return day, hour, class_group.name, subject.name, teacher.id, classroom.id

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}",
                    cache_key=f"random_slot_attempt_{attempt}"
                )

        raise ValueError(f"Failed to generate valid lesson slot after {max_attempts} attempts")

    def crossover(self, ind1: List, ind2: List) -> Tuple[List, List]:
        """
        Operator krzyżowania wykorzystujący segmenty bez konfliktów.

        Args:
            ind1: Pierwszy rodzic
            ind2: Drugi rodzic

        Returns:
            Tuple zawierająca dwójkę potomków
        """
        try:
            # Znajdź dobre segmenty
            good_segments1 = self._find_good_segments(ind1)
            good_segments2 = self._find_good_segments(ind2)

            child1 = creator.Individual(ind1.copy())
            child2 = creator.Individual(ind2.copy())

            # Wymiana segmentów
            for (start1, end1), (start2, end2) in zip(good_segments1, good_segments2):
                if random.random() < self.adaptive_rates['crossover']['current']:
                    temp = child1[start1:end1]
                    child1[start1:end1] = child2[start2:end2]
                    child2[start2:end2] = temp

            return child1, child2

        except Exception as e:
            self.logger.error(f"Crossover failed: {str(e)}")
            return ind1, ind2

    def mutation(self, individual: List) -> List:
        """
        Operator mutacji z inteligentnym wypełnianiem dziur.

        Args:
            individual: Osobnik do mutacji

        Returns:
            Zmutowany osobnik
        """
        try:
            mutant = creator.Individual(individual[:])

            # Wypełnianie dziur
            schedule = self.convert_to_schedule(mutant)
            empty_slots = self._find_empty_slots(schedule)

            if empty_slots and random.random() < 0.7:
                # Próbujemy wypełnić do 3 losowych dziur
                for slot in random.sample(empty_slots, min(len(empty_slots), 3)):
                    new_lesson = self._generate_filling_lesson(*slot)
                    if new_lesson:
                        self._replace_or_add_lesson(mutant, slot, new_lesson)

            # Standardowa mutacja
            mutation_points = self._select_mutation_points(mutant)
            for i in mutation_points:
                if random.random() < self.adaptive_rates['mutation']['current']:
                    try:
                        mutant[i] = self.random_lesson_slot()
                    except ValueError as e:
                        self.logger.warning(f"Failed to generate new lesson for mutation: {e}")

            return mutant

        except Exception as e:
            self.logger.error(f"Mutation failed: {str(e)}")
            return individual

    def _select_mutation_points(self, individual: List) -> List[int]:
        """
        Wybiera punkty do mutacji, preferując problematyczne miejsca.

        Args:
            individual: Osobnik do analizy

        Returns:
            Lista indeksów do mutacji
        """
        schedule = self.convert_to_schedule(individual)
        problem_points = []

        # Znajdź konflikty
        for i, lesson1 in enumerate(individual):
            for j, lesson2 in enumerate(individual[i + 1:], i + 1):
                if self._check_conflict(lesson1, lesson2):
                    problem_points.extend([i, j])

        # Dodaj punkty z dziurami
        empty_slots = self._find_empty_slots(schedule)
        if empty_slots:
            related_lessons = self._find_lessons_near_gaps(individual, empty_slots)
            problem_points.extend(related_lessons)

        # Jeśli nie znaleziono problemów, wybierz losowe punkty
        if not problem_points:
            problem_points = random.sample(range(len(individual)),
                                           k=max(1, len(individual) // 10))

        return list(set(problem_points))  # usuń duplikaty

    def _check_conflict(self, lesson1: Tuple, lesson2: Tuple) -> bool:
        """Sprawdza czy między lekcjami występuje konflikt."""
        if lesson1[0] != lesson2[0] or lesson1[1] != lesson2[1]:
            return False

        return (lesson1[4] == lesson2[4] or  # ten sam nauczyciel
                lesson1[5] == lesson2[5] or  # ta sama sala
                lesson1[2] == lesson2[2])  # ta sama klasa

    def _find_lessons_near_gaps(self, individual: List, empty_slots: List[Tuple]) -> List[int]:
        """Znajduje lekcje sąsiadujące z dziurami w planie."""
        nearby_lessons = []

        for day, hour, class_group in empty_slots:
            for i, lesson in enumerate(individual):
                if (lesson[2] == class_group and  # ta sama klasa
                        lesson[0] == day and  # ten sam dzień
                        abs(lesson[1] - hour) <= 1):  # sąsiednia godzina
                    nearby_lessons.append(i)

        return nearby_lessons

    def _replace_or_add_lesson(self, individual: List, slot: Tuple, new_lesson: Tuple):
        """Zastępuje lub dodaje nową lekcję w odpowiednim miejscu."""
        day, hour, class_group = slot

        # Najpierw próbujemy znaleźć i zastąpić istniejącą lekcję
        for i, lesson in enumerate(individual):
            if (lesson[0] == day and
                    lesson[1] == hour and
                    lesson[2] == class_group):
                individual[i] = new_lesson
                return

        # Jeśli nie znaleziono istniejącej lekcji, dodajemy nową
        individual.append(new_lesson)

    def convert_to_schedule(self, individual: List) -> Schedule:
        """
        Konwertuje chromosom na obiekt Schedule.

        Args:
            individual: Lista lekcji w formacie chromosomu

        Returns:
            Obiekt Schedule

        Raises:
            ValueError: Gdy nie udało się skonwertować którejś z lekcji
        """
        schedule = Schedule(school=self.school)

        try:
            for day, hour, class_name, subject_name, teacher_id, classroom_id in individual:
                teacher = self.school.teachers.get(teacher_id)
                classroom = self.school.classrooms.get(classroom_id)
                subject = next(
                    s for s in self.school.subjects.values()
                    if s.name == subject_name
                )

                if not all([teacher, classroom, subject]):
                    raise ValueError(
                        f"Invalid lesson components: teacher={teacher_id}, "
                        f"classroom={classroom_id}, subject={subject_name}"
                    )

                lesson = Lesson(
                    subject=subject,
                    teacher=teacher,
                    classroom=classroom,
                    class_group=class_name,
                    day=day,
                    hour=hour
                )

                if not schedule.add_lesson(lesson):
                    self.logger.warning(
                        f"Could not add lesson to schedule: {lesson}",
                        cache_key=f"add_lesson_failed_{day}_{hour}_{class_name}"
                    )

            return schedule

        except Exception as e:
            self.logger.error(f"Schedule conversion failed: {str(e)}")
            raise

    def _find_empty_slots(self, schedule: Schedule) -> List[Tuple[int, int, str]]:
        """
        Znajduje puste sloty w planie.

        Returns:
            Lista krotek (dzień, godzina, klasa)
        """
        empty_slots = []

        for class_group in schedule.class_groups:
            class_lessons = schedule.get_class_lessons(class_group)
            used_slots = {(lesson.day, lesson.hour) for lesson in class_lessons}

            for day in range(self.DAYS):
                for hour in range(self.HOURS_PER_DAY):
                    if (day, hour) not in used_slots:
                        empty_slots.append((day, hour, class_group))

        return empty_slots

    def _find_good_segments(self, individual: List) -> List[Tuple[int, int]]:
        """
        Znajduje segmenty planu bez konfliktów i dziur.

        Returns:
            Lista par (początek, koniec) indeksów
        """
        segments = []

        try:
            class_day_lessons = defaultdict(lambda: defaultdict(list))
            for i, lesson in enumerate(individual):
                class_day_lessons[lesson[2]][lesson[0]].append((i, lesson))

            for class_group, days in class_day_lessons.items():
                for day, lessons in days.items():
                    if len(lessons) > 1:
                        sorted_lessons = sorted(lessons, key=lambda x: x[1][1])

                        # Sprawdź ciągłość godzin i brak konfliktów
                        valid_segment = True
                        hours = [l[1][1] for l in sorted_lessons]

                        for i in range(len(hours) - 1):
                            if hours[i + 1] - hours[i] > 1:
                                valid_segment = False
                                break

                        if valid_segment:
                            start_idx = sorted_lessons[0][0]
                            end_idx = sorted_lessons[-1][0]
                            segments.append((start_idx, end_idx + 1))

            return segments

        except Exception as e:
            self.logger.warning(f"Error finding good segments: {str(e)}")
            return []

    def _generate_filling_lesson(
            self,
            day: int,
            hour: int,
            class_group: str
    ) -> Optional[Tuple]:
        """
        Generuje lekcję dla pustego slotu z uwzględnieniem ograniczeń.

        Returns:
            Tuple reprezentujący lekcję lub None jeśli nie udało się wygenerować
        """
        max_attempts = 50

        try:
            class_obj = next(
                c for c in self.school.class_groups
                if c.name == class_group
            )

            for attempt in range(max_attempts):
                subject = random.choice(class_obj.subjects)

                available_teachers = [
                    t for t in self.school.teachers.values()
                    if (subject.name in t.subjects and
                        self._teacher_available(t, day, hour))
                ]

                suitable_rooms = [
                    r for r in self.school.classrooms.values()
                    if (r.is_suitable_for_subject(subject) and
                        self._room_available(r, day, hour))
                ]

                if not available_teachers or not suitable_rooms:
                    continue

                teacher = random.choice(available_teachers)
                classroom = random.choice(suitable_rooms)

                new_lesson = (
                    day, hour, class_group,
                    subject.name, teacher.id, classroom.id
                )

                if not self._check_conflicts([new_lesson]):
                    return new_lesson

            return None

        except Exception as e:
            self.logger.warning(
                f"Failed to generate filling lesson: {str(e)}",
                cache_key=f"fill_lesson_failed_{day}_{hour}_{class_group}"
            )
            return None

    # src/algorithms/genetic/genetic_operators.py (continuation)

    def _teacher_available(self, teacher: 'Teacher', day: int, hour: int) -> bool:
        """
        Sprawdza czy nauczyciel jest dostępny w danym terminie.

        Args:
            teacher: Obiekt nauczyciela
            day: Dzień tygodnia (0-4)
            hour: Godzina lekcyjna (0-7)

        Returns:
            bool: True jeśli nauczyciel jest dostępny
        """
        teacher_hours = self.school.get_teacher_hours(teacher)
        daily_hours = teacher_hours['daily'].get(day, 0)

        if daily_hours >= teacher.max_hours_per_day:
            return False

        # Sprawdź czy nauczyciel nie ma już lekcji w tym czasie
        for lesson in self.school.get_teacher_lessons(teacher):
            if lesson.day == day and lesson.hour == hour:
                return False

        return True

    def _room_available(self, room: 'Classroom', day: int, hour: int) -> bool:
        """
        Sprawdza czy sala jest dostępna w danym terminie.

        Args:
            room: Obiekt sali
            day: Dzień tygodnia (0-4)
            hour: Godzina lekcyjna (0-7)

        Returns:
            bool: True jeśli sala jest dostępna
        """
        for lesson in self.school.get_classroom_lessons(room):
            if lesson.day == day and lesson.hour == hour:
                return False
        return True

    def _check_conflicts(self, lessons: List[Tuple]) -> bool:
        """
        Sprawdza czy występują konflikty między lekcjami.

        Args:
            lessons: Lista lekcji do sprawdzenia

        Returns:
            bool: True jeśli występują konflikty
        """
        for i, lesson1 in enumerate(lessons):
            if not self._validate_lesson_tuple(lesson1):
                return True

            for lesson2 in lessons[i + 1:]:
                if not self._validate_lesson_tuple(lesson2):
                    return True

                if lesson1[0] == lesson2[0] and lesson1[1] == lesson2[1]:
                    # Ten sam czas - sprawdź kolizje
                    if (lesson1[4] == lesson2[4] or  # ten sam nauczyciel
                            lesson1[5] == lesson2[5] or  # ta sama sala
                            lesson1[2] == lesson2[2]):  # ta sama klasa
                        return True
        return False

    def _validate_lesson_tuple(self, lesson: Tuple) -> bool:
        """
        Sprawdza poprawność struktury krotki reprezentującej lekcję.

        Args:
            lesson: Krotka (dzień, godzina, klasa, przedmiot, id_nauczyciela, id_sali)

        Returns:
            bool: True jeśli struktura jest poprawna
        """
        try:
            if len(lesson) != 6:
                return False

            day, hour, class_name, subject_name, teacher_id, classroom_id = lesson

            # Sprawdź typy i zakresy
            if not (isinstance(day, int) and 0 <= day < self.DAYS):
                return False
            if not (isinstance(hour, int) and 0 <= hour < self.HOURS_PER_DAY):
                return False
            if not isinstance(class_name, str):
                return False
            if not isinstance(subject_name, str):
                return False
            if not isinstance(teacher_id, int):
                return False
            if not isinstance(classroom_id, int):
                return False

            # Sprawdź czy referencje istnieją
            if not self.school.teachers.get(teacher_id):
                return False
            if not self.school.classrooms.get(classroom_id):
                return False
            if not any(c.name == class_name for c in self.school.class_groups):
                return False
            if not any(s.name == subject_name for s in self.school.subjects.values()):
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Lesson validation failed: {str(e)}")
            return False

    def update_adaptive_rates(self, population_diversity: float):
        """
        Aktualizuje współczynniki adaptacyjne na podstawie różnorodności populacji.

        Args:
            population_diversity: Miara różnorodności populacji (0-1)
        """
        try:
            # Aktualizacja współczynnika mutacji
            if population_diversity < 0.3:
                # Zwiększ mutację przy małej różnorodności
                self.adaptive_rates['mutation']['current'] = min(
                    self.adaptive_rates['mutation']['current'] * 1.5,
                    self.adaptive_rates['mutation']['max_rate']
                )
            elif population_diversity > 0.7:
                # Zmniejsz mutację przy dużej różnorodności
                self.adaptive_rates['mutation']['current'] = max(
                    self.adaptive_rates['mutation']['current'] * 0.75,
                    self.adaptive_rates['mutation']['min_rate']
                )

            # Aktualizacja współczynnika krzyżowania
            if population_diversity < 0.3:
                # Zwiększ krzyżowanie przy małej różnorodności
                self.adaptive_rates['crossover']['current'] = min(
                    self.adaptive_rates['crossover']['current'] * 1.2,
                    self.adaptive_rates['crossover']['max_rate']
                )
            elif population_diversity > 0.7:
                # Zmniejsz krzyżowanie przy dużej różnorodności
                self.adaptive_rates['crossover']['current'] = max(
                    self.adaptive_rates['crossover']['current'] * 0.9,
                    self.adaptive_rates['crossover']['min_rate']
                )

        except Exception as e:
            self.logger.error(f"Error updating adaptive rates: {str(e)}")
