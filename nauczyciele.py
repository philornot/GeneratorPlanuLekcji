from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
import random
import math
from stale import DNI_TYGODNIA, oblicz_potrzebne_godziny, PRZEDMIOTY_ROCZNIKI


@dataclass(frozen=True)
class Nauczyciel:
    id: int
    imie_nazwisko: str
    tytul: str
    przedmioty: List[str]
    dostepne_dni: Set[str]
    maks_godzin_dziennie: int
    przydzielone_godziny: int = 0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Nauczyciel):
            return NotImplemented
        return self.id == other.id


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

    if random.random() < 0.65:  # 65% szans na kobietę
        imie = random.choice(imiona_zenskie)
        nazwisko = random.choice(nazwiska_zenskie)
    else:
        imie = random.choice(imiona_meskie)
        nazwisko = random.choice(nazwiska_meskie)

    return f"{imie} {nazwisko}"


def oblicz_etaty() -> Dict[str, int]:
    """Oblicza minimalną potrzebną liczbę etatów dla każdego przedmiotu."""
    godziny = oblicz_potrzebne_godziny()
    etaty = {}

    for przedmiot, liczba_godzin in godziny.items():
        # Jeden etat to około 18-20 godzin
        etaty[przedmiot] = math.ceil(liczba_godzin / 18)

    return etaty


def przydziel_dni_pracy(pelny_etat: bool) -> Set[str]:
    if pelny_etat:
        return set(DNI_TYGODNIA)
    else:
        # 13 nauczycieli pracuje 2 dni, 27 pracuje 3 dni
        liczba_dni = random.choices([2, 3], weights=[1, 2])[0]
        return set(random.sample(DNI_TYGODNIA, liczba_dni))


def generuj_nauczycieli() -> List[Nauczyciel]:
    potrzebne_etaty = oblicz_etaty()
    nauczyciele = []
    id_nauczyciela = 1

    # Lista możliwych kombinacji przedmiotów
    kombinacje_przedmiotow = {
        'fizyka': ['matematyka'],
        'matematyka': ['fizyka', 'informatyka'],
        'biologia': ['chemia'],
        'chemia': ['biologia'],
        'historia': ['HiT', 'WOS'],
        'polski': ['historia'],
        'informatyka': ['matematyka', 'przedsiębiorczość']
    }

    # Generowanie nauczycieli dla każdego przedmiotu
    for przedmiot, liczba_etatow in potrzebne_etaty.items():
        etaty_do_obsadzenia = liczba_etatow

        while etaty_do_obsadzenia > 0:
            # Decyzja czy to będzie nauczyciel na pełny etat
            pelny_etat = etaty_do_obsadzenia >= 1 or random.random() < 0.7

            # Decyzja czy nauczyciel będzie miał drugi przedmiot
            drugi_przedmiot = None
            if (przedmiot in kombinacje_przedmiotow and
                    random.random() < 0.3 and
                    pelny_etat):
                mozliwe_drugie = kombinacje_przedmiotow[przedmiot]
                drugi_przedmiot = random.choice(mozliwe_drugie)

            przedmioty = [przedmiot]
            if drugi_przedmiot:
                przedmioty.append(drugi_przedmiot)

            nauczyciel = Nauczyciel(
                id=id_nauczyciela,
                imie_nazwisko=f"{generuj_tytul()}{generuj_imie_nazwisko()}",
                tytul="",
                przedmioty=przedmioty,
                dostepne_dni=przydziel_dni_pracy(pelny_etat),
                maks_godzin_dziennie=random.randint(6, 8) if pelny_etat else random.randint(3, 5),
                przydzielone_godziny=0
            )

            nauczyciele.append(nauczyciel)
            id_nauczyciela += 1

            # Odejmujemy obsadzony etat
            if pelny_etat:
                etaty_do_obsadzenia -= 1
            else:
                etaty_do_obsadzenia -= 0.5

    return nauczyciele


if __name__ == "__main__":
    print("Potrzebna liczba etatów dla każdego przedmiotu:")
    etaty = oblicz_etaty()
    for przedmiot, liczba in etaty.items():
        print(f"{przedmiot}: {liczba}")

    print("\nGenerowanie nauczycieli...")
    nauczyciele = generuj_nauczycieli()
    print(f"\nŁącznie wygenerowano {len(nauczyciele)} nauczycieli")

    # Statystyki przedmiotów
    przedmioty_stat = {}
    for n in nauczyciele:
        for p in n.przedmioty:
            przedmioty_stat[p] = przedmioty_stat.get(p, 0) + 1

    print("\nLiczba nauczycieli dla każdego przedmiotu:")
    for przedmiot in sorted(przedmioty_stat.keys()):
        print(f"{przedmiot}: {przedmioty_stat[przedmiot]}")

    print("\nPrzykładowi nauczyciele (pierwsi 5):")
    for n in nauczyciele[:5]:
        print(f"\nID: {n.id}")
        print(f"Imię i nazwisko: {n.imie_nazwisko}")
        print(f"Przedmioty: {', '.join(n.przedmioty)}")
        print(f"Dostępne dni: {', '.join(sorted(n.dostepne_dni))}")
        print(f"Maksymalna liczba godzin dziennie: {n.maks_godzin_dziennie}")