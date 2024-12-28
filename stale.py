from enum import Enum, auto
from typing import Dict, Tuple, Set, List


class TypSali(Enum):
    """Typy sal dostępnych w szkole"""
    ZWYKLA = auto()  # Sala na zwykłe przedmioty (26 sal)
    INFORMATYCZNA = auto()  # Sala komputerowa (2 sale)
    SILOWNIA = auto()  # Sala do WF (1 sala - 1 grupa)
    MALA_SALA_GIM = auto()  # Sala do WF (1 sala - 3 grupy)
    DUZA_HALA = auto()  # Sala do WF (1 sala - 6 grup)


# Godziny lekcyjne w formacie (początek, koniec)
GODZINY_LEKCJI: List[Tuple[str, str]] = [
    ("08:00", "08:45"),  # 1 lekcja
    ("08:50", "09:35"),  # 2 lekcja
    ("09:45", "10:30"),  # 3 lekcja
    ("10:45", "11:30"),  # 4 lekcja
    ("11:40", "12:25"),  # 5 lekcja
    ("12:55", "13:40"),  # 6 lekcja
    ("13:50", "14:35"),  # 7 lekcja
    ("14:40", "15:25"),  # 8 lekcja
    ("15:30", "16:15")  # 9 lekcja
]

DNI_TYGODNIA: List[str] = [
    'Poniedziałek',
    'Wtorek',
    'Środa',
    'Czwartek',
    'Piątek'
]

# Przedmioty i ich wymiar godzinowy tygodniowo dla każdego rocznika
# Format: (1kl, 2kl, 3kl, 4kl)
PRZEDMIOTY_ROCZNIKI: Dict[str, Tuple[int, int, int, int]] = {
    # Przedmioty dla całej klasy
    'polski': (4, 4, 4, 4),
    'matematyka': (4, 4, 4, 3),
    'niemiecki': (2, 2, 2, 2),
    'francuski': (2, 2, 2, 2),
    'hiszpański': (2, 2, 2, 2),
    'fizyka': (1, 2, 2, 2),
    'biologia': (1, 2, 2, 1),
    'chemia': (1, 2, 2, 1),
    'historia': (2, 2, 2, 2),
    'HiT': (1, 1, 0, 0),
    'przedsiębiorczość': (0, 1, 1, 0),
    'religia': (1, 1, 1, 1),

    # Przedmioty dzielone na grupy
    'angielski': (3, 3, 3, 3),
    'informatyka': (1, 1, 1, 1),
    'WF': (3, 3, 3, 3)
}

# Łączna liczba godzin tygodniowo dla każdego rocznika
GODZINY_W_TYGODNIU: Dict[int, int] = {
    1: 25,  # Pierwsze klasy
    2: 32,  # Drugie klasy
    3: 35,  # Trzecie klasy
    4: 28  # Czwarte klasy
}

# Zbiory przedmiotów ze specjalnymi wymaganiami
PRZEDMIOTY_DZIELONE: Set[str] = {
    'angielski',
    'informatyka',
    'WF'
}

PRZEDMIOTY_PIERWSZE_OSTATNIE: Set[str] = {
    'religia'  # Musi być bezpośrednio przed pierwszą lub po ostatniej lekcji klasy
}

PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH: Set[str] = {
    'matematyka',
    'fizyka'
}

PRZEDMIOTY_POD_RZAD: Set[str] = {
    'matematyka',  # maks 2h
    'polski',  # maks 2h
    'informatyka'  # maks 2h
}


def oblicz_potrzebne_godziny() -> Dict[str, int]:
    """
    Oblicza całkowitą liczbę godzin tygodniowo potrzebną dla każdego przedmiotu.
    Uwzględnia liczebność klas (5 w każdym roczniku) i podział na grupy.
    """
    potrzebne_godziny = {}

    for przedmiot, wymiar in PRZEDMIOTY_ROCZNIKI.items():
        suma_godzin = sum(wymiar) * 5  # 5 klas w każdym roczniku

        if przedmiot in PRZEDMIOTY_DZIELONE:
            suma_godzin *= 2  # Przedmioty dzielone potrzebują 2x więcej godzin

        potrzebne_godziny[przedmiot] = suma_godzin

    return potrzebne_godziny


if __name__ == "__main__":
    # Test - wyświetl potrzebną liczbę godzin dla każdego przedmiotu
    godziny = oblicz_potrzebne_godziny()
    print("\nPotrzebne godziny tygodniowo dla każdego przedmiotu:")
    for przedmiot, liczba_godzin in sorted(godziny.items()):
        print(f"{przedmiot}: {liczba_godzin}h")