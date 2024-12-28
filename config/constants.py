# config/constants.py
from typing import Dict, List, Set

# Godziny lekcyjne
HOURS = [
    (8, 0, 8, 45),  # 1. lekcja
    (8, 50, 9, 35),  # 2. lekcja
    (9, 45, 10, 30),  # 3. lekcja
    (10, 45, 11, 30),  # 4. lekcja
    (11, 40, 12, 25),  # 5. lekcja
    (12, 55, 13, 40),  # 6. lekcja
    (13, 50, 14, 35),  # 7. lekcja
    (14, 40, 15, 25),  # 8. lekcja
    (15, 30, 16, 15)  # 9. lekcja
]

# Liczba godzin tygodniowo dla każdego rocznika
WEEKLY_HOURS: Dict[int, int] = {
    1: 25,
    2: 32,
    3: 35,
    4: 28
}

# Przedmioty dla całej klasy
REGULAR_SUBJECTS: Dict[str, Dict[int, int]] = {
    'Polski': {1: 4, 2: 4, 3: 4, 4: 4},
    'Matematyka': {1: 4, 2: 4, 3: 4, 4: 3},
    'Niemiecki': {1: 2, 2: 2, 3: 2, 4: 2},
    'Francuski': {1: 2, 2: 2, 3: 2, 4: 2},
    'Hiszpański': {1: 2, 2: 2, 3: 2, 4: 2},
    'Fizyka': {1: 1, 2: 2, 3: 2, 4: 2},
    'Biologia': {1: 1, 2: 2, 3: 2, 4: 1},
    'Chemia': {1: 1, 2: 2, 3: 2, 4: 1},
    'Historia': {1: 2, 2: 2, 3: 2, 4: 2},
    'HiT': {1: 1, 2: 1, 3: 0, 4: 0},
    'Przedsiębiorczość': {1: 0, 2: 1, 3: 1, 4: 0},
    'Religia': {1: 1, 2: 1, 3: 1, 4: 1}
}

# Przedmioty dzielone na grupy
SPLIT_SUBJECTS: Dict[str, Dict[int, int]] = {
    'Angielski': {1: 3, 2: 3, 3: 3, 4: 3},
    'Informatyka': {1: 1, 2: 1, 3: 1, 4: 1},
    'WF': {1: 3, 2: 3, 3: 3, 4: 3}
}

# Przedmioty z ograniczeniem godzin pod rząd
MAX_CONSECUTIVE_HOURS: Dict[str, int] = {
    'Matematyka': 2,
    'Polski': 2,
    'Informatyka': 2,
    'WF': 1
}

# Przedmioty, które nie mogą być pierwsze ani ostatnie
RESTRICTED_HOURS_SUBJECTS: Set[str] = {'Matematyka', 'Fizyka'}

# Sale lekcyjne
REGULAR_ROOMS: List[int] = [i for i in range(1, 29) if i not in [14, 24]]
COMPUTER_ROOMS: List[int] = [14, 24]
GYM_ROOMS: Dict[str, int] = {
    'SILOWNIA': 1,  # Pojemność: 1 grupa
    'MALA_SALA': 3,  # Pojemność: 3 grupy
    'DUZA_HALA': 6  # Pojemność: 6 grup
}

# Pary powiązanych przedmiotów (dla nauczycieli uczących 2 przedmiotów)
RELATED_SUBJECTS: List[Set[str]] = [
    {'Matematyka', 'Fizyka'},
    {'Biologia', 'Chemia'},
    # można dodać więcej par
]
