# src/gui/app.py
import threading
from tkinter import messagebox

import customtkinter as ctk
import sv_ttk
from typing import Callable, List, Dict
import json
from pathlib import Path
import logging

from src.algorithms.genetic import ScheduleGenerator
from src.models.schedule import Schedule

logger = logging.getLogger(__name__)


class SchedulerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja okna
        self.title("School Scheduler - Konfiguracja")
        self.geometry("600x400")
        sv_ttk.set_theme("light")

        # Ścieżka do pliku z konfiguracją
        self.config_path = Path('data/config.json')

        # Domyślne wartości
        self.default_values = {
            'iterations': 1000,
            'population_size': 100,
            'mutation_rate': 0.1,
            'crossover_rate': 0.8
        }

        # Wczytaj zapisane wartości lub użyj domyślnych
        self.values = self.load_config()

        self.create_widgets()

    def create_parameter_slider(self, parent, label_text: str, min_val: float,
                                max_val: float, default_val: float, step: float = 1) -> ctk.CTkSlider:
        """Tworzy slider z etykietą i polem wartości"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', padx=20, pady=5)

        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side='left')

        value_label = ctk.CTkLabel(frame, text=str(default_val))
        value_label.pack(side='right', padx=10)

        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int((max_val - min_val) / step),
            command=lambda val: value_label.configure(text=f"{val:.2f}"),
        )
        slider.pack(fill='x', padx=10)
        slider.set(default_val)

        return slider

    def load_config(self) -> dict:
        """Wczytuje zapisaną konfigurację lub zwraca domyślne wartości"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")

        return self.default_values.copy()

    def save_config(self, values: dict):
        """Zapisuje konfigurację do pliku"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(values, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_current_values(self) -> dict:
        """Pobiera aktualne wartości ze sliderów"""
        return {
            'iterations': int(self.iterations_slider.get()),
            'population_size': int(self.population_slider.get()),
            'mutation_rate': float(self.mutation_slider.get()),
            'crossover_rate': float(self.crossover_slider.get())
        }

    def reset_values(self):
        """Resetuje wartości do domyślnych"""
        self.iterations_slider.set(self.default_values['iterations'])
        self.population_slider.set(self.default_values['population_size'])
        self.mutation_slider.set(self.default_values['mutation_rate'])
        self.crossover_slider.set(self.default_values['crossover_rate'])

    def save_and_run(self):
        """Zapisuje konfigurację i uruchamia generator planu"""
        values = self.get_current_values()
        self.save_config(values)
        # Tu dodamy później wywołanie głównego algorytmu
        logger.info(f"Starting scheduler with parameters: {values}")

    def create_widgets(self):
        # Zakładki
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill='both', expand=True, padx=20, pady=20)

        # Zakładka struktury szkoły
        school_tab = self.tabview.add("Struktura szkoły")
        self.school_frame = SchoolInputFrame(school_tab)
        self.school_frame.pack(fill='both', expand=True)

        # Zakładka parametrów
        params_tab = self.tabview.add("Parametry")
        self.params_frame = self.create_params_frame(params_tab)
        self.params_frame.pack(fill='both', expand=True)

        # Przycisk uruchomienia
        self.run_button = ctk.CTkButton(
            self,
            text="Generuj plan",
            command=self.run_scheduler
        )
        self.run_button.pack(pady=10)

    def run_scheduler(self):
        """Uruchamia generowanie planu"""
        school_config = self.school_frame.get_configuration()
        params = self.get_current_values()

        # Utwórz szkołę
        school = School(school_config)

        # Utwórz generator
        generator = ScheduleGenerator(school, params)

        # Utwórz okno postępu
        progress_window = self.create_progress_window()

        def update_progress(progress_data):
            progress_window.update_progress(
                progress_data['progress_percent'],
                f"Generacja {progress_data['generation']}\n"
                f"Najlepszy wynik: {progress_data['best_fitness']:.2f}\n"
                f"Średni wynik: {progress_data['avg_fitness']:.2f}"
            )

        # Uruchom generowanie w osobnym wątku
        thread = threading.Thread(
            target=lambda: self.run_generation(generator, update_progress)
        )
        thread.start()

    def run_generation(self, generator: ScheduleGenerator, progress_callback):
        """Uruchamia generowanie planu w osobnym wątku"""
        try:
            schedule, progress_history = generator.generate(progress_callback)

            # Pokaż wyniki
            self.show_results(schedule, progress_history)

        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania planu: {str(e)}")

    def show_results(self, schedule: Schedule, progress_history: List[Dict]):
        """Pokazuje okno z wynikami"""
        results_window = ScheduleResultsWindow(schedule, progress_history)
        results_window.grab_set()  # Zablokuj główne okno