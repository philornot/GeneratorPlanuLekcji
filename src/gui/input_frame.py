# src/gui/input_frame.py

import customtkinter as ctk
from typing import Dict, List


class SchoolInputFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.class_counts = {
            'first_year': 0,
            'second_year': 0,
            'third_year': 0,
            'fourth_year': 0
        }

        self.create_widgets()

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
        for year, name in enumerate(['Pierwsze', 'Drugie', 'Trzecie', 'Czwarte'], 1):
            frame = ctk.CTkFrame(classes_frame)
            frame.pack(fill='x', pady=2)

            label = ctk.CTkLabel(frame, text=f"{name} klasy:")
            label.pack(side='left', padx=5)

            spinbox = ctk.CTkOptionMenu(
                frame,
                values=[str(i) for i in range(6)],
                command=lambda v, y=year: self.update_class_count(y - 1, int(v))
            )
            spinbox.pack(side='right', padx=5)
            spinbox.set("0")

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
        years = ['first_year', 'second_year', 'third_year', 'fourth_year']
        self.class_counts[years[year]] = count

    def add_profile(self):
        profile_frame = ctk.CTkFrame(self.profiles_frame)
        profile_frame.pack(fill='x', pady=2)

        name_entry = ctk.CTkEntry(profile_frame, placeholder_text="Nazwa profilu")
        name_entry.pack(side='left', padx=5)

        # Rozszerzone przedmioty
        subjects = ["matematyka", "fizyka", "chemia", "biologia", "geografia", "informatyka"]
        extended_subjects = ctk.CTkOptionMenu(
            profile_frame,
            values=subjects
        )
        extended_subjects.pack(side='left', padx=5)

        remove_btn = ctk.CTkButton(
            profile_frame,
            text="Usuń",
            command=lambda: profile_frame.destroy()
        )
        remove_btn.pack(side='right', padx=5)

        self.profiles.append({
            'frame': profile_frame,
            'name': name_entry,
            'subjects': extended_subjects
        })

    def get_configuration(self) -> Dict:
        """Zwraca kompletną konfigurację szkoły"""
        return {
            'class_counts': self.class_counts,
            'profiles': [
                {
                    'name': p['name'].get(),
                    'extended_subjects': p['subjects'].get()
                }
                for p in self.profiles
                if p['frame'].winfo_exists()  # sprawdza czy profil nie został usunięty
            ]
        }