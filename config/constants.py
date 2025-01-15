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
    1: 31,  # Minimum z "31–35 + 3"
    2: 35,  # Maksimum z "31–35 + 3"
    3: 31,  # Minimum z "31 + 3"
    4: 24  # Maksimum z "24 + 2"
}

# Przedmioty dla całej klasy
REGULAR_SUBJECTS: Dict[str, Dict[int, int]] = {
    'Polski': {1: 4, 2: 4, 3: 4, 4: 4},
    'Matematyka': {1: 4, 2: 4, 3: 4, 4: 4},
    'Język obcy nowożytny': {1: 3, 2: 3, 3: 3, 4: 2},
    'Drugi język obcy': {1: 2, 2: 2, 3: 2, 4: 2},
    'Historia': {1: 2, 2: 2, 3: 2, 4: 1},
    'HiT': {1: 1, 2: 1, 3: 0, 4: 0},
    'Biologia': {1: 1, 2: 1, 3: 1, 4: 1},
    'Chemia': {1: 1, 2: 1, 3: 1, 4: 1},
    'Fizyka': {1: 1, 2: 1, 3: 1, 4: 1},
    'Geografia': {1: 1, 2: 1, 3: 0, 4: 0},
    'Przedsiębiorczość': {1: 0, 2: 1, 3: 1, 4: 0},
    'Informatyka': {1: 1, 2: 1, 3: 0, 4: 0},
    'Wychowanie fizyczne': {1: 3, 2: 3, 3: 3, 4: 3},
    'Edukacja dla bezpieczeństwa': {1: 0, 2: 0, 3: 1, 4: 0},
    'Zajęcia z wychowawcą': {1: 1, 2: 1, 3: 1, 4: 1},
    'Religia/Etyka': {1: 2, 2: 2, 3: 2, 4: 2}
}

# Przedmioty z ograniczeniem godzin z rzędu
MAX_CONSECUTIVE_HOURS: Dict[str, int] = {
    'Matematyka': 2,
    'Polski': 2,
    'Informatyka': 2,
    'Wychowanie fizyczne': 1  # Tylko 1h dziennie dla danej grupy!
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
    {'Geografia', 'Biologia'},
    {'Język obcy nowożytny', 'Drugi język obcy'}
]

# File: config/constants.py

# Istniejące stałe...

# Wagi przedmiotów dla poszczególnych godzin lekcyjnych
HOUR_WEIGHTS = {
    1: {  # Pierwsza lekcja
        'Język obcy nowożytny': 8,
        'Historia': 7,
        'Geografia': 7,
        'Biologia': 6,
        'Chemia': 6,
        'Informatyka': 5,
        'HiT': 5,
        'Przedsiębiorczość': 5,
        'Wychowanie fizyczne': 4,
        'Drugi język obcy': 4
    },
    2: {  # Druga lekcja
        'Matematyka': 10,
        'Polski': 9,
        'Fizyka': 8,
        'Język obcy nowożytny': 7,
        'Chemia': 7,
        'Biologia': 6
    },
    3: {  # Trzecia lekcja
        'Matematyka': 10,
        'Polski': 9,
        'Fizyka': 8,
        'Chemia': 7,
        'Biologia': 7,
        'Historia': 6
    },
    4: {  # Czwarta lekcja
        'Matematyka': 8,
        'Polski': 8,
        'Historia': 7,
        'Geografia': 7,
        'Język obcy nowożytny': 6,
        'Drugi język obcy': 6
    },
    5: {  # Piąta lekcja
        'Język obcy nowożytny': 7,
        'Drugi język obcy': 7,
        'Geografia': 6,
        'Historia': 6,
        'Wychowanie fizyczne': 5,
        'HiT': 5
    },
    6: {  # Szósta lekcja
        'Wychowanie fizyczne': 7,
        'Informatyka': 6,
        'HiT': 5,
        'Przedsiębiorczość': 5,
        'Zajęcia z wychowawcą': 5
    },
    7: {  # Siódma lekcja
        'Wychowanie fizyczne': 6,
        'Informatyka': 5,
        'Zajęcia z wychowawcą': 5,
        'Edukacja dla bezpieczeństwa': 4
    },
    8: {  # Ósma lekcja
        'Wychowanie fizyczne': 5,
        'Zajęcia z wychowawcą': 4,
        'Edukacja dla bezpieczeństwa': 4
    }
}

# Domyślne wagi przedmiotów
DEFAULT_SUBJECT_WEIGHTS = {
    'Matematyka': 8,
    'Polski': 8,
    'Fizyka': 7,
    'Chemia': 7,
    'Biologia': 6,
    'Geografia': 6,
    'Historia': 6,
    'Język obcy nowożytny': 6,
    'Drugi język obcy': 5,
    'Informatyka': 5,
    'Wychowanie fizyczne': 5,
    'HiT': 4,
    'Przedsiębiorczość': 4,
    'Zajęcia z wychowawcą': 4,
    'Edukacja dla bezpieczeństwa': 3
}

# Przedmioty maturalne (do bonusu wagowego)
MATURA_SUBJECTS = {'Matematyka', 'Polski', 'Język obcy nowożytny'}

# Modyfikatory wag
WEIGHT_MODIFIERS = {
    'MATURA_BONUS': 1.2,
    'HOURS_MODIFIER_MAX': 1.5
}
