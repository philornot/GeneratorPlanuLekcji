import logging
from typing import List, Dict, Tuple, Optional

from stale import GODZINY_LEKCJI, DNI_TYGODNIA, PRZEDMIOTY_ROCZNIKI, PRZEDMIOTY_DZIELONE, TypSali
from modele import PlanLekcji, Lekcja, BrakDostepnegoTerminuError, BrakNauczycielaError
from walidacja import WalidatorPlanu
from infrastruktura import Sala
from nauczyciele import Nauczyciel

logger = logging.getLogger(__name__)


class PlanowaniePrzedmiotow:
    """Klasa odpowiedzialna za planowanie przedmiotów w planie lekcji."""

    def __init__(self, sale: Dict[TypSali, List[Sala]], nauczyciele: List[Nauczyciel]):
        self.sale = sale
        self.nauczyciele = nauczyciele
        self.walidator = WalidatorPlanu()
        self.przydzielone_godziny: Dict[int, int] = {}  # id_nauczyciela -> liczba_godzin

    def reset(self):
        """Resetuje stan planowania."""
        self.przydzielone_godziny.clear()

    def znajdz_wolny_termin(
            self,
            plany: List[PlanLekcji],
            plan: PlanLekcji,
            przedmiot: str,
            liczba_grup: int
    ) -> Optional[Tuple[str, int, Sala, Nauczyciel]]:
        """Znajduje wolny termin na lekcję, uwzględniając wszystkie ograniczenia."""
        try:
            mozliwe_terminy = []

            for dzien in DNI_TYGODNIA:
                # Policz aktualną liczbę lekcji w dniu
                aktualne_lekcje = sum(1 for g in plan.lekcje.get(dzien, {}).values() for _ in g)

                if aktualne_lekcje >= 8:  # Maksymalna liczba lekcji w dniu
                    logger.debug(f"Dzień {dzien} pominięty - za dużo lekcji ({aktualne_lekcje})")
                    continue

                # Sprawdź wszystkie możliwe godziny
                for godzina in range(len(GODZINY_LEKCJI)):
                    # Sprawdź podstawowe ograniczenia
                    if not self.walidator.czy_mozna_dodac_lekcje(plan, dzien, godzina, przedmiot):
                        continue

                    # Sprawdź czy nie powstanie okienko
                    if not self.walidator.sprawdz_okienka(plan, dzien, godzina):
                        continue

                    # Określ które grupy będą miały lekcję
                    grupy = []
                    if przedmiot in PRZEDMIOTY_DZIELONE:
                        grupy = [plan.klasa.grupa1]  # jedna grupa na raz
                    else:
                        grupy = [plan.klasa.grupa1, plan.klasa.grupa2]  # cała klasa

                    # Szukanie dostępnej sali
                    sale = self._znajdz_sale_dla_przedmiotu(przedmiot, liczba_grup)
                    for sala in sale:
                        if not self.walidator.sprawdz_dostepnosc_sali(plany, sala, dzien, godzina):
                            continue

                        # Szukanie dostępnego nauczyciela
                        nauczyciel = self._znajdz_nauczyciela(przedmiot, plany, dzien, godzina)
                        if not nauczyciel:
                            continue

                        # Sprawdź duplikaty
                        if not self.walidator.sprawdz_duplikaty_lekcji(
                                plan, dzien, godzina, przedmiot, nauczyciel, sala, grupy
                        ):
                            continue

                        # Oblicz priorytet dla tego terminu
                        priorytet = (
                            aktualne_lekcje,  # Preferuj dni z mniejszą liczbą lekcji
                            godzina,  # Preferuj wcześniejsze godziny
                            self.przydzielone_godziny.get(nauczyciel.id, 0)  # Preferuj mniej obciążonych nauczycieli
                        )
                        mozliwe_terminy.append((priorytet, (dzien, godzina, sala, nauczyciel)))

            if mozliwe_terminy:
                return min(mozliwe_terminy, key=lambda x: x[0])[1]

            logger.warning(f"Nie znaleziono wolnego terminu dla przedmiotu {przedmiot}")
            return None

        except Exception as e:
            logger.error(f"Błąd podczas szukania wolnego terminu: {e}", exc_info=True)
            return None

    def planuj_przedmiot(self, plany: List[PlanLekcji], plan: PlanLekcji, przedmiot: str) -> bool:
        """
        Planuje wszystkie godziny danego przedmiotu dla klasy.
        Zwraca True jeśli udało się zaplanować wszystkie godziny.
        """
        try:
            # Ile godzin musimy zaplanować
            godziny_do_przydzielenia = PRZEDMIOTY_ROCZNIKI[przedmiot][plan.klasa.rocznik - 1]

            for _ in range(godziny_do_przydzielenia):
                try:
                    # Szukamy terminu dla całej klasy
                    termin = self.znajdz_wolny_termin(plany, plan, przedmiot, 2)
                    if not termin:
                        logger.warning(f"Nie znaleziono terminu dla przedmiotu {przedmiot}")
                        return False

                    dzien, godzina, sala, nauczyciel = termin

                    # Dodajemy lekcję
                    lekcja = Lekcja(
                        przedmiot=przedmiot,
                        nauczyciel=nauczyciel,
                        sala=sala,
                        grupy=[plan.klasa.grupa1, plan.klasa.grupa2],
                        godzina=godzina,
                        dzien=dzien
                    )
                    plan.dodaj_lekcje(lekcja)
                    self._zwieksz_godziny_nauczyciela(nauczyciel)

                except (BrakDostepnegoTerminuError, BrakNauczycielaError) as e:
                    logger.error(f"Nie udało się zaplanować przedmiotu {przedmiot}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Błąd podczas planowania przedmiotu {przedmiot}: {e}")
            return False

    def planuj_przedmiot_dzielony(self, plany: List[PlanLekcji], plan: PlanLekcji, przedmiot: str) -> bool:
        """
        Planuje wszystkie godziny przedmiotu dzielonego na grupy.
        Zwraca True jeśli udało się zaplanować wszystkie godziny.
        """
        try:
            godziny_do_przydzielenia = PRZEDMIOTY_ROCZNIKI[przedmiot][plan.klasa.rocznik - 1]

            for _ in range(godziny_do_przydzielenia):
                try:
                    # Planujemy dla pierwszej grupy
                    termin1 = self.znajdz_wolny_termin(plany, plan, przedmiot, 1)
                    if not termin1:
                        logger.warning(f"Nie znaleziono terminu dla grupy 1 przedmiotu {przedmiot}")
                        return False

                    dzien1, godzina1, sala1, nauczyciel1 = termin1
                    lekcja1 = Lekcja(
                        przedmiot=przedmiot,
                        nauczyciel=nauczyciel1,
                        sala=sala1,
                        grupy=[plan.klasa.grupa1],
                        godzina=godzina1,
                        dzien=dzien1
                    )
                    plan.dodaj_lekcje(lekcja1)
                    self._zwieksz_godziny_nauczyciela(nauczyciel1)

                    # Planujemy dla drugiej grupy
                    termin2 = self.znajdz_wolny_termin(plany, plan, przedmiot, 1)
                    if not termin2:
                        logger.warning(f"Nie znaleziono terminu dla grupy 2 przedmiotu {przedmiot}")
                        return False

                    dzien2, godzina2, sala2, nauczyciel2 = termin2
                    lekcja2 = Lekcja(
                        przedmiot=przedmiot,
                        nauczyciel=nauczyciel2,
                        sala=sala2,
                        grupy=[plan.klasa.grupa2],
                        godzina=godzina2,
                        dzien=dzien2
                    )
                    plan.dodaj_lekcje(lekcja2)
                    self._zwieksz_godziny_nauczyciela(nauczyciel2)

                except (BrakDostepnegoTerminuError, BrakNauczycielaError) as e:
                    logger.error(f"Nie udało się zaplanować przedmiotu dzielonego {przedmiot}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Błąd podczas planowania przedmiotu dzielonego {przedmiot}: {e}")
            return False

    def planuj_religie(self, plany: List[PlanLekcji], plan: PlanLekcji) -> bool:
        """
        Planuje godziny religii, które muszą być na początku lub końcu dnia.
        """
        try:
            godziny_do_przydzielenia = PRZEDMIOTY_ROCZNIKI['religia'][plan.klasa.rocznik - 1]
            przydzielone = 0

            for dzien in DNI_TYGODNIA:
                if przydzielone >= godziny_do_przydzielenia:
                    break

                # Znajdź godziny zajęć w tym dniu (jeśli są)
                godziny_zajec = []
                if dzien in plan.lekcje:
                    godziny_zajec = sorted(plan.lekcje[dzien].keys())

                # Określ możliwe godziny dla religii
                mozliwe_godziny = []
                if not godziny_zajec:
                    # Jeśli nie ma jeszcze zajęć, możemy użyć dowolnej godziny
                    mozliwe_godziny = [0, len(GODZINY_LEKCJI) - 1]
                else:
                    # Godzina przed pierwszą lekcją
                    if godziny_zajec[0] > 0:
                        mozliwe_godziny.append(godziny_zajec[0] - 1)
                    # Godzina po ostatniej lekcji
                    if godziny_zajec[-1] < len(GODZINY_LEKCJI) - 1:
                        mozliwe_godziny.append(godziny_zajec[-1] + 1)

                for godzina in mozliwe_godziny:
                    try:
                        # Szukamy sali i nauczyciela
                        sale = self._znajdz_sale_dla_przedmiotu('religia', 2)
                        if not sale:
                            continue

                        for sala in sale:
                            if not self.walidator.sprawdz_dostepnosc_sali(plany, sala, dzien, godzina):
                                continue

                            nauczyciel = self._znajdz_nauczyciela('religia', plany, dzien, godzina)
                            if not nauczyciel:
                                continue

                            # Sprawdzamy czy grupy nie mają już lekcji
                            if not self.walidator.sprawdz_duplikaty_lekcji(
                                    plan, dzien, godzina, 'religia', nauczyciel, sala,
                                    [plan.klasa.grupa1, plan.klasa.grupa2]
                            ):
                                continue

                            # Wszystko OK - dodajemy lekcję
                            lekcja = Lekcja(
                                przedmiot='religia',
                                nauczyciel=nauczyciel,
                                sala=sala,
                                grupy=[plan.klasa.grupa1, plan.klasa.grupa2],
                                godzina=godzina,
                                dzien=dzien
                            )
                            plan.dodaj_lekcje(lekcja)
                            self._zwieksz_godziny_nauczyciela(nauczyciel)
                            przydzielone += 1
                            logger.info(f"Zaplanowano lekcję religii: {dzien} {GODZINY_LEKCJI[godzina][0]}")
                            break

                    except Exception as e:
                        logger.error(f"Błąd podczas planowania religii: {e}")
                        continue

            return przydzielone >= godziny_do_przydzielenia

        except Exception as e:
            logger.error(f"Błąd podczas planowania religii: {e}")
            return False

    def _znajdz_sale_dla_przedmiotu(self, przedmiot: str, liczba_grup: int) -> List[Sala]:
        """Znajduje wszystkie sale odpowiednie dla danego przedmiotu i liczby grup."""
        try:
            odpowiednie_sale = []
            if przedmiot == 'WF':
                # Dla WF używamy tylko sal gimnastycznych
                for typ_sal in [TypSali.SILOWNIA, TypSali.MALA_SALA_GIM, TypSali.DUZA_HALA]:
                    for sala in self.sale[typ_sal]:
                        if sala.pojemnosc_grup >= liczba_grup:
                            odpowiednie_sale.append(sala)
            else:
                for typ_sal, sale in self.sale.items():
                    # Dla pozostałych przedmiotów nie używamy sal WF
                    if typ_sal not in [TypSali.SILOWNIA, TypSali.MALA_SALA_GIM, TypSali.DUZA_HALA]:
                        for sala in sale:
                            if (sala.dozwolone_przedmioty is None
                                or przedmiot in sala.dozwolone_przedmioty) \
                                    and sala.pojemnosc_grup >= liczba_grup:
                                odpowiednie_sale.append(sala)
            return odpowiednie_sale

        except Exception as e:
            logger.error(f"Błąd podczas szukania sal dla przedmiotu: {e}")
            return []

    def _znajdz_nauczyciela(
            self,
            przedmiot: str,
            plany: List[PlanLekcji],
            dzien: str,
            godzina: int
    ) -> Optional[Nauczyciel]:
        """Znajduje dostępnego nauczyciela dla przedmiotu w danym terminie."""
        try:
            # Znajdź wszystkich nauczycieli uczących tego przedmiotu
            potencjalni = [n for n in self.nauczyciele if przedmiot in n.przedmioty]
            if not potencjalni:
                logger.error(f"Brak nauczycieli dla przedmiotu {przedmiot}")
                return None

            najlepszy_wynik = -1
            najlepszy_nauczyciel = None

            for nauczyciel in potencjalni:
                # Sprawdź dostępność
                if not self.walidator.sprawdz_dostepnosc_nauczyciela(
                        plany, nauczyciel, dzien, godzina, self.przydzielone_godziny
                ):
                    continue

                # System oceny nauczyciela (0-1, gdzie 1 to najlepszy wybór)
                wynik = self._ocen_nauczyciela(nauczyciel, przedmiot)

                if wynik > najlepszy_wynik:
                    najlepszy_wynik = wynik
                    najlepszy_nauczyciel = nauczyciel

            return najlepszy_nauczyciel

        except Exception as e:
            logger.error(f"Błąd podczas szukania nauczyciela: {e}")
            return None

    def _ocen_nauczyciela(self, nauczyciel: Nauczyciel, przedmiot: str) -> float:
        """Ocenia jak dobrym wyborem jest dany nauczyciel (0-1)."""
        try:
            # Podstawowe kryteria
            scoring = {
                'specjalizacja': 1.0 if przedmiot == nauczyciel.przedmioty[0] else 0.5,
                'dostepnosc': len(nauczyciel.dostepne_dni) / 5,
                'obciazenie': 1.0 - (self.przydzielone_godziny.get(nauczyciel.id, 0) / 20)
            }

            # Wagi kryteriów
            wagi = {
                'specjalizacja': 0.4,
                'dostepnosc': 0.3,
                'obciazenie': 0.3
            }

            return sum(scoring[k] * wagi[k] for k in scoring)

        except Exception as e:
            logger.error(f"Błąd podczas oceny nauczyciela: {e}")
            return 0.0

    def _zwieksz_godziny_nauczyciela(self, nauczyciel: Nauczyciel):
        """Zwiększa licznik przydzielonych godzin dla nauczyciela."""
        if nauczyciel.id not in self.przydzielone_godziny:
            self.przydzielone_godziny[nauczyciel.id] = 0
        self.przydzielone_godziny[nauczyciel.id] += 1