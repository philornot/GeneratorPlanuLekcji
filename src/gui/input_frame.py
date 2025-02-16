# src/gui/input_frame.py
import json
import logging
from pathlib import Path
from typing import Dict

import customtkinter as ctk

logger = logging.getLogger(__name__)


class SchoolInputFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Inicjalizacja podstawowych zmiennych
        self.class_counts = {
            'first_year': 0,
            'second_year': 0,
            'third_year': 0,
            'fourth_year': 0
        }
        self.profiles = []  # lista profili

        # Wczytaj zapisaną konfigurację lub użyj domyślnej
        self.load_configuration()

        # Tworzenie widgetów powinno być na końcu
        self.create_widgets()

    def load_configuration(self):
        try:
            config_path = Path('data/school_config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.class_counts = config.get('class_counts', {
                        'first_year': 0,
                        'second_year': 0,
                        'third_year': 0,
                        'fourth_year': 0
                    })
                    self.saved_profiles = config.get('profiles', [])
                    logger.debug(f"Loaded configuration: {config}")
            else:
                self.saved_profiles = []
        except Exception as e:
            logger.error(f"Error loading school configuration: {e}")
            self.class_counts = {
                'first_year': 0,
                'second_year': 0,
                'third_year': 0,
                'fourth_year': 0
            }
            self.saved_profiles = []

    def create_widgets(self):
        # Nagłówek
        header = ctk.CTkLabel(
            self,
            text="Struktura szkoły",
            font=("Helvetica", 16, "bold")
        )
        header.pack(pady=10)

        # Frame na liczby klas
        classes_frame = ctk.CTkFrame(self)
        classes_frame.pack(fill='x', padx=20, pady=5)

        # Spinboxy dla każdego rocznika
        self.spinboxes = {}  # dodajemy słownik na spinboxy
        for year, name in enumerate(['Pierwsze', 'Drugie', 'Trzecie', 'Czwarte'], 1):
            frame = ctk.CTkFrame(classes_frame)
            frame.pack(fill='x', pady=2)

            label = ctk.CTkLabel(frame, text=f"{name} klasy:")
            label.pack(side='left', padx=5)

            year_key = ['first_year', 'second_year', 'third_year', 'fourth_year'][year - 1]
            spinbox = ctk.CTkOptionMenu(
                frame,
                values=[str(i) for i in range(1, 6)],
                command=lambda v, y=year: self.update_class_count(y - 1, int(v))
            )
            spinbox.pack(side='right', padx=5)
            # Ustaw wartość z zapisanej konfiguracji
            spinbox.set(str(self.class_counts[year_key]))
            self.spinboxes[year_key] = spinbox

        # Profile klas
        self.profiles_frame = ctk.CTkFrame(self)
        self.profiles_frame.pack(fill='x', padx=20, pady=5)

        self.add_profile_button = ctk.CTkButton(
            self.profiles_frame,
            text="Dodaj profil",
            command=self.add_profile
        )
        self.add_profile_button.pack(pady=5)

        self.profiles = []  # lista profili

    def update_class_count(self, year: int, count: int):
        """Aktualizuje i zapisuje liczbę klas"""
        years = ['first_year', 'second_year', 'third_year', 'fourth_year']
        self.class_counts[years[year]] = count

        # Zapisz konfigurację
        self.save_configuration()

    def add_profile(self):
        profile_frame = ctk.CTkFrame(self.profiles_frame)
        profile_frame.pack(fill='x', pady=2)

        name_entry = ctk.CTkEntry(profile_frame, placeholder_text="Nazwa profilu")
        name_entry.pack(side='left', padx=5)

        # Lista wszystkich możliwych przedmiotów rozszerzonych
        available_subjects = [
            "matematyka", "fizyka", "chemia", "biologia",
            "geografia", "informatyka", "polski", "historia",
            "wos", "angielski"
        ]

        # Checkboxy dla przedmiotów rozszerzonych
        subjects_frame = ctk.CTkFrame(profile_frame)
        subjects_frame.pack(side='left', padx=5)

        subject_vars = {subject: ctk.BooleanVar() for subject in available_subjects}
        for subject in available_subjects:
            checkbox = ctk.CTkCheckBox(
                subjects_frame,
                text=subject,
                variable=subject_vars[subject]
            )
            checkbox.pack(anchor='w')

        remove_btn = ctk.CTkButton(
            profile_frame,
            text="Usuń",
            command=lambda: profile_frame.destroy()
        )
        remove_btn.pack(side='right', padx=5)

        self.profiles.append({
            'frame': profile_frame,
            'name': name_entry,
            'subjects': subject_vars  # teraz przechowujemy zmienne dla checkboxów
        })

        # Zapisywanie po dodaniu profilu
        self.save_configuration()

    def get_configuration(self) -> Dict:
        """Zwraca kompletną konfigurację szkoły"""
        return {
            'class_counts': self.class_counts,
            'profiles': [
                {
                    'name': p['name'].get(),
                    'extended_subjects': [
                        subject for subject, var in p['subjects'].items()
                        if var.get()  # tylko wybrane przedmioty
                    ]
                }
                for p in self.profiles
                if p['frame'].winfo_exists()  # sprawdza czy profil nie został usunięty
            ]
        }

    def save_configuration(self):
        """Zapisuje aktualną konfigurację do pliku"""
        config = {
            'class_counts': self.class_counts,
            'profiles': [
                {
                    'name': p['name'].get(),
                    'extended_subjects': [
                        subject for subject, var in p['subjects'].items()
                        if var.get()
                    ]
                }
                for p in self.profiles
                if p['frame'].winfo_exists()
            ]
        }

        try:
            config_path = Path('data/school_config.json')
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug("Saved school configuration")
        except Exception as e:
            logger.error(f"Error saving school configuration: {e}")
