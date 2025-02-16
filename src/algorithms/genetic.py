# src/algorithms/genetic.py
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
from deap import creator, tools, base

from src.models.lesson import Lesson
from src.models.schedule import Schedule
from src.models.school import School
from src.utils.fitness_evaluator import FitnessEvaluator

logger = logging.getLogger(__name__)


class ScheduleGenerator:
    def __init__(self, school: School, params: Dict):
        self.school = school
        self.params = params
        self.evaluator = FitnessEvaluator(school=school, config=params)

        # Stałe czasowe
        self.DAYS = 5  # Poniedziałek-Piątek
        self.HOURS_PER_DAY = 8  # 8 godzin lekcyjnych dziennie

        # Parametry adaptacyjne
        self.adaptive_rates = {
            'mutation': {
                'min_rate': 0.01,
                'max_rate': 0.3,
                'current': 0.1
            },
            'crossover': {
                'min_rate': 0.6,
                'max_rate': 0.95,
                'current': 0.8
            }
        }

        # Cache dla ocen
        self.fitness_cache = {}

        # Dodajemy pole na najlepsze znane rozwiązanie
        self.best_known_solution = None
        try:
            best_solution_path = Path('data/best_solution.json')
            if best_solution_path.exists():
                with open(best_solution_path, 'r') as f:
                    data = json.load(f)
                    self.best_known_solution = data['solution']
                    logger.info(f"Loaded best known solution with fitness: {data['fitness']}")
        except Exception as e:
            logger.error(f"Error loading best solution: {e}")
            self.best_known_solution = None

        # Inicjalizacja DEAP
        self.setup_deap()

    def adaptive_mutation_rate(self, population: List) -> float:
        """Dynamicznie dostosowuje współczynnik mutacji"""
        # Oblicz różnorodność populacji
        diversity = self.calculate_population_diversity(population)

        if diversity < 0.3:  # Mała różnorodność
            # Zwiększ mutację aby uciec z lokalnego minimum
            self.adaptive_rates['mutation']['current'] = min(
                self.adaptive_rates['mutation']['current'] * 1.5,
                self.adaptive_rates['mutation']['max_rate']
            )
        elif diversity > 0.7:  # Duża różnorodność
            # Zmniejsz mutację aby ustabilizować populację
            self.adaptive_rates['mutation']['current'] = max(
                self.adaptive_rates['mutation']['current'] * 0.75,
                self.adaptive_rates['mutation']['min_rate']
            )

        return self.adaptive_rates['mutation']['current']

    def calculate_population_diversity(self, population: List) -> float:
        """Oblicza różnorodność populacji"""
        if not population:
            return 0.0

        # Zamieniamy każdy element osobnika na tuple, żeby był hashowalny
        unique_individuals = set(
            tuple(tuple(lesson) for lesson in ind)
            for ind in population
        )
        return len(unique_individuals) / len(population)

    def crossover(self, ind1: List, ind2: List) -> Tuple[List, List]:
        """Operator krzyżowania"""
        size = len(ind1)

        # Znajdź dobre segmenty (bez konfliktów)
        good_segments1 = self.find_good_segments(ind1)
        good_segments2 = self.find_good_segments(ind2)

        # Stwórz nowe osobniki - używamy creator.Individual zamiast zwykłych list
        child1 = creator.Individual(ind1.copy())
        child2 = creator.Individual(ind2.copy())

        # Wymień dobre segmenty między osobnikami
        for (start1, end1), (start2, end2) in zip(good_segments1, good_segments2):
            if random.random() < 0.5:  # 50% szans na wymianę
                temp = child1[start1:end1]
                child1[start1:end1] = child2[start2:end2]
                child2[start2:end2] = temp

        return child1, child2

    def find_good_segments(self, individual: List) -> List[Tuple[int, int]]:
        """Znajduje segmenty planu bez konfliktów"""
        segments = []
        current_start = 0
        conflicts = 0

        for i in range(len(individual)):
            if self.check_conflicts(individual[i:i + 1]):
                conflicts += 1
                if conflicts == 0 and i > current_start:
                    segments.append((current_start, i))
                current_start = i + 1

        return segments

    def mutation(self, individual: List) -> List:
        """Mutacja uwzględniająca konflikty"""
        # Tworzymy kopię osobnika jako creator.Individual
        mutant = creator.Individual(individual[:])

        # Znajdź problematyczne miejsca
        conflict_indices = []
        for i, lesson in enumerate(mutant):
            if self.check_conflicts([lesson]):
                conflict_indices.append(i)

        # Jeśli są konflikty, skup się na ich naprawie
        if conflict_indices:
            for idx in conflict_indices:
                if random.random() < 0.8:  # 80% szans na naprawę konfliktu
                    mutant[idx] = self.generate_repair_lesson(mutant, idx)
        else:
            # Jeśli nie ma konfliktów, wykonaj standardową mutację
            for i in range(len(mutant)):
                if random.random() < self.adaptive_rates['mutation']['current']:
                    mutant[i] = self.random_lesson_slot()

        return mutant

    def generate_repair_lesson(self, individual: List, index: int) -> Tuple:
        """Generuje nową lekcję unikając konfliktów"""
        max_attempts = 50
        current_lesson = individual[index]

        for _ in range(max_attempts):
            # Zachowaj niektóre oryginalne atrybuty
            new_lesson = list(current_lesson)

            # Spróbuj zmienić czas
            new_lesson[0] = random.randint(0, self.DAYS - 1)
            new_lesson[1] = random.randint(0, self.HOURS_PER_DAY - 1)

            # Jeśli nadal jest konflikt, spróbuj zmienić salę
            if self.check_conflicts([tuple(new_lesson)]):
                subject = self.school.get_subject(new_lesson[3])
                new_classroom = self.find_available_classroom(subject)
                new_lesson[5] = new_classroom.id

            # Sprawdź czy naprawiono konflikt
            if not self.check_conflicts([tuple(new_lesson)]):
                return tuple(new_lesson)

        # Jeśli nie udało się naprawić, wygeneruj całkowicie nowy slot
        return self.random_lesson_slot()

    def optimize_population(self, population: List) -> List:
        """Optymalizuje populację używając technik lokalnego przeszukiwania"""
        improved_population = []

        for individual in population:
            if random.random() < 0.1:  # 10% szans na optymalizację lokalną
                improved = self.local_search(individual)
                improved_population.append(improved)
            else:
                improved_population.append(individual)

        return improved_population

    def local_search(self, individual: List) -> List:
        """Wykonuje lokalne przeszukiwanie"""
        best_fitness = self.evaluate_schedule(individual)[0]
        best_solution = creator.Individual(individual[:])

        for _ in range(10):  # 10 prób poprawy
            # Wygeneruj sąsiada
            neighbor = creator.Individual(best_solution[:])

            # Małe zmiany w losowych miejscach
            for _ in range(3):
                idx = random.randrange(len(neighbor))
                neighbor[idx] = self.random_lesson_slot()

            # Sprawdź czy lepszy
            neighbor_fitness = self.evaluate_schedule(neighbor)[0]
            if neighbor_fitness > best_fitness:
                best_fitness = neighbor_fitness
                best_solution = neighbor

        return best_solution

    def generate(self, progress_callback=None) -> Tuple[Schedule, List[Dict]]:
        """Główna funkcja generująca plan"""
        logger.info("Starting schedule generation")

        # Parametry
        pop_size = self.params.get('population_size', 300)
        n_generations = self.params.get('iterations', 1000)

        # Inicjalizacja populacji z poprzednim najlepszym rozwiązaniem
        population = self.toolbox.population(n=pop_size - 1)
        if self.best_known_solution:
            population.append(creator.Individual(self.best_known_solution))

        # Statystyki i historia
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        halloffame = tools.HallOfFame(5)  # Zachowuj 5 najlepszych rozwiązań
        progress_history = []

        # Ocena początkowej populacji
        fitnesses = self.toolbox.map(self.toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit

        # Główna pętla
        for gen in range(n_generations):
            # Adaptacyjne dostosowanie parametrów
            mut_rate = self.adaptive_mutation_rate(population)

            # Selekcja i reprodukcja
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))

            # Krzyżowanie
            for i in range(1, len(offspring), 2):
                if random.random() < self.adaptive_rates['crossover']['current']:
                    offspring[i - 1], offspring[i] = self.crossover(
                        offspring[i - 1], offspring[i]
                    )
                    del offspring[i - 1].fitness.values
                    del offspring[i].fitness.values

            # Mutacja
            for i in range(len(offspring)):
                if random.random() < mut_rate:
                    offspring[i] = self.mutation(offspring[i])
                    del offspring[i].fitness.values

            # Lokalna optymalizacja
            offspring = self.optimize_population(offspring)

            # Ocena nowego pokolenia
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # Aktualizacja populacji
            population[:] = offspring

            # Aktualizacja hall of fame
            halloffame.update(population)

            # Zbieranie statystyk
            record = stats.compile(population)

            # Logowanie i callback
            progress_data = {
                'generation': gen,
                'best_fitness': record['max'],
                'avg_fitness': record['avg'],
                'std_fitness': record['std'],
                'progress_percent': (gen + 1) / n_generations * 100
            }
            progress_history.append(progress_data)

            logger.info(
                f"Gen {gen}: Best={record['max']:.2f}, "
                f"Avg={record['avg']:.2f}, "
                f"Std={record['std']:.2f}"
            )

            if progress_callback:
                progress_callback(progress_data)

            # Opcjonalne wczesne zatrzymanie jeśli osiągnięto wystarczająco dobry wynik
            if record['max'] >= 95:  # Możesz dostosować ten próg
                logger.info("Achieved excellent fitness score, stopping early")
                break

        # Zwróć najlepsze rozwiązanie i historię
        best_individual = halloffame[0]
        best_schedule = self.convert_to_schedule(best_individual)

        # Zapisz najlepsze rozwiązanie
        self.save_best_solution(best_individual, best_individual.fitness.values[0])

        return best_schedule, progress_history

    def setup_deap(self):
        """Konfiguracja biblioteki DEAP"""
        # Definiujemy problem maksymalizacji (chcemy maksymalizować ocenę planu)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()

        # Rejestracja funkcji generujących
        self.toolbox.register("lesson_slot", self.random_lesson_slot)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,
                              self.toolbox.lesson_slot, n=self.calculate_total_lessons())
        self.toolbox.register("population", tools.initRepeat, list,
                              self.toolbox.individual)

        # Operatory genetyczne
        self.toolbox.register("evaluate", self.evaluate_schedule)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self.mutation)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def calculate_total_lessons(self) -> int:
        """Oblicza całkowitą liczbę lekcji do zaplanowania"""
        total = 0
        for class_group in self.school.class_groups:
            for subject in class_group.subjects:
                total += subject.hours_per_week
        return total

    def random_lesson_slot(self) -> Tuple[int, int, str, str, int, int]:
        """Generuje losowy slot lekcyjny (dzień, godzina, klasa, przedmiot, nauczyciel, sala)"""
        max_attempts = 50

        for _ in range(max_attempts):
            day = random.randint(0, self.DAYS - 1)
            hour = random.randint(0, self.HOURS_PER_DAY - 1)

            if not self.school.class_groups:
                raise ValueError("Brak zdefiniowanych grup klasowych")

            # Poprawka: dodajemy więcej logów
            logger.debug(f"Próba wygenerowania slotu: dzień {day}, godzina {hour}")

            class_group = random.choice(self.school.class_groups)
            if not class_group.subjects:
                logger.error(f"Klasa {class_group.name} nie ma przypisanych przedmiotów")
                raise ValueError(f"Brak przedmiotów dla grupy {class_group.name}")

            subject = random.choice(class_group.subjects)
            logger.debug(f"Wylosowano: klasa {class_group.name}, przedmiot {subject.name}")

            # Znajdź odpowiedniego nauczyciela i salę
            available_teachers = [t for t in self.school.teachers.values()
                                  if subject.name in t.subjects]
            suitable_rooms = [r for r in self.school.classrooms.values()
                              if r.is_suitable_for_subject(subject)]

            if not available_teachers:
                logger.error(f"Brak nauczycieli mogących uczyć przedmiotu {subject.name}")
                continue

            if not suitable_rooms:
                logger.error(f"Brak odpowiednich sal dla przedmiotu {subject.name}")
                continue

            teacher = random.choice(available_teachers)
            classroom = random.choice(suitable_rooms)
            logger.debug(f"Przydzielono: nauczyciel {teacher.name}, sala {classroom.name}")

            return (day, hour, class_group.name, subject.name, teacher.id, classroom.id)

        raise ValueError(f"Nie udało się wygenerować poprawnego slotu po {max_attempts} próbach")

    def check_conflicts(self, lessons: List[Tuple]) -> bool:
        """Sprawdza czy występują konflikty między lekcjami"""
        for i, lesson1 in enumerate(lessons):
            # Sprawdź konflikty z istniejącymi lekcjami
            for lesson2 in lessons[i + 1:]:
                if lesson1[0] == lesson2[0] and lesson1[1] == lesson2[1]:  # ten sam dzień i godzina
                    # Ten sam nauczyciel
                    if lesson1[4] == lesson2[4]:
                        return True
                    # Ta sama sala
                    if lesson1[5] == lesson2[5]:
                        return True
                    # Ta sama klasa
                    if lesson1[2] == lesson2[2]:
                        return True
        return False

    def convert_to_schedule(self, individual: List) -> Schedule:
        """Konwertuje indywiduum na obiekt Schedule"""
        schedule = Schedule(school=self.school)  # Przekazujemy school podczas tworzenia

        for day, hour, class_name, subject_name, teacher_id, classroom_id in individual:
            try:
                # Poprawka: szukamy nauczyciela bezpośrednio po kluczu w słowniku
                teacher = self.school.teachers[teacher_id]  # zamiast używać next()
            except KeyError:
                logger.error(f"Nie znaleziono nauczyciela o id: {teacher_id}")
                raise ValueError(f"Nieprawidłowe id nauczyciela: {teacher_id}")

            try:
                # To samo dla sal
                classroom = self.school.classrooms[classroom_id]  # używamy bezpośredniego dostępu
            except KeyError:
                logger.error(f"Nie znaleziono sali o id: {classroom_id}")
                raise ValueError(f"Nieprawidłowe id sali: {classroom_id}")

            try:
                subject = next(s for s in self.school.subjects.values() if s.name == subject_name)
            except StopIteration:
                logger.error(f"Nie znaleziono przedmiotu o nazwie: {subject_name}")
                logger.error(f"Dostępne przedmioty: {[s.name for s in self.school.subjects.values()]}")
                raise ValueError(f"Nieprawidłowa nazwa przedmiotu: {subject_name}")

            schedule.add_lesson(
                Lesson(
                    subject=subject,
                    teacher=teacher,
                    classroom=classroom,
                    class_group=class_name,
                    day=day,
                    hour=hour
                )
            )

        return schedule

    def save_best_solution(self, solution: List, fitness: float):
        """Zapisuje najlepsze rozwiązanie do pliku"""
        path = Path('data/best_solution.json')
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w') as f:
                json.dump({
                    'solution': solution,
                    'fitness': fitness,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            logger.info(f"Saved best solution with fitness: {fitness}")
        except Exception as e:
            logger.error(f"Error saving best solution: {e}")

    def evaluate_schedule(self, individual: List) -> Tuple[float]:
        """Ocenia jakość planu. Zwraca krotkę bo DEAP tego wymaga"""
        schedule = self.convert_to_schedule(individual)
        result = self.evaluator.evaluate(schedule)
        return (result.total_score,)
