# src/gui/results_view.py

import logging
from tkinter import filedialog
from typing import Dict, List

import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.models.schedule import Schedule, GenerationStats

logger = logging.getLogger(__name__)


class ScheduleResultsWindow(ctk.CTkToplevel):
    def __init__(self, schedule: 'Schedule', progress_history: List[Dict], generation_stats: GenerationStats = None):
        super().__init__()

        self.title("Wyniki generowania planu")
        self.geometry("1200x800")

        # Zmiana z _school na school
        self.school = schedule.school

        # Główny kontener z zakładkami
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill='both', expand=True, padx=10, pady=10)

        # Zakładki
        self.setup_schedule_view(schedule)
        self.setup_progress_chart(progress_history)
        self.setup_statistics_view(schedule, generation_stats)  # Przekazujemy generation_stats

    def setup_schedule_view(self, schedule: 'Schedule'):
        """Tworzy widok planu lekcji"""
        schedule_tab = self.tabview.add("Plan lekcji")

        # Frame na filtry
        filters_frame = ctk.CTkFrame(schedule_tab)
        filters_frame.pack(fill='x', padx=5, pady=5)

        # Filtr klasy
        class_label = ctk.CTkLabel(filters_frame, text="Klasa:")
        class_label.pack(side='left', padx=5)

        # Konwertujemy set na posortowaną listę
        class_list = sorted(list(schedule.class_groups))

        if not class_list:
            logger.error("Brak klas w planie!")
            return

        class_select = ctk.CTkOptionMenu(
            filters_frame,
            values=class_list,
            command=lambda c: self.update_schedule_view(schedule, selected_class=c)
        )
        class_select.pack(side='left', padx=5)

        # Frame na siatkę
        grid_frame = ctk.CTkFrame(schedule_tab, fg_color="gray30")
        grid_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Nagłówki w siatce
        headers = ["Godzina"] + ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
        for col, header in enumerate(headers):
            # Dodaj ramkę dla każdej komórki nagłówka
            cell_frame = ctk.CTkFrame(grid_frame, fg_color="gray20")
            cell_frame.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

            label = ctk.CTkLabel(cell_frame, text=header, font=("Helvetica", 12, "bold"))
            label.pack(expand=True, fill='both', padx=5, pady=5)

        # Godziny lekcji
        hours = ["8:00-8:45", "8:55-9:40", "9:50-10:35", "10:55-11:40",
                 "11:50-12:35", "12:45-13:30", "13:40-14:25", "14:35-15:20"]

        # Inicjalizacja komórek tabeli
        self.schedule_cells = {}
        for row in range(len(hours)):
            # Dodaj godziny w pierwszej kolumnie
            hour_frame = ctk.CTkFrame(grid_frame, fg_color="gray20")
            hour_frame.grid(row=row + 1, column=0, sticky='nsew', padx=1, pady=1)

            hour_label = ctk.CTkLabel(hour_frame, text=hours[row])
            hour_label.pack(expand=True, fill='both', padx=5, pady=5)

            # Dodaj komórki na lekcje
            for col in range(1, len(headers)):
                cell_frame = ctk.CTkFrame(grid_frame, fg_color="gray20")
                cell_frame.grid(row=row + 1, column=col, sticky='nsew', padx=1, pady=1)

                cell = ctk.CTkLabel(cell_frame, text="", width=150)
                cell.pack(expand=True, fill='both', padx=5, pady=5)
                self.schedule_cells[(row, col - 1)] = cell

        # Konfiguracja rozmiaru kolumn/wierszy
        for i in range(len(headers)):
            grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(hours) + 1):
            grid_frame.grid_rowconfigure(i, weight=1)

    def setup_statistics_view(self, schedule: 'Schedule', generation_stats: GenerationStats = None):
        """Tworzy widok statystyk"""
        stats_tab = self.tabview.add("Statystyki")

        # Główny kontener na statystyki
        main_frame = ctk.CTkFrame(stats_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Statystyki generowania
        if generation_stats:
            gen_frame = self._create_stats_section(main_frame, "Statystyki generowania")
            ctk.CTkLabel(gen_frame, text=f"Całkowity czas: {generation_stats.total_time:.2f}s").pack(anchor='w')
            ctk.CTkLabel(gen_frame, text=f"Średni czas generacji: {generation_stats.avg_generation_time:.4f}s").pack(
                anchor='w')
            ctk.CTkLabel(gen_frame, text=f"Min czas generacji: {generation_stats.min_generation_time:.4f}s").pack(
                anchor='w')
            ctk.CTkLabel(gen_frame, text=f"Max czas generacji: {generation_stats.max_generation_time:.4f}s").pack(
                anchor='w')
            ctk.CTkLabel(gen_frame, text=f"Liczba generacji: {generation_stats.total_generations}").pack(anchor='w')

        # Podstawowe informacje
        basic_frame = self._create_stats_section(main_frame, "Podstawowe informacje")
        ctk.CTkLabel(basic_frame, text=f"Liczba klas: {len(schedule.class_groups)}").pack(anchor='w')
        ctk.CTkLabel(basic_frame, text=f"Całkowita liczba lekcji: {len(schedule.lessons)}").pack(anchor='w')

        # Statystyki nauczycieli
        teacher_frame = self._create_stats_section(main_frame, "Obciążenie nauczycieli")
        total_hours = 0
        for teacher in self.school.teachers.values():
            hours = schedule.get_teacher_hours(teacher)
            total_hours += hours['weekly']
            text = f"{teacher.name}: {hours['weekly']}h/tydzień (max dzienny: {max(hours['daily'].values() if hours['daily'] else [0])}h)"
            ctk.CTkLabel(teacher_frame, text=text).pack(anchor='w')

        avg_hours = total_hours / len(self.school.teachers) if self.school.teachers else 0
        ctk.CTkLabel(teacher_frame, text=f"Średnie obciążenie: {avg_hours:.1f}h/tydzień").pack(anchor='w')

        # Statystyki sal
        room_frame = self._create_stats_section(main_frame, "Wykorzystanie sal")
        for classroom in self.school.classrooms.values():
            count = sum(1 for lesson in schedule.lessons if lesson.classroom.id == classroom.id)
            usage = (count / (40)) * 100  # 40 = 8 godzin * 5 dni
            text = f"Sala {classroom.name}: {count} lekcji ({usage:.1f}% wykorzystania)"
            ctk.CTkLabel(room_frame, text=text).pack(anchor='w')

    def _create_stats_section(self, parent, title: str) -> ctk.CTkFrame:
        """Tworzy sekcję statystyk z tytułem"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', padx=5, pady=5)

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Helvetica", 12, "bold")
        ).pack(pady=5)

        return frame

    def update_schedule_view(self, schedule: 'Schedule', selected_class: str):
        """Aktualizuje widok planu dla wybranej klasy"""
        # Wyczyść wszystkie komórki
        for cell in self.schedule_cells.values():
            cell.configure(text="")

        # Wypełnij komórki lekcjami
        for lesson in schedule.lessons:
            if lesson.class_group == selected_class:
                cell = self.schedule_cells.get((lesson.hour, lesson.day))
                if cell:
                    text = f"{lesson.subject.name}\n{lesson.teacher.name}\nSala {lesson.classroom.name}"
                    cell.configure(text=text)

    # src/gui/results_view.py
    def setup_progress_chart(self, progress_history: List[Dict]):
        """Tworzy wykres postępu"""
        progress_tab = self.tabview.add("Postęp")

        # Utworzenie ramki dla wykresu
        chart_frame = ctk.CTkFrame(progress_tab)
        chart_frame.pack(fill='both', expand=True)

        def create_figure():
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            generations = [p['generation'] for p in progress_history]
            best_scores = [p['best_fitness'] for p in progress_history]
            avg_scores = [p['avg_fitness'] for p in progress_history]

            # Wykres najlepszego i średniego wyniku
            ax1.plot(generations, best_scores, label='Najlepszy wynik', color='green')
            ax1.plot(generations, avg_scores, label='Średni wynik', color='blue')
            ax1.set_title('Postęp optymalizacji')
            ax1.set_xlabel('Generacja')
            ax1.set_ylabel('Ocena')
            ax1.legend()
            ax1.grid(True)

            # Wykres poprawy (różnica między kolejnymi najlepszymi wynikami)
            improvements = np.diff(best_scores)
            ax2.bar(generations[1:], improvements, color='orange')
            ax2.set_title('Wielkość poprawy między generacjami')
            ax2.set_xlabel('Generacja')
            ax2.set_ylabel('Poprawa')
            ax2.grid(True)

            return fig

        # Tworzenie wykresu w głównym wątku
        fig = create_figure()

        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)

        # Dodanie paska narzędzi
        toolbar_frame = ctk.CTkFrame(chart_frame)
        toolbar_frame.pack(fill='x')

        def save_plot():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if file_path:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')

        save_button = ctk.CTkButton(
            toolbar_frame,
            text="Zapisz wykres",
            command=save_plot
        )
        save_button.pack(side='right', padx=5, pady=5)
