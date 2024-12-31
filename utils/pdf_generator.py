from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak


class SchedulePDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        # Style dla tytułów
        self.styles['Title'].fontName = 'Helvetica-Bold'
        self.styles['Title'].fontSize = 24
        self.styles['Title'].alignment = TA_CENTER
        self.styles['Title'].spaceAfter = 30

        # Style dla nagłówków klas
        self.styles.add(ParagraphStyle(
            name='ClassHeader',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_LEFT,
            spaceAfter=10
        ))

        # Style dla podtytułów
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.gray
        ))

    def _create_title_page(self, story, schedule, generation_time, execution_time, iterations):
        """Tworzy pierwszą stronę ze statystykami"""
        story.append(Paragraph("Plan Lekcji - Raport Generowania", self.styles['Title']))
        story.append(Spacer(1, 20))

        # Tabela statystyk
        data = [
            ["Data wygenerowania:", generation_time],
            ["Czas wykonania:", f"{execution_time:.2f} sekund"],
            ["Liczba iteracji:", str(iterations)],
            ["Liczba klas:", str(len(schedule.classes))],
            ["Liczba nauczycieli:", str(len(schedule.teachers))],
            ["Liczba sal:", str(len(schedule.classrooms))],
            ["Ocena ogólna:", f"{schedule.calculate_schedule_score():.2f}/100"],
            ["Liczba konfliktów:", str(len(schedule.get_conflicts()))]
        ]

        table = Table(data, colWidths=[200, 300])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(table)
        story.append(PageBreak())

    def _create_schedule_table(self, school_class):
        """Tworzy tabelę planu lekcji dla pojedynczej klasy"""
        hours = [
            "8:00-8:45", "8:50-9:35", "9:45-10:30", "10:45-11:30",
            "11:40-12:25", "12:55-13:40", "13:50-14:35", "14:40-15:25",
            "15:30-16:15"
        ]

        # Przygotuj dane tabeli
        table_data = [['Godzina', 'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek']]

        for hour_idx, hour in enumerate(hours, 1):
            row = [hour]
            for day in range(5):
                cell_content = []
                lessons = school_class.schedule[day][hour_idx]

                if not lessons:
                    cell_content.append('-')
                else:
                    for lesson in lessons:
                        cell_content.append(f"{lesson.subject}")
                        cell_content.append(f"s.{lesson.room_id}")

                row.append('\n'.join(cell_content))
            table_data.append(row)

        # Utwórz tabelę z odpowiednimi wymiarami
        col_widths = [2.5 * cm] + [4.5 * cm] * 5
        row_heights = [0.8 * cm] + [1.5 * cm] * 9

        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)

        # Stylizacja tabeli
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))

        return table

    def generate_pdf(self, schedule, output_path: str, generation_time: str,
                     execution_time: float, iterations: int):
        """Generuje pełny PDF z planem lekcji"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        story = []

        # Pierwsza strona — statystyki
        self._create_title_page(story, schedule, generation_time, execution_time, iterations)

        # Kolejne strony — plany lekcji dla każdej klasy
        for class_name, school_class in sorted(schedule.classes.items()):
            story.append(Paragraph(f"Plan lekcji - Klasa {class_name}", self.styles['ClassHeader']))
            story.append(
                Paragraph(f"Wychowawca: {school_class.class_teacher_id} | Sala wychowawcza: {school_class.home_room}",
                          self.styles['SubHeader']))
            story.append(Spacer(1, 0.2 * inch))

            table = self._create_schedule_table(school_class)
            story.append(table)

            if class_name != sorted(schedule.classes.keys())[-1]:
                story.append(PageBreak())

        doc.build(story)
