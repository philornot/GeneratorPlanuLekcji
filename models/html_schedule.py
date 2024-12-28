# models/html_schedule.py
class HTMLSchedule:
    def __init__(self, schedule):
        self.schedule = schedule

    def to_html(self):
        """Konwertuje plan do formatu HTML"""
        pass

    def save_html(self, filename):
        """Zapisuje plan do pliku HTML"""
        pass

    @staticmethod
    def generate_class_view(school_class):
        """Generuje widok planu dla pojedynczej klasy"""
        pass

    @staticmethod
    def generate_teacher_view(teacher):
        """Generuje widok planu dla nauczyciela"""
        pass