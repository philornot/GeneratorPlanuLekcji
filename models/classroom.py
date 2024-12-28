# models/classroom.py
from dataclasses import dataclass, field
from typing import List, Dict, Set

from .lesson import Lesson


@dataclass
class Classroom:
    """Reprezentuje salę lekcyjną"""
    room_id: str
    capacity: int  # Liczba grup, które mogą mieć jednocześnie zajęcia
    allowed_subjects: Set[str]
    floor: int
    schedule: Dict[int, Dict[int, List[Lesson]]] = field(default_factory=lambda: {
        day: {hour: [] for hour in range(1, 10)}
        for day in range(5)
    })

    @classmethod
    def create_regular_room(cls, number: int) -> 'Classroom':
        """Tworzy zwykłą salę lekcyjną"""
        return cls(
            room_id=str(number),
            capacity=2,  # Mieści całą klasę (dwie grupy)
            allowed_subjects={subj for subj in {'Polski', 'Matematyka', 'Niemiecki',
                                                'Francuski', 'Hiszpański', 'Fizyka', 'Biologia', 'Chemia',
                                                'Historia', 'HiT', 'Przedsiębiorczość', 'Religia', 'Angielski'}},
            floor=(number - 1) // 10  # Zakładamy, że numery sal odpowiadają piętrom
        )

    @classmethod
    def create_computer_room(cls, number: int) -> 'Classroom':
        """Tworzy salę komputerową"""
        return cls(
            room_id=str(number),
            capacity=1,  # Mieści jedną grupę
            allowed_subjects={'Informatyka'},
            floor=(number - 1) // 10
        )

    @classmethod
    def create_gym_room(cls, room_type: str) -> 'Classroom':
        """Tworzy salę gimnastyczną"""
        if room_type == 'SILOWNIA':
            capacity = 1
        elif room_type == 'MALA_SALA':
            capacity = 3
        elif room_type == 'DUZA_HALA':
            capacity = 6
        else:
            raise ValueError(f"Nieznany typ sali gimnastycznej: {room_type}")

        return cls(
            room_id=room_type,
            capacity=capacity,
            allowed_subjects={'WF'},
            floor=0  # Zakładamy, że wszystkie sale gimnastyczne są na parterze
        )

    def can_accommodate(self, lesson: Lesson) -> bool:
        """Sprawdza czy sala może pomieścić daną lekcję"""
        # Sprawdź czy przedmiot jest dozwolony w tej sali
        if lesson.subject not in self.allowed_subjects:
            return False

        # Pobierz aktualnie zaplanowane lekcje na daną godzinę
        current_lessons = self.schedule[lesson.day][lesson.hour]

        # Sprawdź czy jest miejsce w sali
        if len(current_lessons) >= self.capacity:
            return False

        # Dla WF sprawdź specjalne reguły
        if lesson.subject == 'WF' and self.room_id in {'MALA_SALA', 'DUZA_HALA'}:
            # Dozwolone więcej grup jednocześnie
            current_groups = sum(1 for l in current_lessons if l.group is not None)
            if current_groups >= self.capacity:
                return False

        return True

    def add_lesson(self, lesson: Lesson) -> bool:
        """Dodaje lekcję do harmonogramu sali"""
        if not self.can_accommodate(lesson):
            return False

        self.schedule[lesson.day][lesson.hour].append(lesson)
        return True

    def remove_lesson(self, lesson: Lesson) -> bool:
        """Usuwa lekcję z harmonogramu sali"""
        try:
            self.schedule[lesson.day][lesson.hour].remove(lesson)
            return True
        except ValueError:
            return False

    def get_occupancy(self, day: int) -> float:
        """Zwraca procentowe wykorzystanie sali danego dnia"""
        occupied_slots = sum(
            1 for hour in range(1, 10)
            if len(self.schedule[day][hour]) > 0
        )
        return (occupied_slots / 9) * 100

    def is_available(self, day: int, hour: int) -> bool:
        """Sprawdza czy sala jest dostępna w danym terminie"""
        return len(self.schedule[day][hour]) < self.capacity

    def get_room_type(self) -> str:
        """Zwraca typ sali"""
        if self.room_id in {'SILOWNIA', 'MALA_SALA', 'DUZA_HALA'}:
            return 'Sala gimnastyczna'
        elif self.room_id in {'14', '24'}:
            return 'Sala komputerowa'
        else:
            return 'Sala zwykła'

    def to_dict(self) -> dict:
        """Konwertuje salę do słownika (np. dla szablonu HTML)"""
        return {
            'room_id': self.room_id,
            'capacity': self.capacity,
            'floor': self.floor,
            'type': self.get_room_type(),
            'allowed_subjects': list(self.allowed_subjects),
            'schedule': {
                day: {
                    hour: [lesson.to_dict() for lesson in lessons]
                    for hour, lessons in hours.items()
                }
                for day, hours in self.schedule.items()
            }
        }
