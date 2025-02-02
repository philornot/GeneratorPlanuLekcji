# src/gui/results_view.py

import customtkinter as ctk
from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class ScheduleResultsWindow(ctk.CTkToplevel):
    def __init__(self, schedule: 'Schedule', progress_history: List[Dict]):
        super().__init__()

        self.title("Wyniki generowania planu")
        self.geometry("1200x800")

        # Główny kontener z zakładkami
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill='both', expand=True, padx=10, pady=10)

        # Zakładki
        self.setup_schedule_view(schedule)
        self.setup_progress_chart(progress_history)
        self.setup_statistics_view(schedule)

    def setup_schedule_view(self, schedule: 'Schedule'):
        """Tworzy widok planu lekcji"""
        schedule_tab = self.tabview.add("Plan lekcji")

        # Frame na filtry
        filters_frame = ctk.CTkFrame(schedule_tab)
        filters_frame.pack(fill='x', padx=5, pady=5)

        # Filtr klasy
        class_label = ctk.CTkLabel(filters_frame, text="Klasa:")
        class_label.pack(side='left', padx=5)

        class_select = ctk.CTkOptionMenu(
            filters_frame,
            values=sorted(list(schedule.class_groups)),
            command=lambda c: self.update_schedule_view(schedule, selected_class=c)
        )
        class_select.pack(side='left', padx=5)

        # Tabela z planem
        table_frame = ctk.CTkFrame(schedule_tab)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Nagłówki
        headers = ["Godzina"] + [f"Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(table_frame, text=header, font=("Helvetica", 12, "bold"))
            label.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

        # Godziny lekcji
        hours = ["8:00-8:45", "8:55-9:40", "9:50-10:35", "10:55-11:40",
                 "11:50-12:35", "12:45-13:30", "13:40-14:25", "14:35-15:20"]

        for row, hour in enumerate(hours, 1):
            label = ctk.CTkLabel(table_frame, text=hour)
            label.grid(row=row, column=0, sticky='nsew', padx=1, pady=1)

        # Inicjalizacja komórek tabeli
        self.schedule_cells = {}
        for row in range(1, len(hours) + 1):
            for col in range(1, len(headers)):
                cell = ctk.CTkLabel(table_frame, text="", width=150)
                cell.grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
                self.schedule_cells[(row - 1, col - 1)] = cell

        # Pokaż plan dla pierwszej klasy
        if schedule.class_groups:
            self.update_schedule_view(schedule, schedule.class_groups[0])

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

    def setup_progress_chart(self, progress_history: List[Dict]):
        """Tworzy wykres postępu"""
        progress_tab = self.tabview.add("Postęp")

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

        canvas = FigureCanvasTkAgg(fig, progress_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def setup_statistics_view(self, schedule: 'Schedule'):
        """Tworzy widok statystyk"""
        stats_tab = self.tabview.add("Statystyki")

        # Statystyki nauczycieli
        teacher_frame = ctk.CTkFrame(stats_tab)
        teacher_frame.pack(fill='x', padx=5, pady=5)

        ctk.CTkLabel(
            teacher_frame,
            text="Obciążenie nauczycieli",
            font=("Helvetica", 12, "bold")
        ).pack()

        for teacher in schedule.get_all_teachers():
            hours = schedule.get_teacher_hours(teacher)
            text = f"{teacher.name}: {hours['weekly']} godz./tydzień"
            ctk.CTkLabel(teacher_frame, text=text).pack()

        # Statystyki sal
        classroom_frame = ctk.CTkFrame(stats_tab)
        classroom_frame.pack(fill='x', padx=5, pady=5)

        ctk.CTkLabel(
            classroom_frame,
            text="Wykorzystanie sal",
            font=("Helvetica", 12, "bold")
        ).pack()

        for classroom in schedule.get_all_classrooms():
            usage = schedule.get_classroom_usage(classroom)
            text = f"Sala {classroom.name}: {usage}% wykorzystania"
            ctk.CTkLabel(classroom_frame, text=text).pack()