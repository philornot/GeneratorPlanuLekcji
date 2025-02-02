# src/models/school.py

from dataclasses import dataclass
from typing import List, Dict
import string


@dataclass
class ClassGroup:
    year: int  # 1-4
    letter: str  # A, B, C...
    profile: str
    extended_subjects: List[str]

    @property
    def name(self) -> str:
        return f"{self.year}{self.letter}"


class School:
    def __init__(self, config: Dict):
        self.class_groups: List[ClassGroup] = []
        self.initialize_classes(config)

    def initialize_classes(self, config: Dict):
        """Inicjalizuje klasy na podstawie konfiguracji"""
        year_keys = ['first_year', 'second_year', 'third_year', 'fourth_year']

        for year_idx, year_key in enumerate(year_keys, 1):
            class_count = config['class_counts'][year_key]

            # Przypisz profile do klas
            available_profiles = config['profiles']
            for class_idx in range(class_count):
                profile = available_profiles[class_idx % len(available_profiles)]

                self.class_groups.append(
                    ClassGroup(
                        year=year_idx,
                        letter=string.ascii_uppercase[class_idx],
                        profile=profile['name'],
                        extended_subjects=[profile['extended_subjects']]
                    )
                )