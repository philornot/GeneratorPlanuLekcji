import random
from dataclasses import dataclass
from typing import List, Set


@dataclass
class Nauczyciel:
    id: int
    imie_nazwisko: str
    tytul: str
    przedmioty: List[str]
    dostepne_dni: Set[str]
    maks_godzin_dziennie: int


def generuj_tytul() -> str:
    tytuly = [
        "", "", "", "",  # puste tytuły mają większe prawdopodobieństwo
        "mgr ",
        "dr ",
        "dr hab. ",
        "prof. "
    ]
    return random.choice(tytuly)


def generuj_imie_nazwisko() -> str:
    imiona_meskie = [
        "Adam", "Piotr", "Paweł", "Krzysztof", "Andrzej", "Tomasz", "Jan", "Marek",
        "Michał", "Grzegorz", "Jerzy", "Tadeusz", "Zbigniew", "Stanisław", "Jakub",
        "Dariusz", "Robert", "Maciej", "Mariusz", "Kamil", "Mateusz"
    ]

    imiona_zenskie = [
        "Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Ewa",
        "Krystyna", "Magdalena", "Elżbieta", "Joanna", "Aleksandra", "Zofia",
        "Monika", "Teresa", "Danuta", "Natalia", "Julia", "Karolina", "Beata"
    ]

    nazwiska_meskie = [
        "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
        "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski",
        "Jankowski", "Mazur", "Kwiatkowski", "Krawczyk", "Piotrowski", "Grabowski",
        "Nowakowski", "Pawłowski", "Michalski", "Adamczyk"
    ]

    nazwiska_zenskie = [
        "Nowak", "Kowalska", "Wiśniewska", "Wójcik", "Kowalczyk", "Kamińska",
        "Lewandowska", "Zielińska", "Szymańska", "Woźniak", "Dąbrowska", "Kozłowska",
        "Jankowska", "Mazur", "Kwiatkowska", "Krawczyk", "Piotrowska", "Grabowska",
        "Nowakowska", "Pawłowska", "Michalska", "Adamczyk"
    ]

    # Losujemy płeć
    if random.random() < 0.65:  # 65% szans na kobietę (częściej w zawodzie nauczyciela)
        imie = random.choice(imiona_zenskie)
        nazwisko = random.choice(nazwiska_zenskie)
    else:
        imie = random.choice(imiona_meskie)
        nazwisko = random.choice(nazwiska_meskie)

    return f"{imie} {nazwisko}"


def generuj_przedmioty() -> List[str]:
    wszystkie_przedmioty = {
        'polski': 4,
        'angielski': 4,
        'niemiecki': 2,
        'francuski': 2,
        'hiszpański': 2,
        'matematyka': 4,
        'fizyka': 2,
        'informatyka': 2,
        'biologia': 2,
        'chemia': 2,
        'przedsiębiorczość': 1,
        'historia': 3,
        'HiT': 2,
        'religia': 2,
        'WF': 6
    }

    # Losujemy 1 lub 2 przedmioty
    liczba_przedmiotow = random.choices([1, 2], weights=[70, 30])[0]
    przedmioty = []
    dostepne_przedmioty = list(wszystkie_przedmioty.keys())

    for _ in range(liczba_przedmiotow):
        if dostepne_przedmioty:
            przedmiot = random.choice(dostepne_przedmioty)
            przedmioty.append(przedmiot)
            dostepne_przedmioty.remove(przedmiot)

            # Usuwamy przedmioty, które nie mogą być łączone
            if przedmiot in ['matematyka', 'fizyka']:
                for p in ['matematyka', 'fizyka']:
                    if p in dostepne_przedmioty:
                        dostepne_przedmioty.remove(p)

    return przedmioty


def generuj_dostepne_dni() -> Set[str]:
    dni = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek']
    # 40 nauczycieli pracuje w innych szkołach
    if random.random() < 0.5:  # 50% szans na pełny etat
        return set(dni)
    else:
        # 13 pracuje 2 dni, 27 pracuje 3 dni
        liczba_dni = random.choices([2, 3], weights=[13, 27])[0]
        return set(random.sample(dni, liczba_dni))


def generuj_nauczycieli(liczba_nauczycieli: int = 80) -> List[Nauczyciel]:
    nauczyciele = []
    for i in range(liczba_nauczycieli):
        tytul = generuj_tytul()
        imie_nazwisko = generuj_imie_nazwisko()
        przedmioty = generuj_przedmioty()
        dostepne_dni = generuj_dostepne_dni()
        maks_godzin = random.randint(5, 8)  # maksymalna liczba godzin dziennie

        nauczyciele.append(Nauczyciel(
            id=i + 1,
            imie_nazwisko=f"{tytul}{imie_nazwisko}",
            tytul=tytul,
            przedmioty=przedmioty,
            dostepne_dni=dostepne_dni,
            maks_godzin_dziennie=maks_godzin
        ))

    return nauczyciele


# Test generatora
if __name__ == "__main__":
    nauczyciele = generuj_nauczycieli()
    print("\nWygenerowani nauczyciele (przykład pierwszych 5):")
    for nauczyciel in nauczyciele[:5]:
        print(f"\nID: {nauczyciel.id}")
        print(f"Imię i nazwisko: {nauczyciel.imie_nazwisko}")
        print(f"Przedmioty: {', '.join(nauczyciel.przedmioty)}")
        print(f"Dostępne dni: {', '.join(sorted(nauczyciel.dostepne_dni))}")
        print(f"Maksymalna liczba godzin dziennie: {nauczyciel.maks_godzin_dziennie}")
