# config/validation_rules.py
from typing import List

from config.constants import (
    RESTRICTED_HOURS_SUBJECTS,
    MAX_CONSECUTIVE_HOURS
)
from models.school_class import SchoolClass


class ValidationRules:
    @staticmethod
    def validate_class_schedule(school_class: SchoolClass) -> List[str]:
        """Sprawdza wszystkie zasady dla planu lekcji danej klasy"""
        errors = []

        # Zbierz wszystkie błędy z różnych walidacji
        errors.extend(ValidationRules._validate_daily_hours(school_class))
        errors.extend(ValidationRules._validate_continuity(school_class))
        errors.extend(ValidationRules._validate_subject_restrictions(school_class))
        errors.extend(ValidationRules._validate_split_subjects(school_class))
        errors.extend(ValidationRules._validate_religion_placement(school_class))
        errors.extend(ValidationRules._validate_consecutive_subjects(school_class))

        return errors

    @staticmethod
    def _validate_daily_hours(school_class: SchoolClass) -> List[str]:
        """Sprawdza liczbę godzin dziennie (min 5, max 8, bez religii)"""
        errors = []
        for day in range(5):
            lessons = []
            for hour in range(1, 10):
                day_lessons = [l for l in school_class.schedule[day][hour]
                               if l.subject != 'Religia']
                if day_lessons:
                    lessons.append(hour)

            if not lessons:
                errors.append(f"Dzień {day}: brak lekcji")
            elif len(lessons) < 5:
                errors.append(f"Dzień {day}: za mało lekcji (minimum 5)")
            elif len(lessons) > 8:
                errors.append(f"Dzień {day}: za dużo lekcji (maksimum 8)")

        return errors

    @staticmethod
    def _validate_continuity(school_class: SchoolClass) -> List[str]:
        """Sprawdza ciągłość lekcji (brak okienek)"""
        errors = []
        for day in range(5):
            for group in [1, 2]:
                group_lessons = []
                for hour in range(1, 10):
                    lessons = [l for l in school_class.schedule[day][hour]
                               if l.group == group or l.group is None]
                    if lessons:
                        group_lessons.append(hour)

                if group_lessons:
                    min_hour = min(group_lessons)
                    max_hour = max(group_lessons)
                    for hour in range(min_hour, max_hour + 1):
                        if hour not in group_lessons:
                            errors.append(
                                f"Dzień {day}, grupa {group}: okienko na lekcji {hour}"
                            )

        return errors

    @staticmethod
    def _validate_subject_restrictions(school_class: SchoolClass) -> List[str]:
        """Sprawdza ograniczenia dotyczące pierwszej/ostatniej lekcji"""
        errors = []
        for day in range(5):
            day_lessons = []
            for hour in range(1, 10):
                if school_class.schedule[day][hour]:
                    day_lessons.append(hour)

            if day_lessons:
                first_hour = min(day_lessons)
                last_hour = max(day_lessons)

                for hour in [first_hour, last_hour]:
                    lessons = school_class.schedule[day][hour]
                    for lesson in lessons:
                        if lesson.subject in RESTRICTED_HOURS_SUBJECTS:
                            errors.append(
                                f"Dzień {day}: {lesson.subject} nie może być na "
                                f"{'pierwszej' if hour == first_hour else 'ostatniej'} "
                                f"lekcji"
                            )

        return errors

    @staticmethod
    def _validate_split_subjects(school_class: SchoolClass) -> List[str]:
        """Sprawdza zasady dla przedmiotów dzielonych"""
        errors = []
        split_subjects = {'Angielski', 'Informatyka', 'WF'}

        for day in range(5):
            for hour in range(1, 10):
                lessons = school_class.schedule[day][hour]
                if not lessons:
                    continue

                # Sprawdź czy obie grupy mają przedmioty dzielone lub jedna jest wolna
                split_lesson = any(l.subject in split_subjects for l in lessons)
                if split_lesson:
                    groups_present = {l.group for l in lessons if l.group is not None}
                    if len(groups_present) == 1:
                        # Jedna grupa ma przedmiot dzielony - sprawdź czy to pierwsza/ostatnia lekcja
                        absent_group = 2 if 1 in groups_present else 1
                        group_lessons = [h for h in range(1, 10)
                                         if any(l.group == absent_group or l.group is None
                                                for l in school_class.schedule[day][h])]
                        if group_lessons and hour not in [min(group_lessons), max(group_lessons)]:
                            errors.append(
                                f"Dzień {day}, lekcja {hour}: grupa {absent_group} ma wolne "
                                f"w środku dnia podczas przedmiotu dzielonego"
                            )

        return errors

    @staticmethod
    def _validate_religion_placement(school_class: SchoolClass) -> List[str]:
        """Sprawdza umiejscowienie lekcji religii"""
        errors = []
        for day in range(5):
            religion_hours = []
            regular_hours = []

            for hour in range(1, 10):
                lessons = school_class.schedule[day][hour]
                if any(l.subject == 'Religia' for l in lessons):
                    religion_hours.append(hour)
                elif lessons:
                    regular_hours.append(hour)

            if religion_hours:
                regular_min = min(regular_hours) if regular_hours else None
                regular_max = max(regular_hours) if regular_hours else None

                for religion_hour in religion_hours:
                    if regular_min and regular_max:
                        if religion_hour > regular_min and religion_hour < regular_max:
                            errors.append(
                                f"Dzień {day}: religia musi być przed pierwszą "
                                f"lub po ostatniej lekcji"
                            )

        return errors

    @staticmethod
    def _validate_consecutive_subjects(school_class: SchoolClass) -> List[str]:
        """Sprawdza maksymalną liczbę godzin pod rząd dla przedmiotów z ograniczeniami"""
        errors = []

        for day in range(5):
            # Dla każdego przedmiotu z ograniczeniem
            for subject, max_hours in MAX_CONSECUTIVE_HOURS.items():
                # Dla każdej grupy (None = cała klasa)
                for group in [None, 1, 2]:
                    consecutive_hours = 0
                    last_hour_had_subject = False

                    for hour in range(1, 10):
                        lessons = school_class.schedule[day][hour]
                        has_subject = any(
                            l.subject == subject and (l.group == group or l.group is None)
                            for l in lessons
                        )

                        if has_subject:
                            if last_hour_had_subject:
                                consecutive_hours += 1
                                if consecutive_hours > max_hours:
                                    errors.append(
                                        f"Dzień {day}: za dużo godzin {subject} pod rząd "
                                        f"{'dla grupy ' + str(group) if group else ''}"
                                    )
                            else:
                                consecutive_hours = 1
                            last_hour_had_subject = True
                        else:
                            consecutive_hours = 0
                            last_hour_had_subject = False

        return errors

    @staticmethod
    def calculate_schedule_score(school_class: SchoolClass) -> float:
        """Oblicza punktację dla planu lekcji"""
        score = 100.0  # Maksymalna punktacja

        # Kara za późne kończenie w piątki
        friday_end_hour = 0
        for hour in range(9, 0, -1):
            if school_class.schedule[4][hour]:  # Piątek
                friday_end_hour = hour
                break
        score -= (friday_end_hour - 5) * 2 if friday_end_hour > 5 else 0

        # Kara za nierównomierne rozłożenie "ciężkich" przedmiotów
        heavy_subjects = {'Matematyka', 'Fizyka', 'Chemia'}
        for day in range(5):
            heavy_count = sum(
                1 for hour in range(1, 10)
                for lesson in school_class.schedule[day][hour]
                if lesson.subject in heavy_subjects
            )
            if heavy_count > 2:
                score -= (heavy_count - 2) * 5

        # Kara za duże różnice w czasie rozpoczęcia/zakończenia między grupami
        for day in range(5):
            group1_hours = []
            group2_hours = []

            for hour in range(1, 10):
                lessons = school_class.schedule[day][hour]
                if any(l.group == 1 or l.group is None for l in lessons):
                    group1_hours.append(hour)
                if any(l.group == 2 or l.group is None for l in lessons):
                    group2_hours.append(hour)

            if group1_hours and group2_hours:
                start_diff = abs(min(group1_hours) - min(group2_hours))
                end_diff = abs(max(group1_hours) - max(group2_hours))
                score -= (start_diff + end_diff) * 2

        return max(0, score)  # Nie może być ujemna
