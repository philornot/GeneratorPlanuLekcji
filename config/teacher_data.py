# config/teacher_data.py
import random
from typing import List, Set, Dict, Tuple

# Najpopularniejsze polskie imiona
FIRST_NAMES = {
    'M': [  # Męskie
        'Adam', 'Andrzej', 'Bartosz', 'Dariusz', 'Grzegorz', 'Jacek', 'Jan',
        'Kamil', 'Krzysztof', 'Marek', 'Michał', 'Paweł', 'Piotr', 'Robert',
        'Sławomir', 'Tomasz', 'Wojciech', 'Zbigniew'
    ],
    'K': [  # Żeńskie
        'Agnieszka', 'Anna', 'Barbara', 'Dorota', 'Ewa', 'Halina', 'Iwona',
        'Joanna', 'Katarzyna', 'Magdalena', 'Małgorzata', 'Monika', 'Renata',
        'Teresa', 'Urszula', 'Wioletta', 'Zofia'
    ]
}

# Popularne polskie nazwiska
LAST_NAMES = {
    'M': [  # Męskie
        'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński',
        'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski',
        'Kozłowski', 'Jankowski', 'Mazur', 'Kwiatkowski', 'Krawczyk'
    ],
    'K': [  # Żeńskie
        'Nowak', 'Kowalska', 'Wiśniewska', 'Wójcik', 'Kowalczyk', 'Kamińska',
        'Lewandowska', 'Zielińska', 'Szymańska', 'Woźniak', 'Dąbrowska',
        'Kozłowska', 'Jankowska', 'Mazur', 'Kwiatkowska', 'Krawczyk'
    ]
}

# Preferowane płcie dla przedmiotów (na podstawie statystyk)
SUBJECT_GENDER_RATIO = {
    'Polski': 0.9,  # 90% kobiet
    'Matematyka': 0.6,
    'Angielski': 0.8,
    'Niemiecki': 0.8,
    'Francuski': 0.9,
    'Hiszpański': 0.8,
    'Fizyka': 0.4,  # 40% kobiet
    'Biologia': 0.7,
    'Chemia': 0.6,
    'Historia': 0.5,
    'HiT': 0.5,
    'Przedsiębiorczość': 0.6,
    'WF': 0.5,
    'Informatyka': 0.3,  # 30% kobiet
    'Religia': 0.4
}

# Pary przedmiotów, które mogą być uczone przez jednego nauczyciela
SUBJECT_PAIRS = [
    {'Matematyka', 'Fizyka', 'Informatyka'},
    {'Biologia', 'Chemia'},
    {'Polski', 'Historia'},
    {'Niemiecki', 'Angielski'},
    {'Francuski', 'Hiszpański'}
]


class TeacherDataGenerator:
    @staticmethod
    def generate_teacher_name(subject: str) -> Tuple[str, str]:
        """Generuje imię i nazwisko nauczyciela na podstawie statystyk dla przedmiotu"""
        gender = 'K' if random.random() < SUBJECT_GENDER_RATIO[subject] else 'M'
        first_name = random.choice(FIRST_NAMES[gender])
        last_name = random.choice(LAST_NAMES[gender])
        return first_name, last_name

    @staticmethod
    def calculate_required_teachers(max_teachers: int = 40) -> Dict[str, int]:
        """Oblicza wymaganą liczbę nauczycieli dla każdego przedmiotu

        Args:
            max_teachers: Maksymalna łączna liczba nauczycieli (domyślnie 40)
        """
        # Liczba godzin tygodniowo dla każdego przedmiotu w całej szkole
        total_hours = {
            'Polski': (4 * 4) * 5,  # 4h * 4 roczniki * 5 klas
            'Matematyka': (4 * 3 + 3) * 5,  # (4h * 3 roczniki + 3h * 1 rocznik) * 5 klas
            'Angielski': 3 * 4 * 5 * 2,  # 3h * 4 roczniki * 5 klas * 2 grupy
            'Niemiecki': 2 * 4 * 5,
            'Francuski': 2 * 4 * 5,
            'Hiszpański': 2 * 4 * 5,
            'Fizyka': (1 + 2 * 3) * 5,  # (1h * 1 rocznik + 2h * 3 roczniki) * 5 klas
            'Biologia': (1 + 2 * 2 + 1) * 5,
            'Chemia': (1 + 2 * 2 + 1) * 5,
            'Historia': 2 * 4 * 5,
            'HiT': 1 * 2 * 5,  # 1h * 2 roczniki * 5 klas
            'Przedsiębiorczość': 1 * 2 * 5,
            'WF': 3 * 4 * 5 * 2,  # 3h * 4 roczniki * 5 klas * 2 grupy
            'Informatyka': 1 * 4 * 5 * 2,  # 1h * 4 roczniki * 5 klas * 2 grupy
            'Religia': 1 * 4 * 5
        }

        # Zakładamy, że nauczyciel na pełny etat ma 18h tygodniowo
        # a na część etatu średnio 12h
        required_teachers = {}
        for subject, hours in total_hours.items():
            full_time_count = hours // 18
            if hours % 18 > 0:
                full_time_count += 1  # Dodajemy jednego nauczyciela jeśli są nadgodziny
            required_teachers[subject] = full_time_count

        # Dostosuj liczbę nauczycieli do maksymalnego limitu
        total_teachers = sum(required_teachers.values())
        if total_teachers > max_teachers:
            scaling_factor = max_teachers / total_teachers
            for subject in required_teachers:
                required_teachers[subject] = max(1, int(required_teachers[subject] * scaling_factor))

        # Upewnij się, że mamy dokładnie max_teachers nauczycieli
        while sum(required_teachers.values()) > max_teachers:
            # Znajdź przedmiot z największą liczbą nauczycieli i zmniejsz o 1
            subject = max(required_teachers.items(), key=lambda x: x[1])[0]
            if required_teachers[subject] > 1:
                required_teachers[subject] -= 1

        return required_teachers

    @staticmethod
    def assign_second_subjects(teachers_count: Dict[str, int]) -> List[Set[str]]:
        """Przydziela drugie przedmioty nauczycielom tam gdzie to możliwe"""
        assignments = []
        remaining = teachers_count.copy()

        # Najpierw przydzielamy pojedyncze przedmioty dla minimalnej wymaganej liczby nauczycieli
        for subject, count in teachers_count.items():
            for _ in range(count):
                assignments.append({subject})

        # Próbujemy łączyć przedmioty gdzie to możliwe
        for pair in SUBJECT_PAIRS:
            subjects_in_pair = [s for s in pair if s in remaining and remaining[s] > 0]
            while len(subjects_in_pair) >= 2:
                s1, s2 = random.sample(subjects_in_pair, 2)
                if remaining[s1] > 0 and remaining[s2] > 0:
                    # Znajdujemy nauczyciela z jednym przedmiotem i dodajemy drugi
                    for assignment in assignments:
                        if len(assignment) == 1 and (s1 in assignment or s2 in assignment):
                            assignment.add(s1 if s2 in assignment else s2)
                            remaining[s1] -= 1
                            remaining[s2] -= 1
                            break
                subjects_in_pair = [s for s in pair if s in remaining and remaining[s] > 0]

        return assignments

    @classmethod
    def generate_teacher_data(cls) -> List[Dict]:
        """Generuje pełne dane nauczycieli"""
        required_teachers = cls.calculate_required_teachers()
        subject_assignments = cls.assign_second_subjects(required_teachers)

        teachers = []
        teacher_id = 1

        for subjects in subject_assignments:
            main_subject = random.choice(list(subjects))
            first_name, last_name = cls.generate_teacher_name(main_subject)

            # Określ dostępność (pełny etat lub część etatu)
            is_full_time = random.random() < 0.6  # 60% nauczycieli na pełny etat
            available_days = {0, 1, 2, 3, 4} if is_full_time else set(
                random.sample(range(5), k=3 if random.random() < 0.7 else 2)
            )

            teachers.append({
                'teacher_id': f"T{teacher_id}",
                'first_name': first_name,
                'last_name': last_name,
                'subjects': subjects,
                'is_full_time': is_full_time,
                'available_days': available_days
            })
            teacher_id += 1

        return teachers
