# tests/conftest.py
import sys
import pytest
from pathlib import Path

# Dodanie głównego katalogu projektu do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.subject import Subject
from src.models.teacher import Teacher
from src.models.classroom import Classroom
from src.models.school import School, ClassGroup
from src.models.lesson import Lesson
from src.models.schedule import Schedule


@pytest.fixture
def basic_subjects():
    """Fixture zwracający podstawowy zestaw przedmiotów"""
    return {
        "math": Subject(id=1, name="matematyka", hours_per_week=4),
        "polish": Subject(id=2, name="polski", hours_per_week=4),
        "english": Subject(id=3, name="angielski", hours_per_week=3),
        "pe": Subject(id=11, name="wf", hours_per_week=3,
                     requires_special_classroom=True,
                     special_classroom_type="sala_gimnastyczna")
    }


@pytest.fixture
def basic_teachers():
    """Fixture zwracający podstawowy zestaw nauczycieli"""
    return {
        "math_teacher": Teacher(id=1, name="Kowalski", subjects=["matematyka", "matematyka_rozszerzony"]),
        "polish_teacher": Teacher(id=7, name="Kamiński", subjects=["polski"]),
        "english_teacher": Teacher(id=10, name="Szymański", subjects=["angielski", "angielski_rozszerzony"]),
        "pe_teacher": Teacher(id=11, name="Woźniak", subjects=["wf"])
    }


@pytest.fixture
def basic_classrooms():
    """Fixture zwracający podstawowy zestaw sal"""
    return {
        "regular": Classroom(id=1, name="101", capacity=30),
        "computer_lab": Classroom(id=5, name="Sala komputerowa", capacity=25, room_type="sala_komputerowa"),
        "gym": Classroom(id=8, name="Sala gimnastyczna", capacity=50, room_type="sala_gimnastyczna")
    }


@pytest.fixture
def simple_school():
    """Fixture tworzący prostą szkołę do testów"""
    config = {
        'class_counts': {
            'first_year': 1,
            'second_year': 1,
            'third_year': 0,
            'fourth_year': 0
        },
        'profiles': [{
            'name': 'test_profile',
            'extended_subjects': ['matematyka', 'angielski']
        }]
    }
    return School(config)


@pytest.fixture
def simple_schedule(simple_school):
    """Fixture tworzący prosty harmonogram do testów"""
    return Schedule(school=simple_school)