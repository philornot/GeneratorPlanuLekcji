# tests/test_schedule.py
import pytest

from src.models.lesson import Lesson


def test_schedule_add_lesson(simple_schedule, basic_subjects, basic_teachers, basic_classrooms):
    """Test dodawania lekcji do planu"""
    lesson1 = Lesson(
        subject=basic_subjects["math"],
        teacher=basic_teachers["math_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=0
    )

    # Dodanie pierwszej lekcji powinno się udać
    assert simple_schedule.add_lesson(lesson1)
    assert len(simple_schedule.lessons) == 1
    assert "1A" in simple_schedule.class_groups

    # Konflikt - ta sama sala, nauczyciel i klasa w tym samym czasie
    lesson2 = Lesson(
        subject=basic_subjects["polish"],
        teacher=basic_teachers["math_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=0
    )
    assert not simple_schedule.add_lesson(lesson2)
    assert len(simple_schedule.lessons) == 1

    # Powinna się udać - inny czas
    lesson3 = Lesson(
        subject=basic_subjects["math"],
        teacher=basic_teachers["math_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=1
    )
    assert simple_schedule.add_lesson(lesson3)
    assert len(simple_schedule.lessons) == 2


def test_schedule_get_class_lessons(simple_schedule, basic_subjects, basic_teachers, basic_classrooms):
    """Test pobierania lekcji dla danej klasy"""
    lesson1 = Lesson(
        subject=basic_subjects["math"],
        teacher=basic_teachers["math_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=0
    )

    lesson2 = Lesson(
        subject=basic_subjects["polish"],
        teacher=basic_teachers["polish_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=1
    )

    lesson3 = Lesson(
        subject=basic_subjects["english"],
        teacher=basic_teachers["english_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="2A",
        day=0,
        hour=0
    )

    simple_schedule.add_lesson(lesson1)
    simple_schedule.add_lesson(lesson2)
    simple_schedule.add_lesson(lesson3)

    class_lessons = simple_schedule.get_class_lessons("1A")
    assert len(class_lessons) == 2
    assert lesson1 in class_lessons
    assert lesson2 in class_lessons
    assert lesson3 not in class_lessons


def test_schedule_get_teacher_hours(simple_schedule, basic_subjects, basic_teachers, basic_classrooms):
    """Test liczenia godzin nauczyciela"""
    math_teacher = basic_teachers["math_teacher"]

    # Dodaj kilka lekcji dla nauczyciela matematyki
    simple_schedule.add_lesson(Lesson(
        subject=basic_subjects["math"],
        teacher=math_teacher,
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,  # Poniedziałek
        hour=0
    ))

    simple_schedule.add_lesson(Lesson(
        subject=basic_subjects["math"],
        teacher=math_teacher,
        classroom=basic_classrooms["regular"],
        class_group="2A",
        day=0,  # Poniedziałek
        hour=1
    ))

    simple_schedule.add_lesson(Lesson(
        subject=basic_subjects["math"],
        teacher=math_teacher,
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=1,  # Wtorek
        hour=0
    ))

    hours = simple_schedule.get_teacher_hours(math_teacher)

    assert hours['weekly'] == 3
    assert hours['daily'][0] == 2  # 2 godziny w poniedziałek
    assert hours['daily'][1] == 1  # 1 godzina we wtorek