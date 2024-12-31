# config/teacher_data.py
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import REGULAR_SUBJECTS

# Najpopularniejsze polskie imiona
FIRST_NAMES = {
    'M': [  # Męskie
        'Adam', 'Andrzej', 'Bartosz', 'Dariusz', 'Grzegorz', 'Jacek', 'Jan',
        'Kamil', 'Krzysztof', 'Marek', 'Michał', 'Paweł', 'Piotr', 'Robert',
        'Sławomir', 'Tomasz', 'Wojciech', 'Zbigniew'
    ],
    'K': [  # Żeńskie
        'Agnieszka', 'Anna', 'Barbara', 'Dorota', 'Ewa', 'Halina', 'Iwona',
        'Joanna', 'Katarzyna', 'Magdalena', 'Małgorzata', 'Monika', 'Renata',
        'Teresa', 'Urszula', 'Wioletta', 'Zofia'
    ]
}

# Popularne polskie nazwiska
LAST_NAMES = {
    'M': [  # Męskie
        'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński',
        'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski',
        'Kozłowski', 'Jankowski', 'Mazur', 'Kwiatkowski', 'Krawczyk'
    ],
    'K': [  # Żeńskie
        'Nowak', 'Kowalska', 'Wiśniewska', 'Wójcik', 'Kowalczyk', 'Kamińska',
        'Lewandowska', 'Zielińska', 'Szymańska', 'Woźniak', 'Dąbrowska',
        'Kozłowska', 'Jankowska', 'Mazur', 'Kwiatkowska', 'Krawczyk'
    ]
}


@dataclass
class SubjectRequirement:
    weekly_hours: int
    max_hours_per_teacher: int = 18  # Default for full-time
    min_teachers: int = 1


class TeacherDataGenerator:
    @staticmethod
    def calculate_subject_requirements() -> Dict[str, SubjectRequirement]:
        requirements = {}

        # Calculate weekly hours for each subject across all classes
        for year in range(1, 5):
            classes_in_year = 5  # A-E

            # Regular subjects
            for subject, hours_per_year in REGULAR_SUBJECTS.items():
                year_hours = hours_per_year.get(year, 0) * classes_in_year
                if subject not in requirements:
                    requirements[subject] = SubjectRequirement(year_hours)
                else:
                    requirements[subject].weekly_hours += year_hours

        # Set special requirements for certain subjects
        if 'Wychowanie fizyczne' in requirements:
            requirements['Wychowanie fizyczne'].max_hours_per_teacher = 24
            requirements['Wychowanie fizyczne'].min_teachers = 4  # Minimum due to gender separation

        if 'Informatyka' in requirements:
            requirements['Informatyka'].max_hours_per_teacher = 20
            requirements['Informatyka'].min_teachers = 2  # Due to computer lab constraints

        if 'Język obcy nowożytny' in requirements:
            requirements['Język obcy nowożytny'].min_teachers = 3  # Multiple language options

        if 'Drugi język obcy' in requirements:
            requirements['Drugi język obcy'].min_teachers = 3  # Multiple language options

        return requirements

    @staticmethod
    def calculate_minimum_teachers(requirements: Dict[str, SubjectRequirement]) -> Dict[str, int]:
        teachers_count = {}
        for subject, req in requirements.items():
            # Calculate minimum teachers needed based on total hours and max hours per teacher
            min_by_hours = (req.weekly_hours + req.max_hours_per_teacher - 1) // req.max_hours_per_teacher
            teachers_count[subject] = max(min_by_hours, req.min_teachers)
        return teachers_count

    @staticmethod
    def optimize_teacher_count(base_counts: Dict[str, int],
                               total_target: int = 40) -> Dict[str, int]:
        # Start with minimum counts
        current_counts = deepcopy(base_counts)
        total_teachers = sum(current_counts.values())

        if total_teachers > total_target:
            # Need to reduce - try combining subjects first
            pass  # Implementation for reduction if needed

        return current_counts

    @classmethod
    def generate_teacher_data(cls) -> List[Dict]:
        requirements = cls.calculate_subject_requirements()
        min_teachers = cls.calculate_minimum_teachers(requirements)
        optimized_counts = cls.optimize_teacher_count(min_teachers)

        teachers = []
        teacher_id = 1

        for subject, count in optimized_counts.items():
            for _ in range(count):
                first_name, last_name = cls.generate_teacher_name()
                is_full_time = True if requirements[subject].weekly_hours >= 15 else False

                available_days = {0, 1, 2, 3, 4} if is_full_time else set(
                    random.sample(range(5), k=3 if random.random() < 0.7 else 2)
                )

                teachers.append({
                    'teacher_id': f"T{teacher_id}",
                    'first_name': first_name,
                    'last_name': last_name,
                    'subjects': {subject},  # Start with single subject
                    'is_full_time': is_full_time,
                    'available_days': available_days
                })
                teacher_id += 1

        # Try to assign second subjects where possible
        cls._assign_secondary_subjects(teachers)

        return teachers

    @staticmethod
    def _assign_secondary_subjects(teachers: List[Dict]):
        SUBJECT_PAIRS = [
            {'Matematyka', 'Fizyka'},
            {'Biologia', 'Chemia'},
            {'Geografia', 'Biologia'},
            {'Język obcy nowożytny', 'Drugi język obcy'}
        ]

        for teacher in teachers:
            if teacher['is_full_time'] and len(teacher['subjects']) == 1:
                main_subject = next(iter(teacher['subjects']))

                # Find valid pairs for this subject
                valid_pairs = [pair for pair in SUBJECT_PAIRS
                               if main_subject in pair]

                if valid_pairs and random.random() < 0.3:  # 30% chance for second subject
                    chosen_pair = random.choice(valid_pairs)
                    second_subject = next(iter(chosen_pair - {main_subject}))
                    teacher['subjects'].add(second_subject)

    @staticmethod
    def generate_teacher_name() -> Tuple[str, str]:
        """Generuje losowe imię i nazwisko nauczyciela"""
        gender = random.choice(['K', 'M'])
        first_name = random.choice(FIRST_NAMES[gender])
        last_name = random.choice(LAST_NAMES[gender])
        return first_name, last_name
