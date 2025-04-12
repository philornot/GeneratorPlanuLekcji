# tests/test_models.py
import pytest
from src.models.lesson import Lesson
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.models.classroom import Classroom


def test_subject_creation():
    """Test tworzenia obiektu przedmiotu"""
    subject = Subject(id=1, name="matematyka", hours_per_week=4)
    assert subject.id == 1
    assert subject.name == "matematyka"
    assert subject.hours_per_week == 4
    assert not subject.requires_special_classroom
    assert subject.special_classroom_type is None


def test_subject_equality():
    """Test porównywania przedmiotów"""
    subject1 = Subject(id=1, name="matematyka", hours_per_week=4)
    subject2 = Subject(id=1, name="matematyka zmieniona", hours_per_week=3)
    subject3 = Subject(id=2, name="matematyka", hours_per_week=4)

    assert subject1 == subject1  # identyczny obiekt
    assert subject1 == subject2  # ten sam id, różne atrybuty
    assert subject1 != subject3  # różne id
    assert subject1 != "matematyka"  # porównanie z innym typem


def test_teacher_can_teach():
    """Test sprawdzania czy nauczyciel może uczyć danego przedmiotu"""
    teacher = Teacher(id=1, name="Kowalski", subjects=["matematyka", "fizyka"])

    assert teacher.can_teach("matematyka")
    assert teacher.can_teach("fizyka")
    assert not teacher.can_teach("biologia")
    assert not teacher.can_teach("")


def test_classroom_suitability():
    """Test sprawdzania czy sala jest odpowiednia dla przedmiotu"""
    regular_room = Classroom(id=1, name="101", capacity=30)
    science_lab = Classroom(id=2, name="Lab", capacity=25, room_type="lab_fizyczne")

    regular_subject = Subject(id=1, name="matematyka", hours_per_week=4)
    special_subject = Subject(id=2, name="fizyka", hours_per_week=3,
                              requires_special_classroom=True,
                              special_classroom_type="lab_fizyczne")

    assert regular_room.is_suitable_for_subject(regular_subject)
    assert not regular_room.is_suitable_for_subject(special_subject)
    assert science_lab.is_suitable_for_subject(regular_subject)
    assert science_lab.is_suitable_for_subject(special_subject)


def test_lesson_conflicts():
    """Test sprawdzania konfliktów między lekcjami"""
    math = Subject(id=1, name="matematyka", hours_per_week=4)
    physics = Subject(id=2, name="fizyka", hours_per_week=3)

    teacher1 = Teacher(id=1, name="Kowalski", subjects=["matematyka"])
    teacher2 = Teacher(id=2, name="Nowak", subjects=["fizyka"])

    room1 = Classroom(id=1, name="101", capacity=30)
    room2 = Classroom(id=2, name="102", capacity=30)

    # Lekcje w tym samym czasie
    lesson1 = Lesson(subject=math, teacher=teacher1, classroom=room1, class_group="1A", day=0, hour=1)

    # Ten sam nauczyciel
    lesson2 = Lesson(subject=math, teacher=teacher1, classroom=room2, class_group="1B", day=0, hour=1)
    assert lesson1.conflicts_with(lesson2)

    # Ta sama sala
    lesson3 = Lesson(subject=physics, teacher=teacher2, classroom=room1, class_group="1B", day=0, hour=1)
    assert lesson1.conflicts_with(lesson3)

    # Ta sama klasa
    lesson4 = Lesson(subject=physics, teacher=teacher2, classroom=room2, class_group="1A", day=0, hour=1)
    assert lesson1.conflicts_with(lesson4)

    # Brak konfliktu - inny czas
    lesson5 = Lesson(subject=math, teacher=teacher1, classroom=room1, class_group="1B", day=0, hour=2)
    assert not lesson1.conflicts_with(lesson5)

    # Brak konfliktu - inny dzień
    lesson6 = Lesson(subject=math, teacher=teacher1, classroom=room1, class_group="1B", day=1, hour=1)
    assert not lesson1.conflicts_with(lesson6)