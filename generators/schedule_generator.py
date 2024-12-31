# generators/schedule_generator.py
import random
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from models.classroom import Classroom
from models.lesson import Lesson
from models.room_optimizer import znajdz_optymalna_sale
from models.schedule import Schedule
from models.school_class import SchoolClass
from models.teacher import Teacher
from utils.logger import ScheduleLogger


@dataclass
class GeneratorConfig:
    max_iterations: int = 500
    min_score: float = 75.0
    population_size: int = 50
    mutation_rate: float = 0.4
    crossover_rate: float = 0.8
    elitism_count: int = 5
    retry_count: int = 5
    early_stop_iterations: int = 5  # Po ilu iteracjach bez poprawy kończymy


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

        self.logger.log_info("Zainicjalizowano komponenty planu")

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
        """Generuje plan lekcji używając algorytmu genetycznego"""
        self.logger.log_info("Rozpoczynamy generowanie planu")

        last_progress_time = time.time()
        progress_interval = 5
        stagnant_iterations = 0
        best_schedule = None
        best_score = 0
        population = self._create_initial_population()

        for iteration in range(self.config.max_iterations):
            scores = [(schedule, schedule.calculate_schedule_score())
                      for schedule in population]
            scores.sort(key=lambda x: x[1], reverse=True)
            current_best = scores[0]

            if current_best[1] > best_score:
                best_score = current_best[1]
                best_schedule = deepcopy(current_best[0])
                stagnant_iterations = 0
                self.logger.log_info(f"Iteracja {iteration}: Nowy najlepszy wynik {best_score:.2f}/100")
            else:
                stagnant_iterations += 1

            current_time = time.time()
            if current_time - last_progress_time >= progress_interval:
                self.logger.log_info(f"Postęp: iteracja {iteration}/{self.config.max_iterations}, "
                                     f"najlepszy wynik: {best_score:.2f}/100")
                last_progress_time = current_time

            if stagnant_iterations >= self.config.early_stop_iterations:
                self.logger.log_info(f"Zatrzymano po {iteration} iteracjach z powodu braku postępu")
                if best_schedule:
                    self.schedule = best_schedule
                    return True, iteration
                return False, iteration

            if best_score >= self.config.min_score:
                self.schedule = best_schedule
                return True, iteration

            # Selekcja i krzyżowanie
            new_population = []
            while len(new_population) < self.config.population_size:
                parent1 = self._select_parent(scores)
                parent2 = self._select_parent(scores)
                child = self._crossover(parent1, parent2)
                if random.random() < self.config.mutation_rate:
                    child = self._mutate(child)
                new_population.append(child)

            population = new_population

        # Jeśli dotarliśmy tutaj, nie osiągnęliśmy wymaganego wyniku
        if best_schedule:
            self.schedule = best_schedule
            self.logger.log_warning(f"Nie osiągnięto wymaganego wyniku {self.config.min_score}. "
                                    f"Najlepszy wynik: {best_score:.2f}/100")
            return False, self.config.max_iterations

        self.logger.log_error("Nie udało się wygenerować planu")
        return False, self.config.max_iterations

    def _create_initial_population(self) -> List[Schedule]:
        """Tworzy początkową populację planów"""
        population = []
        for _ in range(self.config.population_size):
            schedule = deepcopy(self.schedule)
            self._assign_random_lessons(schedule)
            population.append(schedule)
        return population

    def _assign_random_lessons(self, schedule: Schedule):
        """Przydziela lekcje losowo do planu"""
        # Najpierw przydzielamy przedmioty dzielone na grupy, bo są trudniejsze
        for class_name, school_class in schedule.classes.items():
            split_subjects = {'Angielski': 3, 'Informatyka': 1, 'WF': 3}
            for subject, hours in split_subjects.items():
                # Przydziel obie grupy w tym samym czasie
                for _ in range(hours):
                    for _ in range(self.config.retry_count * 2):  # Więcej prób
                        day = random.randint(0, 4)
                        hour = random.randint(1, 9)

                        # Próbuj przydzielić obie grupy jednocześnie
                        lesson1 = self._create_lesson(subject, class_name, day, hour, schedule, 1)
                        lesson2 = self._create_lesson(subject, class_name, day, hour, schedule, 2)

                        if lesson1 and lesson2:
                            if schedule.add_lesson(lesson1) and schedule.add_lesson(lesson2):
                                break

            # Następnie przedmioty dla całej klasy
            required_subjects = self._get_required_subjects(school_class)
            for subject, hours in required_subjects.items():
                if subject not in split_subjects:
                    hours_per_day = 2 if subject in {'Polski', 'Matematyka'} else 1
                    days = list(range(5))
                    random.shuffle(days)

                    lessons_assigned = 0
                    for day in days:
                        for _ in range(hours_per_day):
                            if lessons_assigned >= hours:
                                break

                            for _ in range(self.config.retry_count):
                                if subject in {'Matematyka', 'Fizyka'}:
                                    hour = random.randint(2, 7)  # Nie pierwsze/ostatnie
                                else:
                                    hour = random.randint(1, 8)

                                lesson = self._create_lesson(subject, class_name, day, hour, schedule)
                                if lesson and schedule.add_lesson(lesson):
                                    lessons_assigned += 1
                                    break

    @staticmethod
    def _get_required_subjects(school_class: SchoolClass) -> Dict[str, int]:
        """Zwraca wymagane przedmioty i ich wymiar godzinowy dla klasy"""
        year = school_class.year
        subjects = {
            'Polski': 4,
            'Matematyka': 4 if year != 4 else 3,
            'Angielski': 3,
            'Niemiecki': 2,
            'Fizyka': 1 if year == 1 else 2,
            'Biologia': 1 if year == 1 else (2 if year in {2, 3} else 1),
            'Chemia': 1 if year == 1 else (2 if year in {2, 3} else 1),
            'Historia': 2,
            'WF': 3,
            'Informatyka': 1
        }

        # Dodaj przedmioty specyficzne dla roczników
        if year in {1, 2}:
            subjects['HiT'] = 1
        if year in {2, 3}:
            subjects['Przedsiębiorczość'] = 1

        return subjects

    def _create_lesson(self, subject: str, class_name: str, day: int, hour: int,
                       schedule: Schedule, group: Optional[int] = None) -> Optional[Lesson]:
        available_teachers = [
            teacher_id for teacher_id, teacher in schedule.teachers.items()
            if (subject in teacher.subjects and
                day in teacher.available_days and
                not teacher.schedule[day][hour])
        ]
        if not available_teachers:
            return None

        teacher_id = random.choice(available_teachers)

        # Użyj nowej metody znajdowania optymalnej sali
        room_id = znajdz_optymalna_sale(schedule, Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id="",  # Tymczasowa wartość
            day=day,
            hour=hour,
            class_name=class_name,
            group=group
        ))

        if not room_id:
            return None

        return Lesson(
            subject=subject,
            teacher_id=teacher_id,
            room_id=room_id,
            day=day,
            hour=hour,
            class_name=class_name,
            group=group
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
                for group in [1, 2]:
                    hours = school_class.get_group_hours(day, group)
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

    def _mutate(self, schedule: Schedule) -> Schedule:
        """Mutuje plan z adaptacyjną siłą mutacji"""
        mutated = deepcopy(schedule)
        current_score = schedule.calculate_schedule_score()

        # Zwiększ liczbę mutacji gdy wynik jest słaby
        base_mutation_rate = 0.1
        if current_score < 40:
            mutation_rate = 0.3
        elif current_score < 60:
            mutation_rate = 0.2
        else:
            mutation_rate = base_mutation_rate

        # Znajdź problematyczne lekcje
        conflicts = mutated.get_conflicts()
        problematic_lessons = []
        for l1, l2 in conflicts:
            if l1 not in problematic_lessons:
                problematic_lessons.append(l1)
            if l2 not in problematic_lessons:
                problematic_lessons.append(l2)

        # Ustal liczbę lekcji do mutacji
        num_mutations = max(
            len(problematic_lessons),
            int(len(mutated.lessons) * mutation_rate)
        )

        # Wybierz lekcje do mutacji
        lessons_to_mutate = problematic_lessons.copy()
        remaining_lessons = [l for l in mutated.lessons if l not in problematic_lessons]
        if len(lessons_to_mutate) < num_mutations:
            additional_lessons = random.sample(remaining_lessons,
                                               min(num_mutations - len(lessons_to_mutate),
                                                   len(remaining_lessons)))
            lessons_to_mutate.extend(additional_lessons)

        # Mutuj lekcje
        for lesson in lessons_to_mutate:
            self._mutate_single_lesson(mutated, lesson)

        return mutated

    def _mutate_single_lesson(self, schedule: Schedule, lesson: Lesson) -> None:
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
                group=lesson.group
            )

            if new_lesson and schedule.add_lesson(new_lesson):
                break
        else:
            # Jeśli nie udało się znaleźć nowego miejsca, przywróć
            schedule.add_lesson(lesson)
