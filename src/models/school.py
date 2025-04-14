# src/models/school.py

import string
from dataclasses import dataclass
from typing import List, Dict

from src.models.classroom import Classroom
from src.models.lesson import Lesson
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.utils.logger import GPLLogger

logger = GPLLogger(__name__)


@dataclass
class ClassGroup:
    year: int  # 1-4
    letter: str  # A, B, C...
    profile: str
    subjects: List[Subject] = None

    @property
    def name(self) -> str:
        return f"{self.year}{self.letter}"


class School:
    def __init__(self, config: Dict):
        self.subjects: Dict[str, Subject] = {}
        self.teachers: Dict[int, Teacher] = {}
        self.classrooms: Dict[int, Classroom] = {}
        self.class_groups: List[ClassGroup] = []

        # Poprawka: musimy zapisać profile przed inicjalizacją klas
        self.profiles = config.get('profiles', [])
        if not self.profiles:
            logger.warning("Brak zdefiniowanych profili, używam domyślnego")
            self.profiles = [{
                'name': 'ogólny',
                'extended_subjects': ['matematyka', 'angielski']
            }]

        # Inicjalizacja w odpowiedniej kolejności
        self._initialize_basic_infrastructure()
        self.initialize_classes(config)

        logger.info(f"Zainicjalizowano szkołę z {len(self.class_groups)} klasami")

    def _initialize_basic_infrastructure(self):
        """Inicjalizuje podstawowe zasoby szkoły"""
        self._initialize_subjects()
        self._initialize_classrooms()
        self._initialize_teachers()

    def _initialize_subjects(self):
        """Inicjalizuje wszystkie przedmioty"""
        # Podstawowe przedmioty z prawidłową liczbą godzin
        basic_subjects = [
            Subject(id=1, name="polski", hours_per_week=4),  # było 4
            Subject(id=2, name="matematyka", hours_per_week=3),  # było 4
            Subject(id=3, name="angielski", hours_per_week=3),
            Subject(id=4, name="fizyka", hours_per_week=1),  # było 2
            Subject(id=5, name="chemia", hours_per_week=1),  # było 2
            Subject(id=6, name="biologia", hours_per_week=1),  # było 2
            Subject(id=7, name="geografia", hours_per_week=1),  # było 2
            Subject(id=8, name="historia", hours_per_week=2),
            Subject(id=9, name="wos", hours_per_week=1),
            Subject(id=10, name="informatyka", hours_per_week=1),
            Subject(id=11, name="wf", hours_per_week=3)
        ]

        # Dodaj podstawowe przedmioty do słownika
        for subject in basic_subjects:
            self.subjects[subject.name] = subject

            # Dla przedmiotów rozszerzonych też należy zmniejszyć liczbę godzin
            # Obecnie jest +2 do podstawowej liczby, co daje za dużo
            extended = Subject(
                id=subject.id + 100,
                name=f"{subject.name}_rozszerzony",
                hours_per_week=subject.hours_per_week + 1,  # było +2
                requires_special_classroom=subject.requires_special_classroom,
                special_classroom_type=subject.special_classroom_type
            )
            self.subjects[extended.name] = extended

        logger.debug(f"Initialized subjects: {list(self.subjects.keys())}")

    def _initialize_classrooms(self):
        """Inicjalizuje sale lekcyjne"""
        classrooms = [
            Classroom(id=1, name="101", capacity=30),
            Classroom(id=2, name="102", capacity=30),
            Classroom(id=3, name="103", capacity=30),
            Classroom(id=4, name="104", capacity=30),
            # Sale specjalne
            Classroom(id=5, name="Sala komputerowa", capacity=25,
                      room_type="sala_komputerowa"),
            Classroom(id=6, name="Laboratorium fizyczne", capacity=20,
                      room_type="lab_fizyczne"),
            Classroom(id=7, name="Laboratorium chemiczne", capacity=20,
                      room_type="lab_chemiczne"),
            Classroom(id=8, name="Sala gimnastyczna", capacity=50,
                      room_type="sala_gimnastyczna"),
        ]

        for classroom in classrooms:
            self.classrooms[classroom.id] = classroom

        logger.debug(f"Initialized {len(self.classrooms)} classrooms")

    def _initialize_teachers(self):
        """Inicjalizuje nauczycieli"""
        teachers = [
            Teacher(id=1, name="Kowalski", subjects=["matematyka", "matematyka_rozszerzony"]),
            Teacher(id=2, name="Nowak", subjects=["fizyka", "fizyka_rozszerzony"]),
            Teacher(id=3, name="Wiśniewska", subjects=["chemia", "chemia_rozszerzony"]),
            Teacher(id=4, name="Dąbrowski", subjects=["biologia", "biologia_rozszerzony"]),
            Teacher(id=5, name="Lewandowski", subjects=["geografia", "geografia_rozszerzony"]),
            Teacher(id=6, name="Wójcik", subjects=["informatyka", "informatyka_rozszerzony"]),
            Teacher(id=7, name="Kamiński", subjects=["polski"]),
            Teacher(id=8, name="Kowalczyk", subjects=["historia", "historia_rozszerzony"]),
            Teacher(id=9, name="Zieliński", subjects=["wos", "wos_rozszerzony"]),
            Teacher(id=10, name="Szymański", subjects=["angielski", "angielski_rozszerzony"]),
            Teacher(id=11, name="Woźniak", subjects=["wf"])
        ]

        for teacher in teachers:
            self.teachers[teacher.id] = teacher

        logger.debug(f"Initialized {len(self.teachers)} teachers")

    def initialize_classes(self, config: Dict):
        """Inicjalizuje klasy na podstawie konfiguracji"""
        try:
            logger.debug(f"Rozpoczynam inicjalizację klas z konfiguracją: {config}")

            # Walidacja podstawowa
            if not isinstance(config, dict):
                raise ValueError(f"Nieprawidłowa konfiguracja: {config}")

            if 'class_counts' not in config:
                raise ValueError("Brak informacji o liczbie klas w konfiguracji")

            # Dodaj domyślnie jedną klasę pierwszą, jeśli nie została zdefiniowana
            try:
                if not config.get('class_counts', {}).get('first_year', 0):
                    logger.warning("Nie wybrano żadnej klasy pierwszej, dodaję domyślnie jedną")
                    if 'class_counts' not in config:
                        config['class_counts'] = {}
                    config['class_counts']['first_year'] = 1
            except Exception as e:
                logger.error(f"Błąd podczas sprawdzania liczby klas: {str(e)}")
                # Ustaw domyślną wartość, aby kontynuować
                config['class_counts'] = {'first_year': 1}

            year_keys = ['first_year', 'second_year', 'third_year', 'fourth_year']

            # Używamy już zainicjalizowanej listy profili
            available_profiles = self.profiles
            if not available_profiles:
                logger.error("Pusta lista profili w initialize_classes, to nie powinno się zdarzyć")
                return

            logger.debug(f"Dostępne profile: {[p.get('name', 'bez_nazwy') for p in available_profiles]}")

            # Tworzenie klas dla każdego rocznika
            for year_idx, year_key in enumerate(year_keys, 1):
                try:
                    class_count = config['class_counts'].get(year_key, 0)
                    logger.debug(f"Tworzę {class_count} klas dla rocznika {year_key}")

                    for class_idx in range(class_count):
                        try:
                            # Wybierz profil, obsługując przypadek pustej listy
                            profile_idx = class_idx % len(available_profiles) if available_profiles else 0
                            profile = available_profiles[profile_idx]

                            logger.debug(
                                f"Używam profilu: {profile['name']} dla klasy {year_idx}{string.ascii_uppercase[class_idx]}")

                            # Przygotuj listę przedmiotów dla klasy
                            class_subjects = []

                            # Dodaj podstawowe przedmioty
                            try:
                                for subject in self.subjects.values():
                                    if not subject.name.endswith('_rozszerzony'):
                                        class_subjects.append(subject)
                            except Exception as e:
                                logger.error(f"Błąd podczas dodawania podstawowych przedmiotów: {str(e)}")

                            # Dodaj przedmioty rozszerzone
                            try:
                                for subject_name in profile.get('extended_subjects', []):
                                    extended_name = f"{subject_name}_rozszerzony"
                                    if extended_name in self.subjects:
                                        class_subjects.append(self.subjects[extended_name])
                                    else:
                                        logger.warning(f"Extended subject not found: {extended_name}")
                            except Exception as e:
                                logger.error(f"Błąd podczas dodawania przedmiotów rozszerzonych: {str(e)}")

                            # Tworzenie obiektu klasy z obsługą wyjątków
                            try:
                                # Bezpieczny dostęp do ASCII_UPPERCASE z kontrolą zakresu
                                letter = string.ascii_uppercase[min(class_idx, len(string.ascii_uppercase) - 1)]

                                class_group = ClassGroup(
                                    year=year_idx,
                                    letter=letter,
                                    profile=profile.get('name', 'domyślny'),
                                    subjects=class_subjects
                                )
                                self.class_groups.append(class_group)
                                logger.debug(
                                    f"Created class {class_group.name} with profile {profile.get('name', 'domyślny')}")
                            except Exception as e:
                                logger.error(
                                    f"Błąd podczas tworzenia klasy {year_idx}{string.ascii_uppercase[min(class_idx, 25)]}: {str(e)}")

                        except Exception as e:
                            logger.error(f"Błąd podczas inicjalizacji klasy {year_idx}-{class_idx}: {str(e)}")

                except Exception as e:
                    logger.error(f"Błąd podczas przetwarzania rocznika {year_key}: {str(e)}")

        except Exception as e:
            logger.error(f"Krytyczny błąd podczas inicjalizacji klas: {str(e)}")
            # W przypadku krytycznego błędu spróbuj utworzyć przynajmniej jedną klasę
            try:
                # Dodaj domyślną klasę 1A z podstawowymi przedmiotami
                default_subjects = [s for s in self.subjects.values() if not s.name.endswith('_rozszerzony')]
                default_class = ClassGroup(
                    year=1,
                    letter='A',
                    profile='awaryjny',
                    subjects=default_subjects
                )
                self.class_groups.append(default_class)
                logger.warning("Utworzono awaryjną klasę 1A z podstawowymi przedmiotami")
            except Exception as recovery_error:
                logger.critical(f"Nie udało się utworzyć awaryjnej klasy: {str(recovery_error)}")

    def get_subject(self, name: str) -> Subject:
        """Zwraca przedmiot o danej nazwie"""
        subject = self.subjects.get(name)
        if subject is None:
            logger.warning(f"Nie znaleziono przedmiotu: {name}")
        return subject

    def get_teacher_lessons(self, teacher: Teacher) -> List[Lesson]:
        """Zwraca wszystkie lekcje danego nauczyciela"""
        teacher_lessons = []
        for lesson in self.lessons:
            if lesson.teacher.id == teacher.id:
                teacher_lessons.append(lesson)
        return teacher_lessons

    def get_classroom_lessons(self, classroom: Classroom) -> List[Lesson]:
        """Zwraca wszystkie lekcje w danej sali"""
        room_lessons = []
        for lesson in self.lessons:
            if lesson.classroom.id == classroom.id:
                room_lessons.append(lesson)
        return room_lessons

    def get_teacher(self, id: int) -> Teacher:
        """Zwraca nauczyciela o danym id"""
        return self.teachers.get(id)

    def get_classroom(self, id: int) -> Classroom:
        """Zwraca salę o danym id"""
        return self.classrooms.get(id)

    def get_basic_subjects(self) -> List[Subject]:
        """Zwraca listę podstawowych (nierozszerzonych) przedmiotów"""
        return [
            subject for subject in self.subjects.values()
            if not subject.name.endswith('_rozszerzony')
        ]

    def get_extended_subjects(self, profile_name: str) -> List[Subject]:
        """Zwraca listę przedmiotów rozszerzonych dla danego profilu"""
        # Find the profile configuration
        profile = next(
            (p for p in self.profiles if p['name'] == profile_name),
            None
        )

        if not profile:
            logger.warning(f"Profile {profile_name} not found")
            return []

        # Uzyskaj rozszerzone tematy dla tego profilu
        extended_subjects = []
        for subject_name in profile['extended_subjects']:
            extended_name = f"{subject_name}_rozszerzony"
            if extended_name in self.subjects:
                extended_subjects.append(self.subjects[extended_name])
            else:
                logger.warning(f"Extended subject not found: {extended_name}")

        return extended_subjects
