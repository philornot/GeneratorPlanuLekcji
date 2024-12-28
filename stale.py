from enum import Enum, auto
from typing import Dict


class TypSali(Enum):
    ZWYKLA = auto()
    INFORMATYCZNA = auto()
    SILOWNIA = auto()
    MALA_SALA_GIM = auto()
    DUZA_HALA = auto()


# Czasy lekcji i przerw
GODZINY_LEKCJI = [
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

DNI_TYGODNIA = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek']

# Przedmioty i ich tygodniowy wymiar godzin dla różnych roczników
PRZEDMIOTY_ROCZNIKI = {
    # (liczba_godzin_1kl, liczba_godzin_2kl, liczba_godzin_3kl, liczba_godzin_4kl)
    'polski': (4, 4, 4, 4),
    'matematyka': (4, 4, 4, 3),
    'angielski': (3, 3, 3, 3),  # grupy
    'niemiecki': (2, 2, 2, 2),
    'francuski': (2, 2, 2, 2),
    'hiszpański': (2, 2, 2, 2),
    'fizyka': (1, 2, 2, 2),
    'informatyka': (1, 1, 1, 1),  # grupy
    'biologia': (1, 2, 2, 1),
    'chemia': (1, 2, 2, 1),
    'historia': (2, 2, 2, 2),
    'WF': (3, 3, 3, 3),  # grupy
    'HiT': (1, 1, 0, 0),
    'przedsiębiorczość': (0, 1, 1, 0),
    'religia': (2, 2, 2, 2)
}

# Łączna liczba godzin tygodniowo dla każdego rocznika
GODZINY_W_TYGODNIU = {
    1: 25,
    2: 32,
    3: 35,
    4: 28
}

# Przedmioty dzielone na grupy
PRZEDMIOTY_DZIELONE = {'angielski', 'informatyka', 'WF'}

# Ograniczenia dla przedmiotów
PRZEDMIOTY_PIERWSZE_OSTATNIE = {'religia'}  # tylko na początku lub końcu dnia
PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH = {'matematyka', 'fizyka'}  # nie mogą być na początku/końcu
PRZEDMIOTY_POD_RAD = {'matematyka', 'polski', 'informatyka'}  # maks 2h pod rząd


def oblicz_potrzebne_godziny() -> Dict[str, int]:
    """Oblicza całkowitą liczbę godzin tygodniowo potrzebną dla każdego przedmiotu."""
    potrzebne_godziny = {}

    for przedmiot, godziny in PRZEDMIOTY_ROCZNIKI.items():
        suma_godzin = sum(godziny) * 5  # 5 klas w każdym roczniku

        # Dla przedmiotów dzielonych na grupy, potrzebujemy dwa razy więcej godzin
        if przedmiot in PRZEDMIOTY_DZIELONE:
            suma_godzin *= 2

        potrzebne_godziny[przedmiot] = suma_godzin

    return potrzebne_godziny


if __name__ == "__main__":
    # Test obliczania potrzebnych godzin
    godziny = oblicz_potrzebne_godziny()
    print("\nPotrzebne godziny tygodniowo dla każdego przedmiotu:")
    for przedmiot, liczba_godzin in godziny.items():
        print(f"{przedmiot}: {liczba_godzin}h")
