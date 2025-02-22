# src/utils/validators.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from src.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ScheduleValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_school_config(self, config: Dict) -> ValidationResult:
        """Walidacja konfiguracji szkoły"""
        self.errors = []
        self.warnings = []

        # Sprawdzenie podstawowej struktury
        if not isinstance(config, dict):
            self.errors.append("Configuration must be a dictionary")
            return self._get_result()

        # Walidacja liczby klas
        self._validate_class_counts(config.get('class_counts', {}))

        # Walidacja profili
        self._validate_profiles(config.get('profiles', []))

        return self._get_result()

    def _validate_class_counts(self, counts: Dict):
        """Walidacja liczby klas dla każdego rocznika"""
        required_years = ['first_year', 'second_year', 'third_year', 'fourth_year']

        for year in required_years:
            count = counts.get(year, 0)
            if not isinstance(count, int):
                self.errors.append(f"Invalid {year} count: must be an integer")
            elif count < 0:
                self.errors.append(f"Invalid {year} count: cannot be negative")
            elif count > 5:
                self.warnings.append(f"High {year} count: {count} classes might be difficult to schedule")

        total = sum(counts.get(year, 0) for year in required_years)
        if total == 0:
            self.errors.append("At least one class must be defined")

    def _validate_profiles(self, profiles: List):
        """Walidacja profili klas"""
        if not profiles:
            self.warnings.append("No profiles defined, will use default")
            return

        for idx, profile in enumerate(profiles):
            if not isinstance(profile, dict):
                self.errors.append(f"Profile {idx} must be a dictionary")
                continue

            if 'name' not in profile:
                self.errors.append(f"Profile {idx} missing name")

            if 'extended_subjects' not in profile:
                self.errors.append(f"Profile {idx} missing extended subjects")
            elif not isinstance(profile['extended_subjects'], list):
                self.errors.append(f"Profile {idx} extended subjects must be a list")
            elif len(profile['extended_subjects']) < 2:
                self.warnings.append(f"Profile {idx} has fewer than 2 extended subjects")

    def _get_result(self) -> ValidationResult:
        """Tworzy obiekt wyniku walidacji"""
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )


class LessonValidator:
    """Walidacja pojedynczych lekcji"""

    def __init__(self, school: 'School'):
        self.school = school
        self.logger = StructuredLogger(__name__)

    def validate_lesson(self, lesson: 'Lesson') -> ValidationResult:
        errors = []
        warnings = []

        # Podstawowa walidacja
        if lesson.hour < 0 or lesson.hour > 7:
            errors.append(f"Invalid hour: {lesson.hour}")

        if lesson.day < 0 or lesson.day > 4:
            errors.append(f"Invalid day: {lesson.day}")

        # Walidacja nauczyciela
        if not lesson.teacher.can_teach(lesson.subject.name):
            errors.append(f"Teacher {lesson.teacher.name} cannot teach {lesson.subject.name}")

        # Walidacja sali
        if not lesson.classroom.is_suitable_for_subject(lesson.subject):
            errors.append(f"Classroom {lesson.classroom.name} not suitable for {lesson.subject.name}")

        # Sprawdzenie obciążenia nauczyciela
        teacher_hours = self.school.get_teacher_hours(lesson.teacher)
        if teacher_hours['weekly'] >= lesson.teacher.max_hours_per_week:
            warnings.append(f"Teacher {lesson.teacher.name} exceeding weekly hours")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )