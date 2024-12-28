# models/lesson.py
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)  # Dodaj frozen=True aby klasa była immutable
class Lesson:
    """Reprezentuje pojedynczą lekcję w planie"""
    subject: str
    teacher_id: str
    room_id: str
    day: int  # 0-4 (pon-pt)
    hour: int  # 1-9
    group: Optional[int] = None  # None dla całej klasy, 1 lub 2 dla grup
    class_name: str = ''  # np. "1A", "2B" itp.

    def __hash__(self):
        """Implementacja hash dla możliwości użycia w set()"""
        return hash((self.subject, self.teacher_id, self.room_id,
                     self.day, self.hour, self.group, self.class_name))

    def is_split_subject(self) -> bool:
        """Sprawdza czy przedmiot jest dzielony na grupy"""
        return self.subject in {'Angielski', 'Informatyka', 'WF'}

    def conflicts_with(self, other: 'Lesson') -> bool:
        """Sprawdza czy lekcja koliduje z inną lekcją"""
        # Te same godziny
        if self.day != other.day or self.hour != other.hour:
            return False

        # Ten sam nauczyciel
        if self.teacher_id == other.teacher_id:
            return True

        # Ta sama sala (chyba że to sala WF)
        if (self.room_id == other.room_id and
                not (self.subject == 'WF' and self.room_id in {'DUZA_HALA', 'MALA_SALA'})):
            return True

        # Ta sama klasa i grupa (lub cała klasa)
        if self.class_name == other.class_name:
            if self.group is None or other.group is None:
                return True
            if self.group == other.group:
                return True

        return False

    def validate_room(self) -> bool:
        """Sprawdza czy sala jest odpowiednia dla przedmiotu"""
        if self.subject == 'Informatyka':
            return self.room_id in {'14', '24'}
        elif self.subject == 'WF':
            return self.room_id in {'SILOWNIA', 'MALA_SALA', 'DUZA_HALA'}
        else:
            # Dla pozostałych przedmiotów - zwykłe sale (1-28, bez 14 i 24)
            try:
                room_num = int(self.room_id)
                return (1 <= room_num <= 28 and
                        room_num != 14 and
                        room_num != 24)
            except ValueError:
                return False

    def to_dict(self) -> dict:
        """Konwertuje lekcję do słownika (np. dla szablonu HTML)"""
        return {
            'subject': self.subject,
            'teacher_id': self.teacher_id,
            'room_id': self.room_id,
            'day': self.day,
            'hour': self.hour,
            'group': self.group,
            'class_name': self.class_name,
            'is_split': self.is_split_subject()
        }
