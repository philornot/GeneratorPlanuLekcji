# models/lesson.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    """Reprezentuje pojedynczą lekcję w planie"""
    subject: str
    teacher_id: str
    room_id: str
    day: int  # 0-4 (pon-pt)
    hour: int  # 1-9
    class_name: str  # np. "1A", "2B" itp.

    def __hash__(self):
        """Implementacja hash dla możliwości użycia w set()"""
        return hash((self.subject, self.teacher_id, self.room_id,
                     self.day, self.hour, self.class_name))

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
                not (self.subject == 'Wychowanie fizyczne' and
                     self.room_id in {'DUZA_HALA', 'MALA_SALA'})):
            return True

        # Ta sama klasa
        if self.class_name == other.class_name:
            return True

        return False

    def validate_room(self) -> bool:
        """Sprawdza, czy sala jest odpowiednia dla przedmiotu"""
        if self.subject == 'Informatyka':
            return self.room_id in {'14', '24'}
        elif self.subject == 'Wychowanie fizyczne':
            return self.room_id in {'SILOWNIA', 'MALA_SALA', 'DUZA_HALA'}
        else:
            # Dla pozostałych przedmiotów — zwykłe sale (1-28, bez 14 i 24)
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
            'class_name': self.class_name
        }
