# tests/test_school.py
import pytest


def test_school_initialization(simple_school):
    """Test poprawnej inicjalizacji szkoły"""
    assert simple_school is not None
    assert len(simple_school.class_groups) > 0
    assert len(simple_school.teachers) > 0
    assert len(simple_school.classrooms) > 0
    assert len(simple_school.subjects) > 0


def test_school_get_basic_subjects(simple_school):
    """Test pobierania podstawowych przedmiotów"""
    basic_subjects = simple_school.get_basic_subjects()
    assert len(basic_subjects) > 0

    # Sprawdź, czy nie ma przedmiotów rozszerzonych
    for subject in basic_subjects:
        assert not subject.name.endswith('_rozszerzony')


def test_school_get_extended_subjects(simple_school):
    """Test pobierania przedmiotów rozszerzonych"""
    extended_subjects = simple_school.get_extended_subjects('test_profile')
    assert len(extended_subjects) > 0

    # Sprawdź, czy wszystkie są rozszerzone
    subject_names = [subject.name for subject in extended_subjects]
    assert 'matematyka_rozszerzony' in subject_names
    assert 'angielski_rozszerzony' in subject_names

    # Sprawdź czy wszystkie przedmioty są rozszerzone
    for subject in extended_subjects:
        assert subject.name.endswith('_rozszerzony')