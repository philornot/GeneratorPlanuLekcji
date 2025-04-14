# src/gui/app.py
import json
import threading
from pathlib import Path
from tkinter import messagebox
from typing import List, Dict

import customtkinter as ctk
import sv_ttk

from src.genetic import ScheduleGenerator, GenerationStats
from src.gui.input_frame import SchoolInputFrame
from src.gui.results_view import ScheduleResultsWindow
from src.models.schedule import Schedule
from src.models.school import School
from src.utils.logger import GPLLogger


class ProgressWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Postęp generowania planu")
        self.geometry("400x150")

        self.logger = GPLLogger(__name__)

        # Etykieta z opisem
        self.status_label = ctk.CTkLabel(self, text="Inicjalizacja...")
        self.status_label.pack(pady=10)

        # Pasek postępu
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=10, padx=20, fill='x')
        self.progress_bar.set(0)

    def update_progress(self, progress_data):
        try:
            # Sprawdź, czy widget wciąż istnieje
            if self.winfo_exists():
                self.progress_bar.set(progress_data['progress_percent'] / 100)
                self.status_label.configure(text=f"Generacja {progress_data['generation']}\n"
                                                 f"Najlepszy wynik: {progress_data['best_fitness']:.2f}\n"
                                                 f"Średni wynik: {progress_data['avg_fitness']:.2f}")
                self.update()  # odśwież okno
        except Exception as e:
            print(f"Błąd aktualizacji postępu: {e}")


class SchedulerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja okna
        self.title("School Scheduler - Konfiguracja")
        self.geometry("600x400")
        sv_ttk.set_theme("light")
        self.logger = GPLLogger(__name__)

        # Ścieżka do pliku z konfiguracją
        self.config_path = Path('data/config.json')

        # Domyślne wartości
        self.default_values = {
            'iterations': 2000,  # zwiększone z 1000
            'population_size': 200,  # zwiększone ze 100
            'mutation_rate': 0.2,  # zwiększone z 0.1
            'crossover_rate': 0.8
        }

        # Wczytaj zapisane wartości lub użyj domyślnych
        self.values = self.load_config()

        # Flagi zatrzymania i referencja do generatora
        self.stop_requested = False
        self.generator = None

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

        def on_slider_change(val):
            # Zaokrąglij wartość do rozsądnej liczby miejsc po przecinku
            rounded_val = round(val, 3)  # 3 miejsca po przecinku powinno wystarczyć
            value_label.configure(text=f"{rounded_val:.3f}")
            current_values = self.get_current_values()
            self.save_config(current_values)
            self.logger.debug(f"Saved new configuration: {current_values}")

        # Zabezpieczenie przed dzieleniem przez zero
        num_steps = 100  # Domyślna wartość
        if step > 0:
            num_steps = int((max_val - min_val) / step)

        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=num_steps,
            command=on_slider_change,
        )
        slider.pack(fill='x', padx=10)
        slider.set(default_val)

        return slider

    def create_params_frame(self, parent) -> ctk.CTkFrame:
        """Tworzy ramkę z parametrami algorytmu"""
        frame = ctk.CTkFrame(parent)

        # Nagłówek
        header = ctk.CTkLabel(
            frame,
            text="Parametry algorytmu",
            font=("Helvetica", 16, "bold")
        )
        header.pack(pady=10)

        # Slider dla liczby iteracji
        self.iterations_slider = self.create_parameter_slider(
            frame,
            "Liczba iteracji:",
            min_val=100,
            max_val=5000,
            default_val=self.values['iterations'],
            step=100
        )

        # Slider dla wielkości populacji
        self.population_slider = self.create_parameter_slider(
            frame,
            "Wielkość populacji:",
            min_val=50,
            max_val=500,
            default_val=self.values['population_size'],
            step=10
        )

        # Slider dla współczynnika mutacji
        self.mutation_slider = self.create_parameter_slider(
            frame,
            "Współczynnik mutacji:",
            min_val=0.01,
            max_val=0.5,
            default_val=self.values['mutation_rate'],
            step=0.01
        )

        # Slider dla współczynnika krzyżowania
        self.crossover_slider = self.create_parameter_slider(
            frame,
            "Współczynnik krzyżowania:",
            min_val=0.1,
            max_val=1.0,
            default_val=self.values['crossover_rate'],
            step=0.05
        )

        # Przycisk resetowania
        reset_button = ctk.CTkButton(
            frame,
            text="Reset do domyślnych",
            command=self.reset_values
        )
        reset_button.pack(pady=10)

        return frame

    def load_config(self) -> dict:
        """Wczytuje zapisaną konfigurację lub zwraca domyślne wartości"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")

        return self.default_values.copy()

    def save_config(self, values: dict):
        """Zapisuje konfigurację do pliku"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(values, f, indent=2)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

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
        self.logger.info(f"Starting scheduler with parameters: {values}")

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

        # Frame na przyciski
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10)

        # Przycisk uruchomienia
        self.run_button = ctk.CTkButton(
            self.button_frame,
            text="Generuj plan",
            command=self.run_scheduler
        )
        self.run_button.pack(side='left', padx=10)

        # Przycisk zatrzymania (początkowo wyłączony)
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="Zatrzymaj generację",
            command=self.stop_generation,
            state="disabled",
            fg_color="#B22222",  # Czerwony kolor przycisku
            hover_color="#8B0000"  # Ciemniejszy czerwony przy najechaniu
        )
        self.stop_button.pack(side='left', padx=10)

    def stop_generation(self):
        """Zatrzymuje trwającą generację planu"""
        if self.generator:
            self.logger.info("Zatrzymanie generacji na żądanie użytkownika")
            self.stop_requested = True
            messagebox.showinfo("Zatrzymywanie",
                                "Proces generacji zostanie zatrzymany po zakończeniu bieżącej generacji.")

    def run_scheduler(self):
        """Uruchamia generowanie planu"""
        school_config = self.school_frame.get_configuration()
        if not school_config['class_counts']['first_year']:
            messagebox.showerror("Błąd", "Musisz zdefiniować co najmniej jedną klasę pierwszą")
            return

        params = self.get_current_values()

        # Resetuj flagę zatrzymania
        self.stop_requested = False

        # Zmień stan przycisków
        self.stop_button.configure(state="normal")
        self.run_button.configure(state="disabled")

        # Utwórz szkołę
        try:
            school = School(school_config)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się utworzyć szkoły: {str(e)}")
            # Przywróć stan przycisków
            self.stop_button.configure(state="disabled")
            self.run_button.configure(state="normal")
            return

        # Utwórz generator i zapisz referencję
        self.generator = ScheduleGenerator(school, params)

        # Utwórz okno postępu
        progress_window = self.create_progress_window()

        def update_progress(progress_data):
            # Dodaj flagę zatrzymania do danych postępu
            if self.stop_requested:
                progress_data['stopping'] = True
            self.after(0, progress_window.update_progress, progress_data)

        # Uruchom generowanie w osobnym wątku
        thread = threading.Thread(
            target=lambda: self.run_generation(self.generator, update_progress, progress_window)
        )
        thread.start()

    def run_generation(self, generator: ScheduleGenerator, progress_callback, progress_window):
        """Uruchamia generowanie planu w osobnym wątku"""
        try:
            def safe_update_progress(progress_data):
                self.after(0, progress_callback, progress_data)

                # Sprawdź, czy użytkownik zażądał zatrzymania
                if self.stop_requested:
                    generator.stop_generation = True

            schedule, progress_history, generation_stats = generator.generate(safe_update_progress)

            # Zamknij okno postępu
            self.after(0, progress_window.destroy)

            # Pokaż wyniki w głównym wątku
            self.after(0, self.show_results, schedule, progress_history, generation_stats)

            # Resetuj stan przycisków
            self.after(0, lambda: (
                self.run_button.configure(state="normal"),
                self.stop_button.configure(state="disabled")
            ))

        except Exception as e:
            self.logger.error(f"Error during generation: {str(e)}", exc_info=True)
            error_message = str(e)

            def show_error():
                try:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania planu: {error_message}")
                except:
                    # Na wypadek, gdyby okno zostało już zamknięte
                    messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania planu: {error_message}")

                # Przywróć stan przycisków
                self.run_button.configure(state="normal")
                self.stop_button.configure(state="disabled")

            self.after(0, show_error)
