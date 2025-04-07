# src/genetic/genetic_evaluator.py

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Union, List, Tuple, TYPE_CHECKING

from src.models.schedule import Schedule
from src.models.school import School
from src.utils.logger import GPLLogger

if TYPE_CHECKING:
    from src.genetic.genetic_operators import GeneticOperators


@dataclass
class EvaluationResult:
    """Wynik oceny planu lekcji"""
    total_score: float  # Wynik całkowity (0-100)
    metrics: Dict[str, float]  # Szczegółowe metryki
    penalties: Dict[str, float]  # Kary
    rewards: Dict[str, float]  # Nagrody


class GeneticEvaluator:
    """Klasa oceniająca jakość wygenerowanych planów lekcji"""

    def __init__(self, school: 'School', operators: 'GeneticOperators', params: Dict):
        self.school = school
        self.params = params
        self.operators = operators
        self.logger = GPLLogger(__name__)

        # Cache dla optymalizacji
        self._metrics_cache = {}
        self.cache_size_limit = 1000
        self._fitness_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

        # Wagi dla różnych komponentów oceny
        self.weights = {
            'completeness': 0.3,  # Kompletność planu
            'distribution': 0.2,  # Rozkład zajęć
            'teacher_load': 0.2,  # Obciążenie nauczycieli
            'room_usage': 0.15,  # Wykorzystanie sal
            'constraints': 0.15  # Spełnienie ograniczeń
        }

    def evaluate_schedule(self, schedule: Union[List, 'Schedule']) -> Tuple[float]:
        """
        Główna funkcja oceniająca plan lekcji.

        Args:
            schedule: Lista reprezentująca osobnika lub obiekt Schedule

        Returns:
            Tuple[float]: Pojedyncza wartość fitness w krotce (wymagane przez DEAP)
        """
        try:
            # Jeśli dostaliśmy listę (osobnika), sprawdź cache i ew. konwertuj na Schedule
            if isinstance(schedule, list):
                # Wylicz hash dla osobnika jako cache key
                try:
                    # Sortujemy i konwertujemy na tuple dla hashowania
                    cache_key = tuple(sorted(tuple(x) if x is not None else None for x in schedule))

                    # Sprawdź czy w cache
                    if cache_key in self._fitness_cache:
                        self._cache_hits += 1
                        return self._fitness_cache[cache_key]

                    self._cache_misses += 1
                except Exception as e:
                    # Jeśli problem z utworzeniem klucza, ignoruj cache
                    self.logger.debug(f"Cache key generation error: {str(e)}")
                    pass

                # Konwertuj na Schedule jeśli potrzeba
                schedule = self.operators.convert_to_schedule(schedule)
                if not schedule:
                    return (0.0,)

            # Sprawdzenie czy mamy poprawny obiekt Schedule
            if not isinstance(schedule, Schedule):
                self.logger.error(f"Invalid schedule type: {type(schedule)}")
                return (0.0,)

            # Obliczenie wszystkich metryk
            try:
                metrics = {
                    'completeness': self._evaluate_completeness(schedule),
                    'distribution': self._evaluate_distribution(schedule),
                    'teacher_load': self._evaluate_teacher_load(schedule),
                    'room_usage': self._evaluate_room_usage(schedule),
                    'constraints': self._evaluate_constraints(schedule)
                }
            except Exception as e:
                self.logger.error(f"Error calculating metrics: {str(e)}")
                return (0.0,)

            # Obliczenie kar i nagród
            penalties = self._calculate_penalties(schedule, metrics)
            rewards = self._calculate_rewards(schedule, metrics)

            # Obliczenie wyniku
            total_score = sum(
                score * self.weights[metric]
                for metric, score in metrics.items()
            )

            # Aplikacja kar i nagród
            total_score = max(0, min(100, total_score - sum(penalties.values()) + sum(rewards.values())))

            # Zapisanie do cache'a
            result = (total_score,)
            if 'cache_key' in locals() and cache_key is not None:
                self._fitness_cache[cache_key] = result

                # Limit rozmiaru cache
                if len(self._fitness_cache) > 10000:  # Ogranicz rozmiar cache
                    # Usuń 20% najstarszych wpisów
                    to_remove = int(len(self._fitness_cache) * 0.2)
                    for old_key in list(self._fitness_cache.keys())[:to_remove]:
                        del self._fitness_cache[old_key]

            # Logowanie statystyk cache co 1000 wywołań
            if (self._cache_hits + self._cache_misses) % 1000 == 0:
                hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) * 100 if (
                                                                                                           self._cache_hits + self._cache_misses) > 0 else 0
                self.logger.debug(f"Fitness cache: {hit_rate:.1f}% hit rate, cache size: {len(self._fitness_cache)}")

            # Zwróć wynik jako krotkę (wymagane przez DEAP)
            return result

        except Exception as e:
            self.logger.error(f"Error during schedule evaluation: {str(e)}")
            return (0.0,)

    def _evaluate_completeness(self, schedule: 'Schedule') -> float:
        """Ocenia kompletność planu lekcji"""
        try:
            total_required = 0
            total_scheduled = 0
            score = 100.0

            for class_group in self.school.class_groups:
                required_hours = sum(
                    subject.hours_per_week
                    for subject in class_group.subjects
                )
                scheduled_hours = len(schedule.get_class_lessons(class_group.name))

                # Dramatyczna kara za puste klasy (zwłaszcza młodsze)
                if scheduled_hours == 0:
                    penalty = 50.0  # Bardzo duża kara
                    # Dodatkowa kara dla klas pierwszych
                    if class_group.year == 1:
                        penalty += 20.0
                    score -= penalty

                # Kara za niekompletny plan
                completion_percent = scheduled_hours / required_hours if required_hours > 0 else 0
                if completion_percent < 0.8:  # Minimum 80% wypełnienia
                    score -= (0.8 - completion_percent) * 100

                total_required += required_hours
                total_scheduled += scheduled_hours

            # Globalny współczynnik wypełnienia
            overall_completion = (total_scheduled / total_required * 100) if total_required > 0 else 0
            return max(0, min(score, overall_completion))
        except Exception as e:
            self.logger.error(f"Error evaluating completeness: {str(e)}")
            return 0.0

    def _evaluate_distribution(self, schedule: 'Schedule') -> float:
        """Ocenia rozkład zajęć w tygodniu"""
        try:
            score = 100.0
            penalties = []

            for class_group in schedule.class_groups:
                daily_lessons = defaultdict(list)

                # Grupuj lekcje po dniach
                for lesson in schedule.get_class_lessons(class_group):
                    daily_lessons[lesson.day].append(lesson)

                # Sprawdź każdy dzień
                for day, lessons in daily_lessons.items():
                    # Kara za pusty dzień
                    if not lessons:
                        penalties.append(20)
                        continue

                    # Kara za okienka
                    hours = sorted(lesson.hour for lesson in lessons)
                    gaps = sum(
                        hours[i + 1] - hours[i] - 1
                        for i in range(len(hours) - 1)
                    )
                    if gaps > 0:
                        penalties.append(15 * gaps)

                    # Kara za zbyt późne/wczesne lekcje
                    if hours[0] > 2:  # rozpoczęcie po 3 lekcji
                        penalties.append(10)
                    if hours[-1] > 6:  # kończenie po 7 lekcji
                        penalties.append(10)

            return max(0, score - sum(penalties))

        except Exception as e:
            self.logger.error(f"Error evaluating distribution: {str(e)}")
            return 0.0

    def _evaluate_teacher_load(self, schedule: 'Schedule') -> float:
        """Ocenia obciążenie nauczycieli"""
        try:
            score = 100.0
            penalties = []

            for teacher in self.school.teachers.values():
                hours = schedule.get_teacher_hours(teacher)

                # Sprawdź dzienny limit
                for day, day_hours in hours['daily'].items():
                    if day_hours > teacher.max_hours_per_day:
                        over = day_hours - teacher.max_hours_per_day
                        penalties.append(10 * over)

                # Sprawdź tygodniowy limit
                weekly = hours['weekly']
                if weekly > teacher.max_hours_per_week:
                    over = weekly - teacher.max_hours_per_week
                    penalties.append(15 * over)
                elif weekly < teacher.max_hours_per_week * 0.5:
                    # Kara za zbyt małe wykorzystanie
                    penalties.append(10)

            return max(0, score - sum(penalties))

        except Exception as e:
            self.logger.error(f"Error evaluating teacher load: {str(e)}")
            return 0.0

    def _evaluate_room_usage(self, schedule: 'Schedule') -> float:
        """Ocenia wykorzystanie sal lekcyjnych"""
        try:
            score = 100.0
            penalties = []

            for classroom in self.school.classrooms.values():
                usage = schedule.get_classroom_usage(classroom)

                # Kara za zbyt małe wykorzystanie
                if usage < 30:
                    penalties.append(10)
                # Kara za przeciążenie
                elif usage > 90:
                    penalties.append(5)
                # Nagroda za optymalne wykorzystanie
                elif 60 <= usage <= 80:
                    score += 5

            return max(0, min(100, score - sum(penalties)))

        except Exception as e:
            self.logger.error(f"Error evaluating room usage: {str(e)}")
            return 0.0

    def _evaluate_constraints(self, schedule: 'Schedule') -> float:
        """Ocenia spełnienie ograniczeń"""
        try:
            score = 100.0
            penalties = []

            # Sprawdź konflikty nauczycieli
            teacher_conflicts = self._check_teacher_conflicts(schedule)
            penalties.extend([20] * teacher_conflicts)

            # Sprawdź konflikty sal
            room_conflicts = self._check_room_conflicts(schedule)
            penalties.extend([20] * room_conflicts)

            # Sprawdź konflikty klas
            class_conflicts = self._check_class_conflicts(schedule)
            penalties.extend([20] * class_conflicts)

            return max(0, score - sum(penalties))

        except Exception as e:
            self.logger.error(f"Error evaluating constraints: {str(e)}")
            return 0.0

    def _calculate_penalties(self, schedule: 'Schedule', metrics: Dict[str, float]) -> Dict[str, float]:
        """Oblicza kary za naruszenie ograniczeń"""
        penalties = {}

        # Kara za niską kompletność
        if metrics['completeness'] < 90:
            penalties['low_completeness'] = (90 - metrics['completeness']) * 0.5

        # Kara za złą dystrybucję
        if metrics['distribution'] < 70:
            penalties['poor_distribution'] = (70 - metrics['distribution']) * 0.3

        # Kara za przeciążenie nauczycieli
        if metrics['teacher_load'] < 80:
            penalties['teacher_overload'] = (80 - metrics['teacher_load']) * 0.4

        return penalties

    def _calculate_rewards(self, schedule: 'Schedule', metrics: Dict[str, float]) -> Dict[str, float]:
        """Oblicza nagrody za dobre rozwiązania"""
        rewards = {}

        # Nagroda za wysoką kompletność
        if metrics['completeness'] > 95:
            rewards['high_completeness'] = (metrics['completeness'] - 95) * 0.5

        # Nagroda za dobrą dystrybucję
        if metrics['distribution'] > 90:
            rewards['good_distribution'] = (metrics['distribution'] - 90) * 0.3

        # Nagroda za optymalne obciążenie
        if metrics['teacher_load'] > 90:
            rewards['optimal_load'] = (metrics['teacher_load'] - 90) * 0.4

        return rewards

    def _calculate_schedule_hash(self, schedule: 'Schedule') -> int:
        """Oblicza hash planu lekcji do cache'owania"""
        try:
            lessons_tuple = tuple(
                (l.day, l.hour, l.class_group, l.subject.name,
                 l.teacher.id, l.classroom.id)
                for l in sorted(
                    schedule.lessons,
                    key=lambda x: (x.day, x.hour, x.class_group)
                )
            )
            return hash(lessons_tuple)

        except Exception as e:
            self.logger.warning(f"Error calculating schedule hash: {str(e)}")
            return 0

    def _update_cache(self, schedule_hash: int, result: EvaluationResult):
        """Aktualizuje cache wyników"""
        try:
            if len(self._metrics_cache) >= self.cache_size_limit:
                # Usuń najstarszy wpis
                oldest_key = next(iter(self._metrics_cache))
                del self._metrics_cache[oldest_key]

            self._metrics_cache[schedule_hash] = result

        except Exception as e:
            self.logger.warning(f"Error updating cache: {str(e)}")

    def _check_teacher_conflicts(self, schedule: 'Schedule') -> int:
        """Sprawdza konflikty w harmonogramie nauczycieli"""
        conflicts = 0
        teacher_schedule = defaultdict(lambda: defaultdict(list))

        for lesson in schedule.lessons:
            teacher_schedule[lesson.teacher.id][(lesson.day, lesson.hour)].append(lesson)
            if len(teacher_schedule[lesson.teacher.id][(lesson.day, lesson.hour)]) > 1:
                conflicts += 1

        return conflicts

    def _check_room_conflicts(self, schedule: 'Schedule') -> int:
        """Sprawdza konflikty w wykorzystaniu sal"""
        conflicts = 0
        room_schedule = defaultdict(lambda: defaultdict(list))

        for lesson in schedule.lessons:
            room_schedule[lesson.classroom.id][(lesson.day, lesson.hour)].append(lesson)
            if len(room_schedule[lesson.classroom.id][(lesson.day, lesson.hour)]) > 1:
                conflicts += 1

        return conflicts

    def _check_class_conflicts(self, schedule: 'Schedule') -> int:
        """Sprawdza konflikty w planie klas"""
        conflicts = 0
        class_schedule = defaultdict(lambda: defaultdict(list))

        for lesson in schedule.lessons:
            class_schedule[lesson.class_group][(lesson.day, lesson.hour)].append(lesson)
            if len(class_schedule[lesson.class_group][(lesson.day, lesson.hour)]) > 1:
                conflicts += 1

        return conflicts
