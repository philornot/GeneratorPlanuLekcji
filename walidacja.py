import logging
from typing import List, Dict, Set

from stale import (
    GODZINY_LEKCJI, DNI_TYGODNIA, PRZEDMIOTY_DZIELONE,
    PRZEDMIOTY_PIERWSZE_OSTATNIE, PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH,
    PRZEDMIOTY_POD_RZAD
)
from modele import PlanLekcji, Lekcja
from nauczyciele import Nauczyciel
from infrastruktura import Sala, Grupa

logger = logging.getLogger(__name__)


class WalidatorPlanu:
    """Klasa odpowiedzialna za sprawdzanie wszystkich ograniczeń w planie lekcji."""

    @staticmethod
    def sprawdz_dostepnosc_sali(plany: List[PlanLekcji], sala: Sala, dzien: str, godzina: int) -> bool:
        """Sprawdza czy sala jest dostępna w danym terminie."""
        try:
            for plan in plany:
                if dzien in plan.lekcje and godzina in plan.lekcje[dzien]:
                    for lekcja in plan.lekcje[dzien][godzina]:
                        if lekcja.sala == sala:
                            return False
            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania dostępności sali: {e}")
            return False

    @staticmethod
    def sprawdz_dostepnosc_nauczyciela(
            plany: List[PlanLekcji],
            nauczyciel: Nauczyciel,
            dzien: str,
            godzina: int,
            przydzielone_godziny: Dict[int, int]
    ) -> bool:
        """Sprawdza czy nauczyciel jest dostępny w danym terminie."""
        try:
            if dzien not in nauczyciel.dostepne_dni:
                return False

            # Sprawdzanie liczby godzin w danym dniu
            godziny_dzisiaj = 0
            for plan in plany:
                if dzien in plan.lekcje:
                    for g, lekcje in plan.lekcje[dzien].items():
                        for lekcja in lekcje:
                            if lekcja.nauczyciel == nauczyciel:
                                godziny_dzisiaj += 1
                                if g == godzina:  # nauczyciel już ma lekcję w tym czasie
                                    return False

            # Sprawdzenie limitów
            if godziny_dzisiaj >= nauczyciel.maks_godzin_dziennie:
                return False

            godziny_tygodniowo = przydzielone_godziny.get(nauczyciel.id, 0)
            if godziny_tygodniowo >= 20:  # Limit tygodniowy
                return False

            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania dostępności nauczyciela: {e}")
            return False

    @staticmethod
    def sprawdz_przedmiot_pod_rzad(plan: PlanLekcji, przedmiot: str, dzien: str, godzina: int) -> bool:
        """Sprawdza czy nie ma za dużo lekcji tego samego przedmiotu pod rząd."""
        try:
            if przedmiot not in PRZEDMIOTY_POD_RZAD:
                return True

            count = 0
            # Sprawdzanie poprzedniej godziny
            if godzina > 0 and dzien in plan.lekcje and godzina - 1 in plan.lekcje[dzien]:
                for lekcja in plan.lekcje[dzien][godzina - 1]:
                    if lekcja.przedmiot == przedmiot:
                        count += 1

            # Sprawdzanie następnej godziny
            if godzina < len(GODZINY_LEKCJI) - 1 and dzien in plan.lekcje and godzina + 1 in plan.lekcje[dzien]:
                for lekcja in plan.lekcje[dzien][godzina + 1]:
                    if lekcja.przedmiot == przedmiot:
                        count += 1

            return count < 2  # Maksymalnie 2 godziny pod rząd
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania przedmiotów pod rząd: {e}")
            return False

    @staticmethod
    def sprawdz_okienka(plan: PlanLekcji, dzien: str, godzina: int) -> bool:
        """Sprawdza czy dodanie lekcji nie stworzy okienka."""
        godziny = WalidatorPlanu.policz_lekcje_w_dniu(plan, dzien)

        # Znajdź pierwszą i ostatnią lekcję w dniu
        lekcje = [g for g, count in godziny.items() if count > 0]
        if not lekcje:  # Jeśli nie ma jeszcze lekcji w tym dniu
            return True

        pierwsza = min(lekcje)
        ostatnia = max(lekcje)

        # Sprawdź czy nowa godzina nie tworzy okienka
        if godzina > pierwsza and godzina < ostatnia:
            for g in range(pierwsza, ostatnia + 1):
                if g != godzina and godziny[g] == 0:
                    return False

        return True

    @staticmethod
    def sprawdz_okienka_w_planie(plan: PlanLekcji) -> bool:
        """Sprawdza czy w całym planie nie ma zbyt dużych przerw między lekcjami."""
        try:
            for dzien in DNI_TYGODNIA:
                if dzien not in plan.lekcje:
                    continue

                godziny_z_lekcjami = sorted(plan.lekcje[dzien].keys())
                if not godziny_z_lekcjami:
                    continue

                # Sprawdź odstępy między lekcjami
                for i in range(len(godziny_z_lekcjami) - 1):
                    if godziny_z_lekcjami[i + 1] - godziny_z_lekcjami[i] > 2:
                        logger.warning(f"Zbyt duża przerwa w planie w dniu {dzien}")
                        return False

            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania okienek w planie: {e}")
            return False

    @staticmethod
    def sprawdz_duplikaty_lekcji(
            plan: PlanLekcji,
            dzien: str,
            godzina: int,
            przedmiot: str,
            nauczyciel: Nauczyciel,
            sala: Sala,
            grupy: List[Grupa]
    ) -> bool:
        """Sprawdza czy nie ma duplikatów lekcji w danym terminie."""
        if dzien not in plan.lekcje or godzina not in plan.lekcje[dzien]:
            return True

        for lekcja in plan.lekcje[dzien][godzina]:
            # Sprawdź czy któraś z grup nie ma już lekcji w tym czasie
            for grupa in grupy:
                if grupa in lekcja.grupy:
                    return False

            if lekcja.przedmiot == przedmiot:
                return False
            if lekcja.nauczyciel == nauczyciel:
                return False
            if lekcja.sala == sala:
                return False
        return True

    @staticmethod
    def czy_mozna_dodac_lekcje(plan: PlanLekcji, dzien: str, godzina: int, przedmiot: str) -> bool:
        """Sprawdza czy można dodać lekcję w danym terminie."""
        try:
            # Sprawdzenie czy to nie jest pierwsza/ostatnia lekcja dla przedmiotów z ograniczeniami
            if przedmiot in PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH:
                if godzina == 0 or godzina == len(GODZINY_LEKCJI) - 1:
                    return False

            # Sprawdzenie przedmiotów pod rząd
            if not WalidatorPlanu.sprawdz_przedmiot_pod_rzad(plan, przedmiot, dzien, godzina):
                return False

            godziny_w_dniu = sorted([g for g in plan.lekcje.get(dzien, {}).keys()])

            # Sprawdzenie dla przedmiotów, które mogą być tylko przed/po wszystkich innych lekcjach
            if przedmiot in PRZEDMIOTY_PIERWSZE_OSTATNIE:
                if not godziny_w_dniu:  # Jeśli nie ma innych lekcji
                    return True

                # Sprawdź czy lekcja jest przed pierwszą lub po ostatniej
                if godzina < min(godziny_w_dniu) - 1 or godzina > max(godziny_w_dniu) + 1:
                    return True

                return False

            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania możliwości dodania lekcji: {e}")
            return False

    @staticmethod
    def weryfikuj_plan(plan: PlanLekcji) -> bool:
        """Weryfikuje czy cały plan jest poprawny."""
        try:
            for dzien in DNI_TYGODNIA:
                if dzien not in plan.lekcje:
                    continue

                for godzina in plan.lekcje[dzien]:
                    # Sprawdź duplikaty sal i nauczycieli
                    uzyte_sale = set()
                    uzyte_nauczyciele = set()
                    uzyte_grupy = set()

                    for lekcja in plan.lekcje[dzien][godzina]:
                        # Sprawdź sale
                        if lekcja.sala in uzyte_sale:
                            logger.error(
                                f"Duplikat sali {lekcja.sala.nazwa} w dniu {dzien} o godzinie {GODZINY_LEKCJI[godzina][0]}")
                            return False
                        uzyte_sale.add(lekcja.sala)

                        # Sprawdź nauczycieli
                        if lekcja.nauczyciel in uzyte_nauczyciele:
                            logger.error(f"Duplikat nauczyciela {lekcja.nauczyciel.imie_nazwisko}")
                            return False
                        uzyte_nauczyciele.add(lekcja.nauczyciel)

                        # Sprawdź grupy
                        for grupa in lekcja.grupy:
                            if grupa in uzyte_grupy:
                                logger.error(f"Duplikat grupy {grupa.nazwa}")
                                return False
                            uzyte_grupy.add(grupa)

            return True
        except Exception as e:
            logger.error(f"Błąd podczas weryfikacji planu: {e}")
            return False

    @staticmethod
    def policz_lekcje_w_dniu(plan: PlanLekcji, dzien: str) -> Dict[int, int]:
        """Zlicza liczbę lekcji w każdej godzinie danego dnia."""
        godziny = {i: 0 for i in range(len(GODZINY_LEKCJI))}
        if dzien in plan.lekcje:
            for godzina, lekcje in plan.lekcje[dzien].items():
                godziny[godzina] = len(lekcje)
        return godziny