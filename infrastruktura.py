from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from stale import TypSali, GODZINY_W_TYGODNIU


@dataclass(frozen=True)  # frozen=True sprawia, że obiekt jest niemutowalny i może być użyty jako klucz
class Sala:
    id: int
    typ: TypSali
    pojemnosc_grup: int
    nazwa: str
    dozwolone_przedmioty: Optional[List[str]] = None

    def __hash__(self):
        return hash(self.id)  # używamy id jako unikalnego identyfikatora

    def __eq__(self, other):
        if not isinstance(other, Sala):
            return NotImplemented
        return self.id == other.id


@dataclass(frozen=True)  # Dodajemy frozen=True aby klasa była niemutowalna
class Grupa:
    id: int
    nazwa: str  # np. "1A1" dla pierwszej grupy z 1A
    przedmioty: Tuple[str, ...]  # używamy krotki zamiast listy

    def __hash__(self):
        return hash(self.id)  # używamy id jako klucza do hashowania

    def __eq__(self, other):
        if not isinstance(other, Grupa):
            return NotImplemented
        return self.id == other.id  # porównujemy tylko id grup


@dataclass
class Klasa:
    rocznik: int  # 1-4
    litera: str  # A-E
    grupa1: Grupa
    grupa2: Grupa
    liczba_godzin: int


def generuj_sale() -> Dict[TypSali, List[Sala]]:
    sale = {typ: [] for typ in TypSali}

    # Zwykłe sale (oprócz informatycznych)
    for i in range(1, 29):
        if i not in {14, 24}:  # pomijamy numery sal informatycznych
            sale[TypSali.ZWYKLA].append(
                Sala(
                    id=i,
                    typ=TypSali.ZWYKLA,
                    pojemnosc_grup=2,  # może pomieścić całą klasę lub jedną grupę
                    nazwa=f"Sala {i}",
                    dozwolone_przedmioty=None  # wszystkie przedmioty oprócz informatyki i WF
                )
            )

    # Sale informatyczne
    sale[TypSali.INFORMATYCZNA].extend([
        Sala(
            id=14,
            typ=TypSali.INFORMATYCZNA,
            pojemnosc_grup=1,
            nazwa="Sala 14 (informatyczna)",
            dozwolone_przedmioty=['informatyka']
        ),
        Sala(
            id=24,
            typ=TypSali.INFORMATYCZNA,
            pojemnosc_grup=1,
            nazwa="Sala 24 (informatyczna)",
            dozwolone_przedmioty=['informatyka']
        )
    ])

    # Sale WF
    sale[TypSali.SILOWNIA].append(
        Sala(
            id=101,
            typ=TypSali.SILOWNIA,
            pojemnosc_grup=1,
            nazwa="Siłownia",
            dozwolone_przedmioty=['WF']
        )
    )
    sale[TypSali.MALA_SALA_GIM].append(
        Sala(
            id=102,
            typ=TypSali.MALA_SALA_GIM,
            pojemnosc_grup=3,
            nazwa="Mała sala gimnastyczna",
            dozwolone_przedmioty=['WF']
        )
    )
    sale[TypSali.DUZA_HALA].append(
        Sala(
            id=103,
            typ=TypSali.DUZA_HALA,
            pojemnosc_grup=6,
            nazwa="Duża hala",
            dozwolone_przedmioty=['WF']
        )
    )

    return sale


def generuj_klasy() -> List[Klasa]:
    """Generuje wszystkie klasy szkolne."""
    klasy = []
    id_grupy = 1

    for rocznik in range(1, 5):
        for litera in ['A', 'B', 'C', 'D', 'E']:
            # Tworzenie grup dla klasy
            grupa1 = Grupa(
                id=id_grupy,
                nazwa=f"{rocznik}{litera}1",
                przedmioty=()  # Pusta krotka zamiast pustej listy
            )
            id_grupy += 1

            grupa2 = Grupa(
                id=id_grupy,
                nazwa=f"{rocznik}{litera}2",
                przedmioty=()  # Pusta krotka zamiast pustej listy
            )
            id_grupy += 1

            klasy.append(Klasa(
                rocznik=rocznik,
                litera=litera,
                grupa1=grupa1,
                grupa2=grupa2,
                liczba_godzin=GODZINY_W_TYGODNIU[rocznik]
            ))

    return klasy


if __name__ == "__main__":
    # Test generowania sal
    sale = generuj_sale()
    print("Wygenerowane sale:")
    for typ_sali, lista_sal in sale.items():
        print(f"\n{typ_sali.name}:")
        for sala in lista_sal:
            print(f"- {sala.nazwa} (pojemność: {sala.pojemnosc_grup} grup)")
            if sala.dozwolone_przedmioty:
                print(f"  Dozwolone przedmioty: {', '.join(sala.dozwolone_przedmioty)}")

    # Test generowania klas
    print("\nWygenerowane klasy:")
    klasy = generuj_klasy()
    for klasa in klasy:
        print(f"\nKlasa {klasa.rocznik}{klasa.litera}:")
        print(f"- Grupa 1: {klasa.grupa1.nazwa}")
        print(f"- Grupa 2: {klasa.grupa2.nazwa}")
        print(f"Liczba godzin tygodniowo: {klasa.liczba_godzin}")
