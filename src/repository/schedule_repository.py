# src/repository/schedule_repository.py

import json
from pathlib import Path
from typing import Optional, Dict, List

from src.utils.logger import GPLLogger


class ScheduleRepository:
    """Warstwa dostępu do danych dla planów lekcji"""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.logger = GPLLogger(__name__)

    def save_schedule(self, schedule: 'Schedule', name: str):
        """Zapisuje plan lekcji"""
        try:
            file_path = self.data_dir / f"{name}.json"
            schedule_data = schedule.to_dict()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(schedule_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Schedule saved successfully: {name}")

        except Exception as e:
            self.logger.error(f"Error saving schedule {name}: {str(e)}")
            raise

    def load_schedule(self, name: str) -> Optional[Dict]:
        """Wczytuje plan lekcji"""
        try:
            file_path = self.data_dir / f"{name}.json"

            if not file_path.exists():
                self.logger.warning(f"Schedule not found: {name}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)

            self.logger.info(f"Schedule loaded successfully: {name}")
            return schedule_data

        except Exception as e:
            self.logger.error(f"Error loading schedule {name}: {str(e)}")
            return None

    def list_schedules(self) -> List[str]:
        """Zwraca listę dostępnych planów"""
        try:
            return [f.stem for f in self.data_dir.glob("*.json")]
        except Exception as e:
            self.logger.error(f"Error listing schedules: {str(e)}")
            return []