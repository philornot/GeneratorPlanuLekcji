# tests/test_utils.py
import pytest
import tempfile
import json
from pathlib import Path
from src.repository.schedule_repository import ScheduleRepository
from src.models.schedule import Schedule


@pytest.fixture
def temp_data_dir():
    """Tworzy tymczasowy katalog na dane testowe"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_schedule_repository(temp_data_dir, simple_schedule, basic_subjects, basic_teachers, basic_classrooms):
    """Test zapisywania i wczytywania planu lekcji"""
    repo = ScheduleRepository(data_dir=temp_data_dir)

    # Dodaj kilka lekcji do planu
    from src.models.lesson import Lesson
    lesson = Lesson(
        subject=basic_subjects["math"],
        teacher=basic_teachers["math_teacher"],
        classroom=basic_classrooms["regular"],
        class_group="1A",
        day=0,
        hour=0
    )
    simple_schedule.add_lesson(lesson)

    # Zapisz plan
    repo.save_schedule(simple_schedule, "test_schedule")

    # Sprawdź, czy plik został utworzony
    file_path = Path(temp_data_dir) / "test_schedule.json"
    assert file_path.exists()

    # Wczytaj plan i sprawdź dane
    loaded_data = repo.load_schedule("test_schedule")
    assert loaded_data is not None
    assert loaded_data['class_groups'] == ['1A']
    assert len(loaded_data['lessons']) == 1
    assert loaded_data['lessons'][0]['class_group'] == '1A'

    # Sprawdź listę planów
    schedules = repo.list_schedules()
    assert "test_schedule" in schedules