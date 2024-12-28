from dataclasses import dataclass
from typing import List, Dict

from infrastruktura import Sala, Klasa, Grupa
from nauczyciele import Nauczyciel


@dataclass
class Lekcja:
    przedmiot: str
    nauczyciel: Nauczyciel
    sala: Sala
    grupy: List[Grupa]  # lista grup które mają tę lekcję
    godzina: int  # indeks z GODZINY_LEKCJI
    dzien: str  # jeden z DNI_TYGODNIA


@dataclass
class PlanLekcji:
    klasa: Klasa
    lekcje: Dict[str, Dict[int, List[Lekcja]]]  # dzien -> godzina -> lista lekcji

    def dodaj_lekcje(self, lekcja: Lekcja) -> None:
        if lekcja.dzien not in self.lekcje:
            self.lekcje[lekcja.dzien] = {}
        if lekcja.godzina not in self.lekcje[lekcja.dzien]:
            self.lekcje[lekcja.dzien][lekcja.godzina] = []
        self.lekcje[lekcja.dzien][lekcja.godzina].append(lekcja)


class BrakDostepnegoTerminuError(Exception):
    """Wyjątek rzucany, gdy nie można znaleźć terminu dla lekcji."""
    pass


class BrakNauczycielaError(Exception):
    """Wyjątek rzucany, gdy nie można znaleźć nauczyciela dla przedmiotu."""
    pass
