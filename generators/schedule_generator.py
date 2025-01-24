# generators/schedule_generator.py
import random
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set, Union

from config.constants import REGULAR_SUBJECTS, DEFAULT_SUBJECT_WEIGHTS, HOUR_WEIGHTS, WEIGHT_MODIFIERS, MATURA_SUBJECTS
from models.classroom import Classroom
from models.lesson import Lesson
from models.room_optimizer import znajdz_optymalna_sale
from models.schedule import Schedule
from models.school_class import SchoolClass
from models.teacher import Teacher
from utils.logger import ScheduleLogger


@dataclass
class GeneratorConfig:
    max_iterations: int = 1000
    min_score: float = 60.0
    population_size: int = 100
    mutation_rate: float = 0.5
    crossover_rate: float = 0.5
    elitism_count: int = 5
    retry_count: int = 10
    early_stop_iterations: int = 20  # Po ilu iteracjach bez poprawy kończymy
    gaps_penalty: float = 20.0


class ScheduleGenerator:
    def __init__(self, config: GeneratorConfig = GeneratorConfig()):
        self.config = config
        self.logger = ScheduleLogger()
        self.schedule = Schedule()

    def initialize_schedule(self):
        """Inicjalizuje podstawowe komponenty planu"""
        self._initialize_classes()
        self._initialize_teachers()
        self._initialize_classrooms()

        # Dodajemy podstawowy przydział lekcji dla każdej klasy
        for class_name, school_class in self.schedule.classes.items():
            # Obliczamy docelową liczbę godzin
            target_hours = self._calculate_target_hours(school_class)

            # Rozkładamy godziny na dni
            hours_per_day = self._distribute_hours_per_day(target_hours)

            # Przydzielamy lekcje z uwzględnieniem rozkładu godzin
            self._assign_class_lessons(class_name, hours_per_day)

    def _reset_teachers_schedule(self):
        """Resetuje harmonogramy nauczycieli między próbami generowania planu"""
        for teacher in self.schedule.teachers.values():
            # Resetowanie harmonogramu do pustego
            teacher.schedule = {
                day: {hour: [] for hour in range(1, 10)}
                for day in range(5)
            }

    def _create_initial_population(self) -> List[Schedule]:
        """Tworzy początkową populację planów"""
        population = [deepcopy(self.schedule)]

        # Najpierw dodajemy oryginalny plan

        # Następnie tworzymy jego zmodyfikowane kopie
        for _ in range(self.config.population_size - 1):
            schedule_copy = deepcopy(self.schedule)

            # Wykonujemy kilka losowych mutacji
            num_mutations = random.randint(3, 10)
            for _ in range(num_mutations):
                if schedule_copy.lessons:  # sprawdzamy czy są lekcje
                    lesson = random.choice(schedule_copy.lessons)
                    self._mutate_lesson(schedule_copy, lesson)

            population.append(schedule_copy)

        return population

    def _calculate_target_hours(self, school_class: SchoolClass) -> int:
        """Oblicza docelową liczbę godzin dla klasy z uwzględnieniem rocznika"""
        year = school_class.year
        base_hours = {
            1: (31, 35),  # (min, max) dla pierwszej klasy
            2: (31, 35),
            3: (31, 34),
            4: (24, 26)
        }

        min_hours, max_hours = base_hours[year]

        # Dla klas 3 i 4 próbujemy trzymać się bliżej minimum
        if year >= 3:
            return min_hours + 1
        # Dla klas 1-2 możemy być bliżej maksimum
        else:
            return (min_hours + max_hours) // 2

    def _distribute_hours_per_day(self, total_hours: int) -> Dict[int, int]:
        """Rozkłada godziny na dni tygodnia równomiernie"""
        hours_per_day = {}
        remaining_hours = total_hours

        # Piątek zawsze ma mniej lekcji
        hours_per_day[4] = min(6, total_hours // 5)  # Piątek
        remaining_hours -= hours_per_day[4]

        # Rozłóż pozostałe godziny na pozostałe dni
        for day in range(4):  # Pon-Czw
            avg_hours = remaining_hours // (4 - day)
            # Limituj do 7-8 godzin dziennie
            hours_per_day[day] = min(8, max(5, avg_hours))
            remaining_hours -= hours_per_day[day]

        return hours_per_day

    def _assign_class_lessons(self, class_name: str, hours_per_day: Dict[int, int]):
        """Przydziela lekcje dla klasy z uwzględnieniem roku"""
        self.logger.log_info(f"Rozpoczynam przydzielanie lekcji dla klasy {class_name}")
        school_class = self.schedule.classes[class_name]
        year = school_class.year

        preferred_start = {1: 2, 2: 1, 3: 2, 4: 2}

        for day, num_hours in hours_per_day.items():
            self.logger.log_info(f"Przydzielam lekcje dla klasy {class_name} w dniu {day}")
            start_hour = preferred_start[year]
            required_subjects = self._get_required_subjects(school_class)
            end_hour = min(start_hour + num_hours, 9)

            # Przydziel lekcje
            success = self._assign_day_lessons(
                class_name=class_name,
                day=day,
                start_hour=start_hour,
                end_hour=end_hour,
                required_subjects=required_subjects
            )

            if not success:
                self.logger.log_warning(
                    f"Nie udało się przydzielić wszystkich lekcji dla klasy {class_name} w dniu {day}")

    def _assign_day_lessons(self, class_name: str, day: int, start_hour: int,
                            end_hour: int, required_subjects: Dict[str, int]) -> bool:
        """Przydziela lekcje na dany dzień z lepszym rozkładem godzin"""
        self.logger.log_info(f"Próba przydzielenia lekcji dla klasy {class_name} w dniu {day}")
        self.logger.log_debug(f"Dostępne przedmioty: {required_subjects}")
        current_hour = start_hour
        assigned_lessons = 0

        # 1. Matematyka i polski na początku dnia
        main_subjects = ['Matematyka', 'Polski']
        for subject in main_subjects:
            if required_subjects.get(subject, 0) > 0 and current_hour <= end_hour:
                if self._try_assign_lesson(class_name, day, current_hour, subject):
                    required_subjects[subject] -= 1
                    current_hour += 1
                    assigned_lessons += 1

        # 2. WF - tylko jedna godzina
        if required_subjects.get('Wychowanie fizyczne', 0) > 0 and current_hour <= end_hour:
            if self._try_assign_lesson(class_name, day, current_hour, 'Wychowanie fizyczne'):
                required_subjects['Wychowanie fizyczne'] -= 1
                current_hour += 1
                assigned_lessons += 1

        # 3. Pozostałe przedmioty
        while current_hour < end_hour:
            available_subjects = [(s, h) for s, h in required_subjects.items() if h > 0]
            if not available_subjects:
                self.logger.log_warning(f"Brak dostępnych przedmiotów dla klasy {class_name} w dniu {day}")
                break

            subject = max(available_subjects, key=lambda x: x[1])[0]

            if self._try_assign_lesson(class_name, day, current_hour, subject):
                required_subjects[subject] -= 1
                current_hour += 1
                assigned_lessons += 1
            else:
                current_hour += 1

        return assigned_lessons > 0

    def _try_assign_lesson(self, class_name: str, day: int, hour: int, subject: str) -> bool:
        """Próbuje przydzielić lekcję w danym terminie"""
        # Dodajemy logowanie dla debugowania
        self.logger.log_debug(f"Próba przydzielenia {subject} dla {class_name} (dzień {day}, godz {hour})")

        lesson = self._create_lesson(
            subject=subject,
            class_name=class_name,
            day=day,
            hour=hour,
            schedule=self.schedule
        )

        if lesson:
            success = self.schedule.add_lesson(lesson)
            if success:
                self.logger.log_debug(f"Sukces: przydzielono {subject} dla {class_name}")
            else:
                self.logger.log_error(f"Błąd: nie można dodać lekcji do planu")
            return success
        else:
            self.logger.log_error(f"Błąd: nie można utworzyć lekcji")
        return False

    def _can_add_subject_at_day(self, schedule: Schedule, class_name: str,
                                day: int, subject: str) -> bool:
        """Sprawdza czy można dodać przedmiot danego dnia"""
        # Sprawdź ile razy przedmiot występuje danego dnia
        count = sum(
            1 for hour in range(1, 10)
            for lesson in schedule.classes[class_name].schedule[day][hour]
            if lesson.subject == subject
        )

        # Przedmioty które mogą występować więcej niż raz dziennie
        multiple_allowed = {
            'Matematyka': 2,
            'Polski': 2,
            'Informatyka': 2
        }

        # Dla pozostałych przedmiotów - maksymalnie raz dziennie
        max_allowed = multiple_allowed.get(subject, 1)
        return count < max_allowed

    def _get_possible_hours_for_subject(self, schedule: Schedule, class_name: str,
                                        day: int, subject: str) -> List[int]:
        """Zwraca możliwe godziny dla przedmiotu"""
        possible_hours = []

        # Sprawdź czy przedmiot może być w ogóle dodany tego dnia
        if not self._can_add_subject_at_day(schedule, class_name, day, subject):
            return possible_hours

        # Sprawdź każdą godzinę
        for hour in range(1, 10):
            # Czy godzina jest wolna
            if schedule.classes[class_name].schedule[day][hour]:
                continue

            # Czy to nie pierwsza/ostatnia godzina dla przedmiotów z ograniczeniem
            if subject in {'Matematyka', 'Fizyka'}:
                if hour in {1, 9}:
                    continue

            possible_hours.append(hour)

        return possible_hours

    def _select_subject_for_hour(self, available_subjects: List[Tuple[str, int]],
                                 hour: int) -> str:
        """Wybiera najlepszy przedmiot na daną godzinę lekcyjną."""
        weighted_subjects = []
        hour_specific_weights = HOUR_WEIGHTS.get(hour, {})

        for subject, remaining_hours in available_subjects:
            # Weź wagę specyficzną dla godziny lub domyślną
            base_weight = hour_specific_weights.get(
                subject,
                DEFAULT_SUBJECT_WEIGHTS.get(subject, 1)
            )

            # Modyfikatory wagi
            hours_modifier = min(
                remaining_hours / 2,
                WEIGHT_MODIFIERS['HOURS_MODIFIER_MAX']
            )

            # Bonus dla przedmiotów maturalnych
            matura_bonus = (WEIGHT_MODIFIERS['MATURA_BONUS']
                            if subject in MATURA_SUBJECTS
                            else 1.0)

            final_weight = base_weight * hours_modifier * matura_bonus
            weighted_subjects.append((subject, final_weight))

        return max(weighted_subjects, key=lambda x: x[1])[0]

    def _initialize_classes(self):
        """Tworzy wszystkie klasy szkolne"""
        for year in range(1, 5):  # 4 roczniki
            for letter in 'ABCDE':  # 5 klas w roczniku
                class_name = f"{year}{letter}"
                self.schedule.classes[class_name] = SchoolClass(
                    name=class_name,
                    year=year,
                    home_room=str(random.randint(1, 28)),  # Tymczasowo losowa sala
                    class_teacher_id=""  # Będzie przypisane później
                )

    def _initialize_teachers(self):
        """Inicjalizuje kadrę nauczycielską"""
        from config.teacher_data import TeacherDataGenerator

        # Generuj dane nauczycieli
        teacher_data = TeacherDataGenerator.generate_teacher_data()

        # Twórz nauczycieli
        for data in teacher_data:
            if data['is_full_time']:
                teacher = Teacher.create_full_time(
                    teacher_id=data['teacher_id'],
                    subjects=data['subjects'],
                    name=f"{data['first_name']} {data['last_name']}"
                )
            else:
                teacher = Teacher.create_part_time(
                    teacher_id=data['teacher_id'],
                    subjects=data['subjects'],
                    name=f"{data['first_name']} {data['last_name']}",
                    days_count=len(data['available_days'])
                )
                teacher.set_available_days(data['available_days'])

            self.schedule.teachers[data['teacher_id']] = teacher

        self.logger.log_info(f"Zainicjalizowano {len(self.schedule.teachers)} nauczycieli")

    def _initialize_classrooms(self):
        """Inicjalizuje sale lekcyjne"""
        # Sale zwykłe
        for room_num in range(1, 29):
            if room_num not in {14, 24}:
                self.schedule.classrooms[str(room_num)] = Classroom.create_regular_room(room_num)

        # Sale komputerowe
        self.schedule.classrooms['14'] = Classroom.create_computer_room(14)
        self.schedule.classrooms['24'] = Classroom.create_computer_room(24)

        # Sale WF
        self.schedule.classrooms['SILOWNIA'] = Classroom.create_gym_room('SILOWNIA')
        self.schedule.classrooms['MALA_SALA'] = Classroom.create_gym_room('MALA_SALA')
        self.schedule.classrooms['DUZA_HALA'] = Classroom.create_gym_room('DUZA_HALA')

    def generate_schedule(self) -> tuple[bool, int]:
        if not self._validate_resources():
            self.logger.log_critical("Brak wymaganych zasobów do wygenerowania planu")
            return False, 0

        try:
            max_attempts = 10
            current_attempt = 0

            while current_attempt < max_attempts:
                try:
                    self.logger.log_info(f"Próba wygenerowania planu: {current_attempt + 1}/{max_attempts}")

                    # Resetowanie stanu
                    self.schedule = Schedule()
                    self.initialize_schedule()
                    self._reset_teachers_schedule()

                    success, iterations = self._generate_schedule_attempt()

                    if success:
                        return True, iterations

                    current_attempt += 1

                except Exception as e:
                    self.logger.log_critical(f"Błąd podczas generowania planu (próba {current_attempt}): {str(e)}")
                    self.logger.log_exception("Szczegóły błędu:", exc_info=e)
                    current_attempt += 1

            self.logger.log_critical("Nie udało się wygenerować planu po wszystkich próbach")
            return False, max_attempts

        except Exception as e:
            self.logger.log_critical(f"Nieoczekiwany błąd podczas generowania planu: {str(e)}")
            self.logger.log_exception("Pełny ślad błędu:", exc_info=e)
            return False, 0

    def _generate_schedule_attempt(self) -> tuple[bool, int]:
        """
        Próbuje wygenerować plan lekcji z zachowaniem wielokrotnych strategii.

        Returns:
        - Tuple: (czy się udało, liczba iteracji)
        """
        last_progress_time = time.time()
        progress_interval = 5
        stagnant_iterations = 0
        best_schedule = None
        best_score = 0.0  # Initialize as float

        # Tworzymy początkową populację planów
        population = self._create_initial_population()

        for iteration in range(self.config.max_iterations):
            # Oblicz oceny wszystkich planów w populacji
            scores = [(schedule, schedule.calculate_schedule_score())
                      for schedule in population]
            scores.sort(key=lambda x: x[1], reverse=True)

            # Znajdź aktualnie najlepszy plan
            current_best_schedule, current_best_score = scores[0]

            # Sprawdź postęp
            if current_best_score > best_score:
                best_score = current_best_score
                best_schedule = deepcopy(current_best_schedule)
                stagnant_iterations = 0

                self.logger.log_info(f"Iteracja {iteration}: Nowy najlepszy wynik {best_score:.2f}/100")
            else:
                stagnant_iterations += 1

            # Diagnostyka postępu
            current_time = time.time()
            if current_time - last_progress_time >= progress_interval:
                self.logger.log_debug(
                    f"Postęp: iteracja {iteration}/{self.config.max_iterations}, "
                    f"najlepszy wynik: {best_score:.2f}/100"
                )
                last_progress_time = current_time

            # Wczesne zatrzymanie, jeśli brak postępu
            if stagnant_iterations >= self.config.early_stop_iterations:
                self.logger.log_info(
                    f"Zatrzymano po {iteration} iteracjach z powodu braku postępu"
                )
                if best_schedule:
                    self.schedule = best_schedule
                    return True, iteration
                return False, iteration

            # Osiągnięto wymagany próg jakości
            if best_score >= self.config.min_score:
                self.schedule = best_schedule
                return True, iteration

            # Selekcja i krzyżowanie nowej populacji
            new_population = []
            while len(new_population) < self.config.population_size:
                # Wybierz rodziców metodą ruletki
                parent1 = self._select_parent(scores)
                parent2 = self._select_parent(scores)

                # Utwórz potomka przez krzyżowanie
                child = self._crossover(parent1, parent2)

                # Opcjonalna mutacja
                if random.random() < self.config.mutation_rate:
                    child = self._mutate(child)

                new_population.append(child)

            # Zaktualizuj populację
            population = new_population

        # Jeśli nie osiągnięto wyniku
        if best_schedule:
            self.schedule = best_schedule
            self.logger.log_warning(
                f"Nie osiągnięto wymaganego wyniku {self.config.min_score}. "
                f"Najlepszy wynik: {best_score:.2f}/100"
            )
            return False, self.config.max_iterations

        # Całkowite niepowodzenie
        self.logger.log_error("Nie udało się wygenerować planu")
        return False, self.config.max_iterations

    def _assign_lessons_ordered(self, schedule: Schedule):
        """Przydziela lekcje w uporządkowany sposób dla wszystkich klas"""
        # Sortujemy klasy według roku (malejąco) i nazwy
        class_order = sorted(
            schedule.classes.keys(),
            key=lambda x: (-int(x[0]), x[1:])  # np. "4A" -> (-4, "A")
        )

        for class_name in class_order:
            school_class = schedule.classes[class_name]
            required_subjects = self._get_required_subjects(school_class)

            # Przydzielamy dni według roku
            days_per_week = {
                1: 5,  # Pierwszaki mają zajęcia codziennie
                2: 5,
                3: 4,  # Trzecioklasiści mogą mieć wolny jeden dzień
                4: 4  # Czwartoklasiści też
            }[school_class.year]

            self._assign_class_lessons_to_days(
                schedule,
                class_name,
                required_subjects,
                days_per_week
            )

    def _assign_class_lessons_to_days(self, schedule: Schedule, class_name: str,
                                      required_subjects: Dict[str, int], days_per_week: int):
        """Przydziela lekcje dla klasy do określonej liczby dni"""
        # Wybierz dni z najmniejszą liczbą zajętych sal
        room_occupancy = self._calculate_room_occupancy(schedule)
        best_days = sorted(range(5), key=lambda d: room_occupancy[d])[:days_per_week]

        # Oblicz liczbę lekcji na dzień
        total_lessons = sum(required_subjects.values())
        lessons_per_day = {day: total_lessons // days_per_week for day in best_days}

        # Dodaj pozostałe lekcje do dni z najmniejszą liczbą godzin
        remaining = total_lessons % days_per_week
        for day in sorted(best_days, key=lambda d: lessons_per_day[d])[:remaining]:
            lessons_per_day[day] += 1

        # Przydziel lekcje do każdego dnia
        for day in best_days:
            target_lessons = lessons_per_day[day]
            self._assign_day_lessons(
                class_name=class_name,
                day=day,
                start_hour=self._get_start_hour(schedule, class_name, day),
                end_hour=self._get_end_hour(schedule, class_name, day, target_lessons),
                required_subjects=required_subjects
            )

    def _calculate_room_occupancy(self, schedule: Schedule) -> Dict[int, int]:
        """Oblicza zajętość sal w poszczególne dni"""
        occupancy = {day: 0 for day in range(5)}
        for room in schedule.classrooms.values():
            for day in range(5):
                for hour in range(1, 10):
                    if room.schedule[day][hour]:
                        occupancy[day] += 1
        return occupancy

    def _get_start_hour(self, schedule: Schedule, class_name: str, day: int) -> int:
        """Określa optymalną godzinę rozpoczęcia zajęć"""
        year = schedule.classes[class_name].year

        # Starsze klasy mogą zaczynać później
        base_start = {
            1: 1,  # Pierwsze klasy mogą zaczynać od pierwszej lekcji
            2: 1,
            3: 2,  # Starsze klasy preferują późniejsze godziny
            4: 2
        }[year]

        # Sprawdź dostępność sal i nauczycieli
        for hour in range(base_start, 5):  # Nie zaczynamy później niż 5 godzina
            if self._hour_has_available_resources(schedule, class_name, day, hour):
                return hour

        return base_start

    def _get_end_hour(self, schedule: Schedule, class_name: str,
                      day: int, target_lessons: int) -> int:
        """Określa optymalną godzinę zakończenia zajęć"""
        year = schedule.classes[class_name].year

        # Maksymalna godzina zakończenia zależy od dnia i roku
        max_end = {
            1: 8,  # Pierwsze klasy nie powinny kończyć zbyt późno
            2: 8,
            3: 7,  # Starsze klasy powinny kończyć wcześniej
            4: 7
        }[year]

        if day == 4:  # Piątek
            max_end = min(max_end, 7)  # W piątek kończymy wcześniej

        # Upewnij się, że zmieścimy wszystkie lekcje
        min_end = self._get_start_hour(schedule, class_name, day) + target_lessons

        return min(max_end, min_end)

    def _hour_has_available_resources(self, schedule: Schedule,
                                      class_name: str, day: int, hour: int) -> bool:
        """Sprawdza czy są dostępne sale i nauczyciele na daną godzinę"""
        # Sprawdź dostępność sal
        available_rooms = any(
            room.is_available(day, hour)
            for room in schedule.classrooms.values()
        )

        # Sprawdź dostępność nauczycieli
        available_teachers = any(
            teacher.is_available(day, hour)
            for teacher in schedule.teachers.values()
            if day in teacher.available_days
        )

        return available_rooms and available_teachers

    def _mutate(self, schedule: Schedule) -> Schedule:
        """Mutuje plan z uwzględnieniem specyfiki klas"""
        mutated = deepcopy(schedule)

        if len(mutated.lessons) == 0:
            # Jeśli plan jest pusty, spróbuj najpierw go zainicjalizować
            self.logger.log_info("Plan jest pusty, próba inicjalizacji...")
            self._assign_random_lessons(mutated)

            # Jeśli nadal jest pusty, zwróć oryginalny plan
            if len(mutated.lessons) == 0:
                self.logger.log_error("Nie udało się zainicjalizować pustego planu")
                return schedule

        score = schedule.calculate_schedule_score()
        num_mutations = self._calculate_mutations_count(score)
        problem_lessons = self._find_problem_lessons(mutated)

        # Sprawdź czy w ogóle mamy lekcje do mutacji
        if not mutated.lessons and not problem_lessons:
            self.logger.log_warning("Próba mutacji pustego planu")
            return mutated

        # Przeprowadź mutacje
        for _ in range(num_mutations):
            if problem_lessons:
                lesson = problem_lessons.pop(0)
            elif mutated.lessons:  # Dodajemy sprawdzenie czy lista nie jest pusta
                lesson = random.choice(mutated.lessons)
            else:
                break  # Jeśli nie ma więcej lekcji do mutacji, przerywamy

            self._mutate_lesson(mutated, lesson)

        return mutated

    def _validate_resources(self) -> bool:
        """Sprawdza czy wszystkie niezbędne zasoby są dostępne"""
        if len(self.schedule.teachers) == 0:
            self.logger.log_error("Brak zainicjalizowanych nauczycieli")
            return False

        if len(self.schedule.classrooms) == 0:
            self.logger.log_error("Brak zainicjalizowanych sal")
            return False

        if len(self.schedule.classes) == 0:
            self.logger.log_error("Brak zainicjalizowanych klas")
            return False

        return True

    def _calculate_mutations_count(self, score: float) -> int:
        """Oblicza liczbę mutacji na podstawie oceny"""
        if score < 50:
            return random.randint(4, 6)
        elif score < 75:
            return random.randint(2, 4)
        else:
            return random.randint(1, 2)

    def _find_problem_lessons(self, schedule: Schedule) -> List[Lesson]:
        """Znajduje lekcje wymagające poprawy"""
        problems = []

        # Sprawdź konflikty
        for l1, l2 in schedule.get_conflicts():
            if l1 not in problems:
                problems.append(l1)
            if l2 not in problems:
                problems.append(l2)

        # Sprawdź niepożądane godziny
        for lesson in schedule.lessons:
            if (lesson.subject in {'Matematyka', 'Fizyka'} and
                    lesson.hour in {1, 9} and
                    lesson not in problems):
                problems.append(lesson)

        return problems

    def _assign_random_lessons(self, schedule: Schedule):
        """Przydziela lekcje do planu z zachowaniem lepszych reguł rozkładu"""
        for class_name, school_class in schedule.classes.items():
            # Najpierw określamy wymagane przedmioty
            required_subjects = self._get_required_subjects(school_class)

            # Obliczamy optymalną liczbę lekcji na dzień
            total_lessons = sum(required_subjects.values())
            target_lessons_per_day = total_lessons / 5

            # Dla każdego dnia tygodnia
            for day in range(5):
                # Piątek ma mniej lekcji
                target_for_day = target_lessons_per_day - 1 if day == 4 else target_lessons_per_day

                # 1. Najpierw układamy przedmioty wymagające specjalnych sal
                self._assign_special_subjects(schedule, class_name, day, required_subjects)

                # 2. Następnie główne przedmioty (matematyka, polski) - najlepiej rano
                self._assign_main_subjects(schedule, class_name, day, required_subjects)

                # 3. Pozostałe przedmioty
                self._assign_remaining_subjects(schedule, class_name, day, required_subjects, target_for_day)

    def _assign_special_subjects(self, schedule: Schedule, class_name: str, day: int,
                                 required_subjects: Dict[str, int]):
        """Przydziela przedmioty wymagające specjalnych sal (WF, informatyka)"""
        special_subjects = {
            'Wychowanie fizyczne': {'SILOWNIA', 'MALA_SALA', 'DUZA_HALA'},
            'Informatyka': {'14', '24'}
        }

        for subject, rooms in special_subjects.items():
            # Sprawdzamy czy jeszcze potrzebujemy tego przedmiotu
            if required_subjects.get(subject, 0) <= 0:
                continue

            # Sprawdzamy czy ten przedmiot nie był już dzisiaj
            if not self._can_add_subject_at_day(schedule, class_name, day, subject):
                continue

            # Znajdź dostępne sale dla tego przedmiotu
            available_rooms = set([
                room for room in rooms
                if any(schedule.classrooms[room].is_available(day, hour) for hour in range(1, 10))
            ])

            # Jeśli nie ma dostępnych sal, przejdź do następnego przedmiotu
            if not available_rooms:
                self.logger.log_warning(f"Brak dostępnych sal dla {subject} w dniu {day}")
                continue

            # Znajdź najlepszą godzinę dla dostępnych sal
            best_hour = self._find_best_hour_for_subject(schedule, day, available_rooms)

            # Debug: pokaż stan sal przed próbą przydzielenia
            self.logger.log_debug(
                f"Próba przydzielenia {subject} w dniu {day}: "
                f"najlepsza godzina {best_hour}, dostępne sale {available_rooms}"
            )

            # Jeśli znaleźliśmy odpowiednią godzinę, próbujemy dodać lekcję
            if best_hour and self._create_and_add_lesson(schedule, subject, class_name, day, best_hour):
                required_subjects[subject] -= 1
                self.logger.log_debug(
                    f"Przydzielono {subject} dla klasy {class_name} w dniu {day} na godzinie {best_hour}"
                )
            else:
                self.logger.log_warning(
                    f"Nie udało się przydzielić {subject} dla klasy {class_name} w dniu {day}"
                )

    def _assign_main_subjects(self, schedule: Schedule, class_name: str, day: int, required_subjects: Dict[str, int]):
        """Przydziela główne przedmioty (matematyka, polski) na początku dnia"""
        main_subjects = ['Matematyka', 'Polski']
        early_hours = range(1, 4)  # Pierwsze 3 godziny lekcyjne

        for subject in main_subjects:
            if required_subjects.get(subject, 0) > 0:
                for hour in early_hours:
                    if self._can_add_lesson_at_time(schedule, class_name, day, hour):
                        if self._create_and_add_lesson(schedule, subject, class_name, day, hour):
                            required_subjects[subject] -= 1
                            break

    def _assign_remaining_subjects(self, schedule: Schedule, class_name: str, day: int,
                                   required_subjects: Dict[str, int], target_lessons: float):
        """Przydziela pozostałe przedmioty z uwzględnieniem limitu dziennego"""
        current_lessons = len([l for hour in range(1, 10)
                               for l in schedule.classes[class_name].schedule[day][hour]])

        while current_lessons < min(7, int(target_lessons)):  # Maksymalnie 7 lekcji dziennie
            # Wybierz przedmiot z największą pozostałą liczbą godzin
            available_subjects = [(s, h) for s, h in required_subjects.items() if h > 0]
            if not available_subjects:
                break

            subject = max(available_subjects, key=lambda x: x[1])[0]

            # Znajdź najlepszą godzinę dla tego przedmiotu
            best_hour = self._find_optimal_hour(schedule, class_name, day, subject)
            if best_hour and self._create_and_add_lesson(schedule, subject, class_name, day, best_hour):
                required_subjects[subject] -= 1
                current_lessons += 1

    def _find_optimal_hour(self, schedule: Schedule, class_name: str, day: int, subject: str) -> Optional[int]:
        """Znajduje optymalną godzinę dla przedmiotu"""
        class_schedule = schedule.classes[class_name].schedule[day]

        # Znajdź aktualnie zajęte godziny
        occupied_hours = [h for h in range(1, 10) if class_schedule[h]]

        if not occupied_hours:
            # Jeśli to pierwszy przedmiot, zacznij od rana
            return 1

        # Unikaj okienek - szukaj godziny przylegającej do istniejących lekcji
        min_hour = min(occupied_hours)
        max_hour = max(occupied_hours)

        # Próbuj dodać przed istniejącym blokiem
        if min_hour > 1 and not subject in {'Matematyka', 'Fizyka'}:  # Te przedmioty nie na pierwszej
            return min_hour - 1

        # Próbuj dodać po istniejącym bloku
        if max_hour < 8:  # Nie później niż 8 godzina
            return max_hour + 1

        # Szukaj dziur w środku
        for h in range(min_hour, max_hour):
            if h not in occupied_hours:
                return h

        return None

    def _create_and_add_lesson(self, schedule: Schedule, subject: str, class_name: str,
                               day: int, hour: int) -> bool:
        """Tworzy i dodaje lekcję z lepszym doborem nauczyciela"""
        # Znajdź najlepszego dostępnego nauczyciela
        available_teachers = [
            teacher_id for teacher_id, teacher in schedule.teachers.items()
            if (subject in teacher.subjects and
                day in teacher.available_days and
                not teacher.schedule[day][hour])
        ]

        if not available_teachers:
            return False

        # Wybierz nauczyciela z najmniejszą liczbą godzin
        teacher_id = min(
            available_teachers,
            key=lambda t: schedule.teachers[t].get_teaching_hours()
        )

        # Znajdź optymalną salę
        room_id = znajdz_optymalna_sale(schedule, Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id="",  # Tymczasowo puste
            day=day,
            hour=hour,
            class_name=class_name
        ))

        if not room_id:
            return False

        lesson = Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id=room_id,
            day=day,
            hour=hour,
            class_name=class_name
        )

        return schedule.add_lesson(lesson)

    def _get_subject_priority(self, subject: str) -> int:
        """Zwraca priorytet przedmiotu do układania w planie"""
        priorities = {
            'Matematyka': 5,
            'Polski': 5,
            'Język obcy nowożytny': 4,
            'Drugi język obcy': 4,
            'Wychowanie fizyczne': 4,
            'Fizyka': 3,
            'Chemia': 3,
            'Biologia': 3,
            'Historia': 3
        }
        return priorities.get(subject, 1)

    @staticmethod
    def _get_required_subjects(school_class: SchoolClass) -> Dict[str, int]:
        """Zwraca wymagane przedmioty i ich wymiar godzinowy dla klasy"""
        year = school_class.year
        subjects = {}

        for subject, hours_per_year in REGULAR_SUBJECTS.items():
            if hours_per_year[year] > 0:
                subjects[subject] = hours_per_year[year]

        return subjects

    def _create_lesson(self, subject: str, class_name: str, day: int, hour: int,
                       schedule: Schedule) -> Optional[Lesson]:
        """Tworzy nową lekcję"""
        # Najpierw znajdź nauczyciela
        available_teachers = [
            teacher_id for teacher_id, teacher in schedule.teachers.items()
            if (subject in teacher.subjects and
                day in teacher.available_days and
                not teacher.schedule[day][hour])
        ]

        if not available_teachers:
            self.logger.log_warning(f"Brak dostępnych nauczycieli dla {subject}")
            return None

        teacher_id = random.choice(available_teachers)

        # Utwórz tymczasową lekcję do znalezienia sali
        temp_lesson = Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id="",  # Tymczasowa wartość
            day=day,
            hour=hour,
            class_name=class_name
        )

        # Znajdź optymalną salę
        room_id = znajdz_optymalna_sale(schedule, temp_lesson)
        if not room_id:
            self.logger.log_debug(f"Brak dostępnej sali dla {subject}")
            return None

        return Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id=room_id,
            day=day,
            hour=hour,
            class_name=class_name
        )

    def _select_parent(self, scored_population: List[Tuple[Schedule, float]]) -> Schedule:
        """Wybiera rodzica metodą ruletki"""
        total_score = sum(score for _, score in scored_population)
        r = random.uniform(0, total_score)
        current_sum = 0

        for schedule, score in scored_population:
            current_sum += score
            if current_sum > r:
                return schedule

        return scored_population[0][0]

    def _crossover(self, parent1: Schedule, parent2: Schedule) -> Schedule:
        """Krzyżuje dwa plany w sposób inteligentny"""
        child = Schedule()
        child.classes = deepcopy(self.schedule.classes)
        child.teachers = deepcopy(self.schedule.teachers)
        child.classrooms = deepcopy(self.schedule.classrooms)

        # Oceń każdą klasę w obu rodzicach
        class_scores1 = self._evaluate_classes(parent1)
        class_scores2 = self._evaluate_classes(parent2)

        # Dla każdej klasy wybierz lepszy plan
        for class_name in child.classes.keys():
            better_parent = parent1 if class_scores1[class_name] > class_scores2[class_name] else parent2
            lessons = [l for l in better_parent.lessons if l.class_name == class_name]

            # Dodaj lekcje do dziecka
            for lesson in lessons:
                child.add_lesson(deepcopy(lesson))

        return child

    def _evaluate_classes(self, schedule: Schedule) -> Dict[str, float]:
        """Ocenia plan każdej klasy"""
        scores = {}
        for class_name, school_class in schedule.classes.items():
            score = 100.0

            # Sprawdź okienka (-10 punktów za każde)
            for day in range(5):
                hours = school_class.get_day_hours(day)
                if hours:
                    for i in range(min(hours), max(hours)):
                        if i not in hours:
                            score -= 10

            # Sprawdź liczbę lekcji dziennie (-20 punktów za złą liczbę)
            for day in range(5):
                day_lessons = school_class.get_day_hours(day)
                if len(day_lessons) < 5 or len(day_lessons) > 8:
                    score -= 20

            # Sprawdź konflikty (-15 punktów za każdy)
            class_lessons = [l for l in schedule.lessons if l.class_name == class_name]
            for i, l1 in enumerate(class_lessons):
                for l2 in class_lessons[i + 1:]:
                    if l1.conflicts_with(l2):
                        score -= 15

            scores[class_name] = max(0, score)
        return scores

    def _mutate_lesson(self, schedule: Schedule, lesson: Lesson) -> None:
        """Mutuje pojedynczą lekcję"""
        schedule.remove_lesson(lesson)

        # Więcej prób dla problematycznych przedmiotów
        max_attempts = self.config.retry_count * 3 if lesson.subject in {'Matematyka', 'Polski',
                                                                         'Angielski'} else self.config.retry_count

        for _ in range(max_attempts):
            new_day = random.randint(0, 4)

            # Inteligentny wybór godziny
            if lesson.subject in {'Matematyka', 'Fizyka'}:
                new_hour = random.randint(2, 7)  # Nie pierwsze/ostatnie
            else:
                # Sprawdź istniejące lekcje tej klasy tego dnia
                class_hours = schedule.classes[lesson.class_name].get_day_hours(new_day)
                if class_hours:
                    # Próbuj umieścić blisko innych lekcji
                    min_hour = max(1, min(class_hours) - 1)
                    max_hour = min(9, max(class_hours) + 1)
                    new_hour = random.randint(min_hour, max_hour)
                else:
                    new_hour = random.randint(1, 8)

            new_lesson = self._create_lesson(
                subject=lesson.subject,
                class_name=lesson.class_name,
                day=new_day,
                hour=new_hour,
                schedule=schedule,
            )

            if new_lesson and schedule.add_lesson(new_lesson):
                break
        else:
            # Jeśli nie udało się znaleźć nowego miejsca, przywróć
            schedule.add_lesson(lesson)

    def _find_best_hour_for_subject(self, schedule: Schedule, day: int, rooms: Union[Set[str], List[str]]) -> Optional[
        int]:
        """Znajduje najlepszą godzinę dla przedmiotu wymagającego specjalnej sali"""
        # Konwersja rooms do listy, jeśli jest to zbiór
        rooms_list = list(rooms)

        try:
            # Dla WF specjalna logika
            if any(room in {'SILOWNIA', 'MALA_SALA', 'DUZA_HALA'} for room in rooms_list):
                # Sprawdź obłożenie każdej z sal gimnastycznych
                room_occupancy: Dict[str, int] = {
                    'SILOWNIA': 0,
                    'MALA_SALA': 0,
                    'DUZA_HALA': 0
                }

                # Oblicz obecne obłożenie sal
                for room in rooms_list:
                    try:
                        classroom = schedule.classrooms.get(room)
                        if classroom is None:
                            self.logger.log_warning(f"Sala {room} nie istnieje w planie")
                            continue

                        for hour in range(1, 10):
                            try:
                                # Use .get() with a default of an empty list to avoid potential errors
                                lessons = classroom.schedule.get(day, {}).get(hour, [])
                                room_occupancy[room] += len(lessons)
                            except (KeyError, IndexError, TypeError) as e:
                                self.logger.log_error(
                                    f"Błąd podczas sprawdzania obłożenia sali {room} w godzinie {hour}: {e}")
                                continue

                    except Exception as e:
                        self.logger.log_error(f"Nieoczekiwany błąd przy sprawdzaniu sali {room}: {e}")
                        continue

                # Znajdź sale, które jeszcze mogą przyjąć grupę
                try:
                    available_rooms = [
                        room for room in rooms_list
                        if room_occupancy.get(room, 0) < {
                            'SILOWNIA': 1,
                            'MALA_SALA': 3,
                            'DUZA_HALA': 6
                        }.get(room, 0)
                    ]
                except Exception as e:
                    self.logger.log_error(f"Błąd przy określaniu dostępnych sal: {e}")
                    available_rooms = []

                # Jeśli nie ma dostępnych sal, zwróć najbliższą dostępną godzinę
                if not available_rooms:
                    return self._find_fallback_hour(schedule, day, rooms_list)

                # Preferuj środkowe godziny dnia
                preferred_hours = [3, 4, 5, 6]
                try:
                    random.shuffle(preferred_hours)
                except Exception as e:
                    self.logger.log_error(f"Błąd podczas losowania godzin: {e}")

                # Sprawdź preferowane godziny
                for hour in preferred_hours:
                    if self._is_room_available_for_hour(schedule, day, hour, available_rooms):
                        return hour

                # Sprawdź pozostałe godziny
                for hour in [1, 2, 7, 8, 9]:
                    if self._is_room_available_for_hour(schedule, day, hour, available_rooms):
                        return hour

            # Standardowa logika dla innych przedmiotów
            return self._find_standard_hour(schedule, day, rooms_list)

        except Exception as e:
            self.logger.log_error(f"Nieoczekiwany błąd w _find_best_hour_for_subject: {e}")
            return None

    def _is_room_available_for_hour(self, schedule: Schedule, day: int, hour: int, rooms: List[str]) -> bool:
        """Sprawdza dostępność sali dla danej godziny"""
        try:
            return any(
                schedule.classrooms.get(room) is not None and
                schedule.classrooms[room].is_available(day, hour)
                for room in rooms
            )
        except Exception as e:
            self.logger.log_error(f"Błąd podczas sprawdzania dostępności sali w godzinie {hour}: {e}")
            return False

    def _find_fallback_hour(self, schedule: Schedule, day: int, rooms: List[str]) -> Optional[int]:
        """Znajduje alternatywną godzinę, gdy nie ma dostępnych sal"""
        try:
            for hour in [3, 4, 5, 6, 1, 2, 7, 8, 9]:
                if self._is_room_available_for_hour(schedule, day, hour, rooms):
                    return hour
            return None
        except Exception as e:
            self.logger.log_error(f"Błąd podczas wyszukiwania zastępczej godziny: {e}")
            return None

    def _find_standard_hour(self, schedule: Schedule, day: int, rooms: Union[Set[str], List[str]]) -> Optional[int]:
        """Znajduje standardową godzinę dla przedmiotów"""
        try:
            # Konwersja rooms do listy, jeśli jest to zbiór
            rooms_list = list(rooms)

            # Preferuj środkowe godziny dnia
            for hour in range(2, 8):
                if self._is_room_available_for_hour(schedule, day, hour, rooms_list):
                    return hour

            # Jeśli nie znaleziono w preferowanych godzinach, sprawdź pozostałe
            for hour in [1, 8, 9]:
                if self._is_room_available_for_hour(schedule, day, hour, rooms_list):
                    return hour

            return None
        except Exception as e:
            self.logger.log_error(f"Błąd podczas wyszukiwania standardowej godziny: {e}")
            return None

    def _can_add_lesson_at_time(self, schedule: Schedule, class_name: str,
                                day: int, hour: int) -> bool:
        """Sprawdza czy można dodać lekcję w danym terminie"""
        school_class = schedule.classes[class_name]

        # Sprawdź czy nie ma już lekcji w tym czasie
        if school_class.schedule[day][hour]:
            return False

        # Sprawdź czy to nie tworzy okienka
        occupied_hours = school_class.get_day_hours(day)
        if occupied_hours:
            min_hour = min(occupied_hours)
            max_hour = max(occupied_hours)
            if min_hour < hour < max_hour and hour not in occupied_hours:
                return False

        return True
