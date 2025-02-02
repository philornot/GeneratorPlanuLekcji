# src/models/lesson.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Lesson:
    subject: 'Subject'
    teacher: 'Teacher'
    classroom: 'Classroom'
    class_group: str  # nazwa klasy np. "1A"
    day: int  # 0-4 (pon-pt)
    hour: int  # numer lekcji (0-7)

    def conflicts_with(self, other: 'Lesson') -> bool:
        """Sprawdza czy lekcja koliduje z inną"""
        if self.day != other.day or self.hour != other.hour:
            return False

        # Ten sam nauczyciel nie może prowadzić dwóch lekcji jednocześnie
        if self.teacher == other.teacher:
            return True

        # Ta sama klasa nie może mieć dwóch lekcji jednocześnie
        if self.class_group == other.class_group:
            return True

        # Ta sama sala nie może być używana przez dwie lekcje jednocześnie
        if self.classroom == other.classroom:
            return True

        return False