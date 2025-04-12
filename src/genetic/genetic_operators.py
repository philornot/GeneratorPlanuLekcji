# src/algorithms/genetic/genetic_operators.py

import random
from collections import defaultdict
from typing import List, Tuple, Optional, Any

from src.genetic.creator import get_individual_class
from src.models.classroom import Classroom
from src.models.lesson import Lesson
from src.models.schedule import Schedule
from src.models.school import School
from src.models.teacher import Teacher
from src.utils.logger import GPLLogger


def _replace_or_add_lesson(individual: List, slot: Tuple, new_lesson: Tuple):
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


class GeneticOperators:
    def __init__(self, school: School):
        self.school = school
        self.logger = GPLLogger(__name__)
        self.schedule = Schedule(school=self.school)

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

    def random_lesson_slot(self) -> tuple[int, int, Any, Any, Any, Any] | None:
        """
        Generuje losowy slot lekcyjny z uwzględnieniem ograniczeń.
        """
        max_attempts = 100  # Zwiększamy liczbę prób

        for attempt in range(max_attempts):
            try:
                # Losuj klasę i przedmiot
                class_group = random.choice(self.school.class_groups)
                subject = random.choice(class_group.subjects)

                # Znajdź dostępnych nauczycieli i sale
                available_teachers = [
                    t for t in self.school.teachers.values()
                    if subject.name in t.subjects
                ]
                suitable_rooms = [
                    r for r in self.school.classrooms.values()
                    if self.is_room_suitable(Lesson(
                        subject=subject,
                        teacher=None,
                        classroom=r,
                        class_group=class_group.name,
                        day=0,  # tymczasowe wartości
                        hour=0
                    ))
                ]

                if not available_teachers or not suitable_rooms:
                    continue

                # Próbuj znaleźć wolny slot
                shuffled_days = list(range(self.DAYS))
                shuffled_hours = list(range(self.HOURS_PER_DAY))
                random.shuffle(shuffled_days)
                random.shuffle(shuffled_hours)

                for day in shuffled_days:
                    for hour in shuffled_hours:
                        teacher = random.choice(available_teachers)
                        classroom = random.choice(suitable_rooms)

                        if self.is_slot_available(day, hour, teacher, classroom, class_group.name):
                            return day, hour, class_group.name, subject.name, teacher.id, classroom.id

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}",
                    cache_key=f"random_slot_attempt_{attempt}"
                )

        self.logger.warning(f"Failed to generate valid lesson slot after {max_attempts} attempts")
        # Zwróć None, zamiast rzucać wyjątek — pozwoli to na lepszą obsługę
        return None

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

            individual = get_individual_class()
            child1 = individual(ind1.copy())
            child2 = individual(ind2.copy())

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
            # Sprawdź, czy individual nie jest None
            if individual is None:
                self.logger.warning("Received None individual in mutation")
                Individual = get_individual_class()
                return Individual([])

            # Używaj get_individual_class zamiast creator.Individual
            Individual = get_individual_class()
            mutant = Individual(individual[:])

            # Filtruj None przed operacjami na elementach
            valid_elements = [i for i in range(len(mutant)) if mutant[i] is not None]

            # Inicjalizacja domyślna
            mutation_points = []

            # Bezpieczne operacje na losowym sample
            if valid_elements:  # Upewnij się, że lista nie jest pusta
                # Wybierz max 5 punktów lub mniej, jeśli nie ma tylu elementów
                mutation_points = random.sample(
                    valid_elements,
                    k=min(5, len(valid_elements))
                )

            # Wypełnianie dziur
            schedule = self.convert_to_schedule(mutant)

            # Tylko jeśli mamy poprawny harmonogram
            if schedule:
                empty_slots = self._find_empty_slots(schedule)

                if empty_slots and random.random() < 0.7:
                    # Wybierz do 3 losowych dziur do wypełnienia
                    slot_count = min(len(empty_slots), 3)
                    for slot in random.sample(empty_slots, slot_count):
                        new_lesson = self._generate_filling_lesson(*slot)
                        if new_lesson:
                            _replace_or_add_lesson(mutant, slot, new_lesson)

            # Standardowa mutacja - wybierz punkty do mutacji
            mutation_points = self._select_mutation_points(mutant)

            # Ogranicz liczbę punktów mutacji dla wydajności
            if len(mutation_points) > 5:
                mutation_points = random.sample(mutation_points, 5)

            # Wykonaj mutację na wybranych punktach
            for i in mutation_points:
                if i < len(mutant) and random.random() < self.adaptive_rates['mutation']['current']:
                    try:
                        # Generuj nowy slot lekcyjny
                        new_slot = self.random_lesson_slot()
                        if new_slot:  # Upewnij się, że slot został wygenerowany
                            mutant[i] = new_slot
                    except ValueError as e:
                        # Cichsze logowanie
                        self.logger.debug(f"Failed to generate new lesson for mutation: {e}")

            return mutant

        except Exception as e:
            import traceback
            self.logger.error(f"＼(｀0´)／ Mutacja nie powiodła się: {str(e)}\n{traceback.format_exc()}")
            return individual  # W przypadku błędu zwróć oryginalny osobnik

    def _select_mutation_points(self, individual: List) -> List[int]:
        """
        Wybiera punkty do mutacji, preferując problematyczne miejsca i klasy z małą liczbą lekcji.

        Args:
            individual: Osobnik do analizy

        Returns:
            Lista indeksów do mutacji
        """
        # Zabezpieczenie przed pustą listą
        if not individual:
            return []

        schedule = self.convert_to_schedule(individual)
        problem_points = []

        # Jeśli nie udało się utworzyć planu, wybierz losowe punkty
        if not schedule:
            num_points = min(10, max(1, len(individual) // 10))
            # Bezpieczny sample - upewnij się, że mamy wystarczającą liczbę elementów
            if len(individual) == 0:
                return []
            elif len(individual) < num_points:
                return list(range(len(individual)))
            else:
                return random.sample(range(len(individual)), k=num_points)

        # Licz lekcje per klasa
        class_lesson_counts = {}
        for class_group in self.school.class_groups:
            count = len(schedule.get_class_lessons(class_group.name))
            class_lesson_counts[class_group.name] = count

        # Znajdź puste i niedostatecznie wypełnione klasy
        empty_classes = [name for name, count in class_lesson_counts.items() if count == 0]
        underfilled_classes = [name for name, count in class_lesson_counts.items()
                               if 0 < count < 15]  # Minimum ~15 lekcji tygodniowo

        # Znajdź konflikty w planie
        for i, lesson1 in enumerate(individual):
            if lesson1 is None:
                problem_points.append(i)
                continue

            # Dodaj punkty dla lekcji w pustych/niedowypełnionych klasach
            if lesson1[2] in empty_classes:
                problem_points.append(i)
                continue

            if lesson1[2] in underfilled_classes:
                # 50% szans na dodanie punktu dla niedowypełnionych klas
                if random.random() < 0.5:
                    problem_points.append(i)
                    continue

            # Sprawdź konflikty
            for j, lesson2 in enumerate(individual[i + 1:], i + 1):
                if lesson2 is None:
                    continue

                if self._check_conflict(lesson1, lesson2):
                    problem_points.extend([i, j])

        # Dodaj punkty dla lekcji None (nieprawidłowych)
        for i, lesson in enumerate(individual):
            if lesson is None:
                problem_points.append(i)

        # Dodaj punkty z dziurami w planie
        if schedule:
            empty_slots = self._find_empty_slots(schedule)
            if empty_slots:
                related_lessons = self._find_lessons_near_gaps(individual, empty_slots)
                problem_points.extend(related_lessons)

        # Jeśli nie znaleziono problemów lub mamy za dużo punktów, optymalizuj
        if not problem_points:
            num_points = max(1, min(5, len(individual) // 20))
            if len(individual) < num_points:
                return list(range(len(individual)))
            else:
                return random.sample(range(len(individual)), k=num_points)
        elif len(problem_points) > 10:
            # Za dużo punktów, wybierz najważniejsze
            # Priorytetyzuj punkty związane z pustymi klasami
            empty_class_points = [p for p in problem_points
                                  if p < len(individual) and individual[p] is not None
                                  and individual[p][2] in empty_classes]

            if empty_class_points:
                # Wybierz wszystkie punkty dla pustych klas + kilka losowych
                other_points = [p for p in problem_points if p not in empty_class_points]

                # Bezpieczne użycie random.sample
                num_others = min(5, len(other_points))
                if num_others == 0:
                    selected_others = []
                else:
                    selected_others = random.sample(other_points, k=num_others)

                problem_points = empty_class_points + selected_others
            else:
                # Wybierz losowe punkty - bezpieczne użycie
                num_points = min(10, len(problem_points))
                problem_points = random.sample(problem_points, k=num_points) if num_points > 0 else []

        # Odfiltruj indeksy poza zakresem tablicy
        problem_points = [p for p in problem_points if 0 <= p < len(individual)]

        return list(set(problem_points))  # usuń duplikaty

    @staticmethod
    def _check_conflict(lesson1, lesson2) -> bool:
        """Sprawdza, czy między lekcjami występuje konflikt."""
        if lesson1 is None or lesson2 is None:
            return False

        if lesson1[0] != lesson2[0] or lesson1[1] != lesson2[1]:
            return False

        return (lesson1[4] == lesson2[4] or  # ten sam nauczyciel
                lesson1[5] == lesson2[5] or  # ta sama sala
                lesson1[2] == lesson2[2])  # ta sama klasa

    @staticmethod
    def _find_lessons_near_gaps(individual: List, empty_slots: List[Tuple]) -> List[int]:
        """Znajduje lekcje sąsiadujące z dziurami w planie."""
        nearby_lessons = []

        for day, hour, class_group in empty_slots:
            for i, lesson in enumerate(individual):
                # Dodane zabezpieczenie przed None
                if lesson is None:
                    continue

                if (lesson[2] == class_group and  # ta sama klasa
                        lesson[0] == day and  # ten sam dzień
                        abs(lesson[1] - hour) <= 1):  # sąsiednia godzina
                    nearby_lessons.append(i)

        return nearby_lessons

    def convert_to_schedule(self, individual: List) -> Optional[Schedule]:
        """Konwertuje chromosom na obiekt Schedule, zachowując ograniczenia."""
        schedule = Schedule(school=self.school)

        # Filtracja przed przetwarzaniem
        valid_indices = [i for i, lesson_data in enumerate(individual) if lesson_data is not None]

        # Przygotowanie wszystkich lekcji przed sprawdzeniami konfliktów
        potential_lessons = []

        for idx in valid_indices:
            lesson_data = individual[idx]
            try:
                teacher = self.school.teachers.get(lesson_data[4])
                classroom = self.school.classrooms.get(lesson_data[5])
                subject = next(
                    s for s in self.school.subjects.values()
                    if s.name == lesson_data[3]
                )

                lesson = Lesson(
                    subject=subject,
                    teacher=teacher,
                    classroom=classroom,
                    class_group=lesson_data[2],
                    day=lesson_data[0],
                    hour=lesson_data[1]
                )

                # Dodaj tylko jeśli sala jest odpowiednia
                if self.is_room_suitable(lesson):
                    potential_lessons.append(lesson)

            except Exception as e:
                # Cichsze logowanie
                pass

        # Sortuj lekcje dla deterministycznej kolejności dodawania
        sorted_lessons = sorted(potential_lessons, key=lambda x: (x.day, x.hour))

        # Dodaj lekcje do planu
        for lesson in sorted_lessons:
            schedule.add_lesson(lesson)

        return schedule if schedule.lessons else None

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
        if individual is None:
            return []

        segments = []

        try:
            class_day_lessons = defaultdict(lambda: defaultdict(list))

            for i, lesson in enumerate(individual):
                if lesson is None:
                    continue

                class_day_lessons[lesson[2]][lesson[0]].append((i, lesson))

            for class_group, days in class_day_lessons.items():
                for day, lessons in days.items():
                    if len(lessons) > 1:
                        sorted_lessons = sorted(lessons, key=lambda x: x[1][1])

                        # Sprawdź ciągłość godzin i brak konfliktów
                        valid_segment = True
                        lesson_hours = [lesson_data[1][1] for lesson_data in sorted_lessons]

                        for i in range(len(lesson_hours) - 1):
                            if lesson_hours[i + 1] - lesson_hours[i] > 1:
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

    def _generate_filling_lesson(self, day: int, hour: int, class_group: str) -> Optional[Tuple]:
        """Generuje lekcję dla pustego slotu"""
        max_attempts = 50

        try:
            class_obj = next(c for c in self.school.class_groups if c.name == class_group)

            for attempt in range(max_attempts):
                subject = random.choice(class_obj.subjects)

                # Znajdź odpowiednie sale najpierw
                suitable_rooms = [
                    r for r in self.school.classrooms.values()
                    if self.is_room_suitable(Lesson(
                        subject=subject,
                        teacher=None,  # Tymczasowo None
                        classroom=r,
                        class_group=class_group,
                        day=day,
                        hour=hour
                    ))
                ]

                if not suitable_rooms:
                    continue

                # Teraz szukaj nauczycieli
                available_teachers = [
                    t for t in self.school.teachers.values()
                    if subject.name in t.subjects and self._teacher_available(t, day, hour)
                ]

                if not available_teachers:
                    continue

                teacher = random.choice(available_teachers)
                classroom = random.choice(suitable_rooms)

                return day, hour, class_group, subject.name, teacher.id, classroom.id

            return None

        except Exception as e:
            self.logger.warning(f"Failed to generate filling lesson: {str(e)}")
            return None

    @staticmethod
    def is_room_suitable(lesson: 'Lesson') -> bool:
        """Sprawdza, czy sala jest odpowiednia dla przedmiotu i dostępna"""
        room = lesson.classroom

        # Sprawdź, czy przedmiot wymaga specjalnej sali
        if lesson.subject.requires_special_classroom:
            if room.room_type != lesson.subject.special_classroom_type:
                return False

        # Specjalne wymagania dla WF
        if lesson.subject.name == 'wf' and room.room_type != 'sala_gimnastyczna':
            return False

        # Specjalne wymagania dla informatyki
        if lesson.subject.name in ['informatyka', 'informatyka_rozszerzony'] and room.room_type != 'sala_komputerowa':
            return False

        return True

    def _teacher_available(self, teacher: 'Teacher', day: int, hour: int) -> bool:
        """
        Sprawdza, czy nauczyciel jest dostępny w danym terminie.
        """
        try:
            # Sprawdź lekcje nauczyciela w tym dniu
            teacher_lessons = [
                lesson for lesson in self.schedule.lessons
                if lesson.teacher.id == teacher.id
            ]

            # Sprawdź czy nauczyciel nie ma już lekcji w tym czasie
            if any(lesson.day == day and lesson.hour == hour for lesson in teacher_lessons):
                return False

            # Policz godziny w danym dniu
            daily_hours = sum(1 for lesson in teacher_lessons if lesson.day == day)
            if daily_hours >= teacher.max_hours_per_day:
                return False

            # Sprawdź tygodniowy limit
            weekly_hours = len(teacher_lessons)
            if weekly_hours >= teacher.max_hours_per_week:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking teacher availability: {str(e)}")
            return False


    def is_slot_available(self, day: int, hour: int, teacher: 'Teacher', classroom: 'Classroom',
                          class_group: str) -> bool:
        """
        Sprawdza, czy dany slot czasowy jest dostępny dla wszystkich zasobów.
        """
        try:
            # Sprawdź, czy sala jest dostępna w tym czasie
            for lesson in self.schedule.lessons:
                if lesson.day == day and lesson.hour == hour:
                    # Ten sam nauczyciel nie może prowadzić dwóch lekcji
                    if lesson.teacher.id == teacher.id:
                        return False
                    # Ta sama klasa nie może mieć dwóch lekcji
                    if lesson.class_group == class_group:
                        return False
                    # Ta sama sala nie może być używana przez dwie lekcje
                    if lesson.classroom.id == classroom.id:
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking slot availability: {str(e)}")
            return False

    def _room_available(self, room: 'Classroom', day: int, hour: int) -> bool:
        """
        Sprawdza, czy sala jest dostępna w danym terminie.

        Args:
            room: Obiekt sali
            day: Dzień tygodnia (0-4)
            hour: Godzina lekcyjna (0-7)

        Returns:
            bool: True, jeśli sala jest dostępna
        """
        for lesson in self.school.get_classroom_lessons(room):
            if lesson.day == day and lesson.hour == hour:
                return False
        return True

    def _check_conflicts(self, lessons: List[Tuple]) -> bool:
        """
        Sprawdza, czy występują konflikty między lekcjami.

        Args:
            lessons: Lista lekcji do sprawdzenia

        Returns:
            bool: True, jeśli występują konflikty
        """
        for i, lesson1 in enumerate(lessons):
            if not self._validate_lesson_tuple(lesson1):
                return True

            for lesson2 in lessons[i + 1:]:
                if not self._validate_lesson_tuple(lesson2):
                    return True

                if lesson1[0] == lesson2[0] and lesson1[1] == lesson2[1]:
                    # Ten sam czas — sprawdź kolizje
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
            bool: True, jeśli struktura jest poprawna
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

            # Sprawdź, czy referencje istnieją
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
