# src/utils/fitness_evaluator.py

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.models.schedule import Schedule
from src.models.subject import Subject

logger = logging.getLogger(__name__)


@dataclass
class FitnessResult:
    total_score: float  # 0-100
    detailed_scores: Dict[str, float]  # szczegółowe wyniki dla każdego kryterium
    penalties: Dict[str, float]  # lista kar
    rewards: Dict[str, float]  # lista nagród

    def to_dict(self) -> Dict:
        return {
            'total_score': self.total_score,
            'detailed_scores': self.detailed_scores,
            'penalties': self.penalties,
            'rewards': self.rewards
        }


class FitnessEvaluator:
    def __init__(self, school: 'School', config: Dict):
        self.school = school
        self.config = config

        # Wczytaj najlepsze parametry
        self.best_score = 0
        self.best_parameters = None
        self._load_best_parameters()

        # Wagi dla różnych komponentów (suma = 1.0)
        self.weights = {
            'completeness': 0.5,
            'load_balance': 0.3,
            'teacher_optimization': 0.2
        }

        # Inicjalizacja wymaganych godzin dla każdej klasy
        self.required_hours = self._initialize_required_hours()

        # Optymalna liczba nauczycieli (bazowana na konfiguracji)
        self.optimal_teacher_count = self._calculate_optimal_teacher_count()

        # Lista wszystkich nauczycieli
        self.teachers = self.school.teachers

    def _initialize_required_hours(self) -> Dict[str, List[Subject]]:
        """Inicjalizuje wymagane godziny dla każdej klasy"""
        required_hours = {}
        for class_group in self.school.class_groups:
            # Podstawowe przedmioty
            required_subjects = self.school.get_basic_subjects()

            # Dodaj rozszerzone przedmioty dla profilu
            extended_subjects = self.school.get_extended_subjects(class_group.profile)

            required_hours[class_group.name] = required_subjects + extended_subjects

        return required_hours

    def _calculate_optimal_teacher_count(self) -> int:
        """Oblicza optymalną liczbę nauczycieli"""
        total_hours = 0
        for class_group, subjects in self.required_hours.items():
            total_hours += sum(subject.hours_per_week for subject in subjects)

        # Zakładamy, że nauczyciel powinien mieć średnio 75% maksymalnego obciążenia
        teacher_capacity = self.config.get('max_hours_per_week', 40) * 0.75
        return max(1, int(total_hours / teacher_capacity))

    def _load_best_parameters(self):
        """Ładuje najlepsze znalezione parametry z pliku"""
        path = Path('data/best_parameters.json')
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.best_score = data['score']
                    self.best_parameters = data['parameters']
                    logger.info(f"Loaded best parameters with score: {self.best_score}")
            except Exception as e:
                logger.error(f"Error loading best parameters: {e}")

    def save_if_better(self, score: float, parameters: dict):
        """Zapisuje parametry jeśli są lepsze od poprzednich"""
        if score > self.best_score:
            self.best_score = score
            self.best_parameters = parameters

            path = Path('data/best_parameters.json')
            path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(path, 'w') as f:
                    json.dump({
                        'score': score,
                        'parameters': parameters,
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2)
                logger.info(f"Saved new best parameters with score: {score}")
            except Exception as e:
                logger.error(f"Error saving best parameters: {e}")

    def evaluate(self, schedule: Schedule) -> FitnessResult:
        """Główna funkcja oceniająca plan lekcji"""
        penalties = {}
        rewards = {}
        detailed_scores = {}

        # 1. Kompletność planu (40% całości)
        completeness_score, completeness_penalties, completeness_rewards = \
            self._evaluate_completeness(schedule)
        detailed_scores['completeness'] = completeness_score
        penalties.update(completeness_penalties)
        rewards.update(completeness_rewards)

        # 2. Równomierne obciążenie (30% całości)
        balance_score, balance_penalties, balance_rewards = \
            self._evaluate_load_balance(schedule)
        detailed_scores['load_balance'] = balance_score
        penalties.update(balance_penalties)
        rewards.update(balance_rewards)

        # 3. Optymalizacja nauczycieli (30% całości)
        teacher_score, teacher_penalties, teacher_rewards = \
            self._evaluate_teacher_optimization(schedule)
        detailed_scores['teacher_optimization'] = teacher_score
        penalties.update(teacher_penalties)
        rewards.update(teacher_rewards)

        # Obliczanie wyniku końcowego (0-100)
        total_score = sum(
            score * self.weights[criterion]
            for criterion, score in detailed_scores.items()
        )

        # Zapisz wynik jeśli jest lepszy od poprzednich
        self.save_if_better(total_score, schedule.to_dict())

        return FitnessResult(
            total_score=total_score,
            detailed_scores=detailed_scores,
            penalties=penalties,
            rewards=rewards
        )

    def _evaluate_completeness(self, schedule: Schedule) -> Tuple[float, Dict, Dict]:
        penalties = {}
        rewards = {}
        base_score = 100.0

        for class_group in schedule.class_groups:
            daily_lessons = defaultdict(list)
            for lesson in schedule.get_class_lessons(class_group):
                daily_lessons[lesson.day].append(lesson)

            # Sprawdź każdy dzień
            for day in range(5):
                lessons = daily_lessons[day]
                if not lessons:
                    penalty = 50  # Zwiększamy karę z 20 do 50 za pusty dzień
                    penalties[f"empty_day_{class_group}_{day}"] = penalty
                    base_score -= penalty
                    continue

                hours = sorted(lesson.hour for lesson in lessons)
                if hours:
                    # Drastycznie zwiększamy karę za późne rozpoczęcie
                    if hours[0] > 0:
                        penalty = hours[0] * 15  # Zwiększamy z 3 do 15
                        penalties[f"late_start_{class_group}_{day}"] = penalty
                        base_score -= penalty

                    # Drastycznie zwiększamy karę za okienka
                    gaps = sum(hours[i + 1] - hours[i] - 1 for i in range(len(hours) - 1))
                    if gaps > 0:
                        penalty = gaps * 25  # Zwiększamy z 10 do 25
                        penalties[f"gaps_{class_group}_{day}"] = penalty
                        base_score -= penalty

        return max(0, base_score), penalties, rewards

    def _evaluate_load_balance(self, schedule: Schedule) -> Tuple[float, Dict, Dict]:
        """Ocena równomiernego obciążenia"""
        penalties = {}
        rewards = {}
        base_score = 100.0

        # Sprawdzenie obciążenia nauczycieli
        teacher_load_score = self._check_teacher_load(schedule)
        if teacher_load_score < 0:
            penalties['unbalanced_teacher_load'] = abs(teacher_load_score)
            base_score += teacher_load_score
        else:
            rewards['balanced_teacher_load'] = teacher_load_score
            base_score = min(100, base_score + teacher_load_score)

        # Sprawdzenie wykorzystania sal
        room_usage_score = self._check_room_usage(schedule)
        if room_usage_score < 0:
            penalties['poor_room_usage'] = abs(room_usage_score)
            base_score += room_usage_score
        else:
            rewards['optimal_room_usage'] = room_usage_score
            base_score = min(100, base_score + room_usage_score)

        return max(0, base_score), penalties, rewards

    def _evaluate_teacher_optimization(self, schedule: Schedule) -> Tuple[float, Dict, Dict]:
        """Ocena optymalizacji nauczycieli"""
        penalties = {}
        rewards = {}
        base_score = 100.0

        # Sprawdzenie liczby wykorzystanych nauczycieli
        used_teachers = schedule.get_used_teachers()
        if len(used_teachers) > self.optimal_teacher_count:
            penalty = 5 * (len(used_teachers) - self.optimal_teacher_count)
            penalties['excess_teachers'] = penalty
            base_score -= penalty
        else:
            reward = 5 * (self.optimal_teacher_count - len(used_teachers))
            rewards['optimal_teacher_count'] = reward
            base_score = min(100, base_score + reward)

        # Sprawdzenie specjalizacji nauczycieli
        specialization_score = self._check_teacher_specialization(schedule)
        if specialization_score > 0:
            rewards['teacher_specialization'] = specialization_score
            base_score = min(100, base_score + specialization_score)

        return max(0, base_score), penalties, rewards

    def _check_distribution_quality(self, schedule: Schedule) -> float:
        """Sprawdza jakość rozkładu lekcji"""
        score = 0.0

        # Zmiana: class_group jest już nazwą klasy (stringiem)
        for class_group in schedule.class_groups:
            logger.debug(f"Sprawdzam rozkład lekcji dla klasy: {class_group}")
            daily_lessons = defaultdict(list)

            # Grupuj lekcje po dniach - używamy bezpośrednio class_group bo to string
            for lesson in schedule.get_class_lessons(class_group):
                daily_lessons[lesson.day].append(lesson)

            logger.debug(f"Rozkład dzienny: {len(daily_lessons)} dni")

            # Ocena każdego dnia
            for day_lessons in daily_lessons.values():
                # Sprawdź różnorodność przedmiotów
                unique_subjects = len({lesson.subject.name for lesson in day_lessons})
                score += unique_subjects * 0.5
                logger.debug(f"Różnorodność przedmiotów: {unique_subjects} (+{unique_subjects * 0.5})")

                # Kara za zbyt dużo tego samego przedmiotu w jeden dzień
                subject_counts = defaultdict(int)
                for lesson in day_lessons:
                    subject_counts[lesson.subject.name] += 1
                    if subject_counts[lesson.subject.name] > 2:
                        score -= 1
                        logger.debug(f"Kara za powtórzenia przedmiotu {lesson.subject.name} (-1)")

                # Sprawdź przerwy między lekcjami
                hours = sorted(lesson.hour for lesson in day_lessons)
                for i in range(1, len(hours)):
                    if hours[i] - hours[i - 1] > 1:  # przerwa większa niż 1 godzina
                        score -= 0.5
                        logger.debug(f"Kara za przerwę między {hours[i - 1]} a {hours[i]} (-0.5)")

        logger.debug(f"Końcowy wynik rozkładu: {score}")
        return score

    def _check_teacher_load(self, schedule: Schedule) -> float:
        """Sprawdza równomierność obciążenia nauczycieli"""
        score = 0.0

        # Zmiana: iterujemy po wartościach słownika teachers
        for teacher in self.teachers.values():
            logger.debug(f"Sprawdzam obciążenie nauczyciela: {teacher.name}")
            hours = schedule.get_teacher_hours(teacher)

            # Sprawdź dzienny limit
            for day, day_hours in hours['daily'].items():
                if day_hours > teacher.max_hours_per_day:
                    penalty = (day_hours - teacher.max_hours_per_day) * 2
                    score -= penalty
                    logger.debug(
                        f"Dzień {day}: Przekroczony dzienny limit o {day_hours - teacher.max_hours_per_day} (-{penalty})")
                elif day_hours == teacher.max_hours_per_day:
                    score += 1
                    logger.debug(f"Dzień {day}: Optymalne wykorzystanie (+1)")

            # Sprawdź tygodniowy limit
            weekly_hours = hours['weekly']
            if weekly_hours > teacher.max_hours_per_week:
                penalty = (weekly_hours - teacher.max_hours_per_week) * 3
                score -= penalty
                logger.debug(
                    f"Przekroczony tygodniowy limit o {weekly_hours - teacher.max_hours_per_week} (-{penalty})")
            elif weekly_hours >= teacher.max_hours_per_week * 0.8:
                score += 2
                logger.debug(f"Optymalne obciążenie tygodniowe (+2)")

        logger.debug(f"Końcowy wynik obciążenia nauczycieli: {score}")
        return score

    def _check_room_usage(self, schedule: Schedule) -> float:
        """Sprawdza efektywność wykorzystania sal"""
        score = 0.0
        room_usage = defaultdict(int)

        # Licz wykorzystanie każdej sali
        for lesson in schedule.lessons:
            room_usage[lesson.classroom.id] += 1

        # Ocena wykorzystania
        # Poprawka: Dodajemy sprawdzenie czy szkoła ma te atrybuty
        max_possible_hours = getattr(self.school, 'days', 5) * getattr(self.school, 'hours_per_day', 8)

        # Poprawka: iterujemy po wartościach słownika classrooms
        for classroom in self.school.classrooms.values():
            usage = room_usage[classroom.id]
            usage_percent = usage / max_possible_hours * 100

            logger.debug(f"Sala {classroom.name}: wykorzystanie {usage_percent:.1f}%")

            if usage_percent < 30:
                score -= 2
                logger.debug(f"Kara za małe wykorzystanie (-2)")
            elif usage_percent > 80:
                score -= 1
                logger.debug(f"Kara za przeciążenie (-1)")
            elif 50 <= usage_percent <= 70:
                score += 2
                logger.debug(f"Nagroda za optymalne wykorzystanie (+2)")

        return score

    def _check_teacher_specialization(self, schedule: Schedule) -> float:
        """Sprawdza dopasowanie nauczycieli do przedmiotów"""
        score = 0.0
        teacher_subjects = defaultdict(set)

        # Zbierz przedmioty dla każdego nauczyciela
        for lesson in schedule.lessons:
            teacher_subjects[lesson.teacher.id].add(lesson.subject.name)

        # Poprawka: używamy values() zamiast iteracji po kluczach
        for teacher in self.teachers.values():
            subjects = teacher_subjects[teacher.id]
            logger.debug(f"Nauczyciel {teacher.name}: uczy przedmiotów {subjects}")

            # Nagroda za nauczanie przedmiotów zgodnych ze specjalizacją
            matching_subjects = subjects.intersection(set(teacher.subjects))
            score += len(matching_subjects) * 2
            logger.debug(f"Zgodne przedmioty: {matching_subjects} (+{len(matching_subjects) * 2})")

            # Kara za zbyt wiele różnych przedmiotów
            if len(subjects) > 3:
                penalty = (len(subjects) - 3)
                score -= penalty
                logger.debug(f"Kara za zbyt wiele przedmiotów (-{penalty})")

        return score
