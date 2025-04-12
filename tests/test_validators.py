# tests/test_validators.py
import pytest
from src.utils.validators import ScheduleValidator, ValidationResult


def test_schedule_validator():
    """Test walidatora konfiguracji szkoły"""
    validator = ScheduleValidator()

    # Test poprawnej konfiguracji
    valid_config = {
        'class_counts': {
            'first_year': 2,
            'second_year': 2,
            'third_year': 2,
            'fourth_year': 2
        },
        'profiles': [
            {
                'name': 'mat-fiz',
                'extended_subjects': ['matematyka', 'fizyka']
            },
            {
                'name': 'biol-chem',
                'extended_subjects': ['biologia', 'chemia']
            }
        ]
    }

    result = validator.validate_school_config(valid_config)
    assert result.is_valid
    assert not result.errors

    # Test niepoprawnej konfiguracji
    invalid_config = {
        'class_counts': {
            'first_year': -1,  # niepoprawna wartość
            'second_year': 2,
            'third_year': 2,
            'fourth_year': 2
        },
        'profiles': []  # brak profili
    }

    result = validator.validate_school_config(invalid_config)
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any('first_year' in error for error in result.errors)