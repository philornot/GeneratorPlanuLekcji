import logging
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from infrastruktura import Sala, Klasa, Grupa, generuj_sale, generuj_klasy
from nauczyciele import Nauczyciel, generuj_nauczycieli
from stale import (
    GODZINY_LEKCJI, DNI_TYGODNIA, PRZEDMIOTY_DZIELONE,
    PRZEDMIOTY_PIERWSZE_OSTATNIE, PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH,
    PRZEDMIOTY_POD_RAD, PRZEDMIOTY_ROCZNIKI, TypSali, GODZINY_W_TYGODNIU
)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='generator_planu.log'
)
logger = logging.getLogger(__name__)


class BrakDostepnegoTerminuError(Exception):
    """Wyjątek rzucany gdy nie można znaleźć terminu dla lekcji."""
    pass


class BrakNauczycielaError(Exception):
    """Wyjątek rzucany gdy nie można znaleźć nauczyciela dla przedmiotu."""
    pass


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
        """Bezpieczne dodawanie lekcji do planu."""
        if lekcja.dzien not in self.lekcje:
            self.lekcje[lekcja.dzien] = {}
        if lekcja.godzina not in self.lekcje[lekcja.dzien]:
            self.lekcje[lekcja.dzien][lekcja.godzina] = []
        self.lekcje[lekcja.dzien][lekcja.godzina].append(lekcja)


class GeneratorPlanu:
    def __init__(self):
        try:
            self.sale = generuj_sale()
            self.klasy = generuj_klasy()
            self.nauczyciele = generuj_nauczycieli()
            self.przydzielone_godziny: Dict[int, int] = {}  # id_nauczyciela -> liczba_godzin
            self.plany: List[PlanLekcji] = []
            logger.info("Zainicjalizowano generator planu")
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji generatora: {e}")
            raise

    def sprawdz_dostepnosc_sali(self, sala: Sala, dzien: str, godzina: int) -> bool:
        """Sprawdza czy sala jest dostępna w danym terminie."""
        try:
            for plan in self.plany:
                if dzien in plan.lekcje and godzina in plan.lekcje[dzien]:
                    for lekcja in plan.lekcje[dzien][godzina]:
                        if lekcja.sala == sala:
                            return False
            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania dostępności sali: {e}")
            return False

    def sprawdz_dostepnosc_nauczyciela(self, nauczyciel: Nauczyciel, dzien: str, godzina: int) -> bool:
        """Sprawdza czy nauczyciel jest dostępny w danym terminie."""
        try:
            if dzien not in nauczyciel.dostepne_dni:
                return False

            # Sprawdzanie liczby godzin w danym dniu
            godziny_dzisiaj = 0
            for plan in self.plany:
                if dzien in plan.lekcje:
                    for g, lekcje in plan.lekcje[dzien].items():
                        for lekcja in lekcje:
                            if lekcja.nauczyciel == nauczyciel:
                                godziny_dzisiaj += 1
                                if g == godzina:  # nauczyciel już ma lekcję w tym czasie
                                    return False

            return godziny_dzisiaj < nauczyciel.maks_godzin_dziennie
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania dostępności nauczyciela: {e}")
            return False

    def reset_przydzielone_godziny(self):
        """Resetuje licznik przydzielonych godzin dla wszystkich nauczycieli."""
        self.przydzielone_godziny = {}

    def sprawdz_przedmiot_pod_rzad(self, plan: PlanLekcji, przedmiot: str, dzien: str, godzina: int) -> bool:
        """Sprawdza czy nie ma za dużo lekcji tego samego przedmiotu pod rząd."""
        try:
            if przedmiot not in PRZEDMIOTY_POD_RAD:
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

            return count < 2
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania przedmiotów pod rząd: {e}")
            return False

    def znajdz_optymalna_godzine(self, plan: PlanLekcji, dzien: str) -> int:
        """Znajduje godzinę z najmniejszą liczbą lekcji, preferując środek dnia."""
        godziny = self.policz_lekcje_w_dniu(plan, dzien)

        # Wagi dla godzin - preferujemy środek dnia
        wagi = {
            0: 1.5,  # Pierwsza lekcja (mniej preferowana)
            1: 1.2,
            2: 1.0,
            3: 1.0,
            4: 1.0,
            5: 1.0,
            6: 1.2,
            7: 1.3,
            8: 1.5,  # Ostatnia lekcja (mniej preferowana)
        }

        # Oblicz ważone wartości dla każdej godziny
        wazone_godziny = {
            godzina: (ilosc * wagi[godzina], godzina)
            for godzina, ilosc in godziny.items()
        }

        # Zwróć godzinę z najmniejszą ważoną wartością
        return min(wazone_godziny.values(), key=lambda x: x[0])[1]

    def sprawdz_okienka_w_planie(self, plan: PlanLekcji) -> bool:
        """Sprawdza czy w planie nie ma zbyt dużych przerw między lekcjami."""
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
            logger.error(f"Błąd podczas sprawdzania okienek: {e}")
            return False

    def sprawdz_okienka(self, plan: PlanLekcji, dzien: str, godzina: int) -> bool:
        """Sprawdza czy dodanie lekcji nie stworzy okienka."""
        godziny = self.policz_lekcje_w_dniu(plan, dzien)

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

    def zwieksz_godziny_nauczyciela(self, nauczyciel: Nauczyciel):
        """Zwiększa licznik przydzielonych godzin dla nauczyciela."""
        if nauczyciel.id not in self.przydzielone_godziny:
            self.przydzielone_godziny[nauczyciel.id] = 0
        self.przydzielone_godziny[nauczyciel.id] += 1

    def pobierz_godziny_nauczyciela(self, nauczyciel: Nauczyciel) -> int:
        """Zwraca liczbę przydzielonych godzin dla nauczyciela."""
        return self.przydzielone_godziny.get(nauczyciel.id, 0)

    def znajdz_sale_dla_przedmiotu(self, przedmiot: str, liczba_grup: int) -> List[Sala]:
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
                            if (sala.dozwolone_przedmioty is None or przedmiot in sala.dozwolone_przedmioty) and \
                                    sala.pojemnosc_grup >= liczba_grup:
                                odpowiednie_sale.append(sala)
            return odpowiednie_sale
        except Exception as e:
            logger.error(f"Błąd podczas szukania sal dla przedmiotu: {e}")
            return []

    def weryfikuj_plan(self, plan: PlanLekcji) -> bool:
        """Weryfikuje czy plan jest poprawny pod względem sal i nauczycieli."""
        try:
            for dzien in DNI_TYGODNIA:
                if dzien not in plan.lekcje:
                    continue

                for godzina in plan.lekcje[dzien]:
                    # Sprawdź duplikaty sal
                    uzyte_sale = set()
                    for lekcja in plan.lekcje[dzien][godzina]:
                        if lekcja.sala in uzyte_sale:
                            logger.error(
                                f"Duplikat sali {lekcja.sala.nazwa} w dniu {dzien} o godzinie {GODZINY_LEKCJI[godzina][0]}")
                            return False
                        uzyte_sale.add(lekcja.sala)

                        # Sprawdź czy sala jest odpowiednia dla przedmiotu
                        if lekcja.przedmiot == 'WF' and lekcja.sala.typ not in [TypSali.SILOWNIA, TypSali.MALA_SALA_GIM,
                                                                                TypSali.DUZA_HALA]:
                            logger.error(f"WF w nieodpowiedniej sali {lekcja.sala.nazwa}")
                            return False

                        # Sprawdź duplikaty nauczycieli
                        uzyte_nauczyciele = set()
                        for lekcja in plan.lekcje[dzien][godzina]:
                            if lekcja.nauczyciel in uzyte_nauczyciele:
                                logger.error(f"Duplikat nauczyciela {lekcja.nauczyciel.imie_nazwisko}")
                                return False
                            uzyte_nauczyciele.add(lekcja.nauczyciel)

            return True
        except Exception as e:
            logger.error(f"Błąd podczas weryfikacji planu: {e}")
            return False

    def znajdz_nauczyciela_dla_przedmiotu(self, przedmiot: str, dzien: str, godzina: int) -> Optional[Nauczyciel]:
        """Znajduje dostępnego nauczyciela dla danego przedmiotu."""
        try:
            # Zbierz wszystkich nauczycieli uczących danego przedmiotu
            potencjalni_nauczyciele = [n for n in self.nauczyciele if przedmiot in n.przedmioty]

            # Lista dostępnych nauczycieli (po sprawdzeniu wszystkich warunków)
            dostepni_nauczyciele = []

            for nauczyciel in potencjalni_nauczyciele:
                # Sprawdź podstawową dostępność (dni pracy)
                if not self.sprawdz_dostepnosc_nauczyciela(nauczyciel, dzien, godzina):
                    continue

                # Sprawdź czy nauczyciel nie jest już zajęty w tym czasie w innych planach
                zajety = False
                for plan in self.plany:
                    if (dzien in plan.lekcje and
                            godzina in plan.lekcje[dzien]):
                        for lekcja in plan.lekcje[dzien][godzina]:
                            if lekcja.nauczyciel == nauczyciel:
                                zajety = True
                                break
                    if zajety:
                        break

                if not zajety:
                    # Sprawdź liczbę godzin w danym dniu
                    godziny_dzisiaj = 0
                    for plan in self.plany:
                        if dzien in plan.lekcje:
                            for g, lekcje in plan.lekcje[dzien].items():
                                for lekcja in lekcje:
                                    if lekcja.nauczyciel == nauczyciel:
                                        godziny_dzisiaj += 1

                    if godziny_dzisiaj < nauczyciel.maks_godzin_dziennie:
                        # Sprawdź całkowite obciążenie nauczyciela
                        if self.pobierz_godziny_nauczyciela(nauczyciel) < 20:  # limit tygodniowy
                            dostepni_nauczyciele.append(nauczyciel)

            # Wybierz nauczyciela z najmniejszą liczbą przydzielonych godzin
            if dostepni_nauczyciele:
                return min(dostepni_nauczyciele,
                           key=lambda n: (self.pobierz_godziny_nauczyciela(n),
                                          len([l for p in self.plany
                                               for d in p.lekcje.values()
                                               for g in d.values()
                                               for l in g
                                               if l.nauczyciel == n])))
            return None

        except Exception as e:
            logger.error(f"Błąd podczas szukania nauczyciela: {e}")
            return None

    def policz_pozostale_godziny(self, plan: PlanLekcji, przedmiot: str) -> int:
        """Oblicza ile godzin danego przedmiotu zostało do przydzielenia."""
        try:
            godziny_tygodniowo = PRZEDMIOTY_ROCZNIKI[przedmiot][plan.klasa.rocznik - 1]
            przydzielone = 0

            for dzien in DNI_TYGODNIA:
                if dzien not in plan.lekcje:
                    continue
                for godzina in plan.lekcje[dzien]:
                    for lekcja in plan.lekcje[dzien][godzina]:
                        if lekcja.przedmiot == przedmiot:
                            przydzielone += 1

            return godziny_tygodniowo - przydzielone
        except Exception as e:
            logger.error(f"Błąd podczas liczenia pozostałych godzin: {e}")
            return 0

    def czy_mozna_dodac_lekcje(self, plan: PlanLekcji, dzien: str, godzina: int, przedmiot: str) -> bool:
        """Sprawdza czy można dodać lekcję w danym terminie."""
        try:
            # Sprawdzenie czy to nie jest pierwsza/ostatnia lekcja dla przedmiotów z ograniczeniami
            if przedmiot in PRZEDMIOTY_BEZ_PIERWSZYCH_OSTATNICH:
                if godzina == 0 or godzina == len(GODZINY_LEKCJI) - 1:
                    return False

            # Sprawdzenie dla przedmiotów, które mogą być tylko na początku/końcu
            if przedmiot in PRZEDMIOTY_PIERWSZE_OSTATNIE:
                if godzina != 0 and godzina != len(GODZINY_LEKCJI) - 1:
                    return False

            # Sprawdzenie przedmiotów pod rząd
            if not self.sprawdz_przedmiot_pod_rzad(plan, przedmiot, dzien, godzina):
                return False

            return True
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania możliwości dodania lekcji: {e}")
            return False

    def zapisz_plan_do_pliku(self, plan: PlanLekcji, sciezka: str = "plany_lekcji") -> None:
        """Zapisuje plan lekcji do pliku."""
        try:
            # Upewnij się, że katalog istnieje
            if not os.path.exists(sciezka):
                os.makedirs(sciezka)

            nazwa_planu = f"{sciezka}/plan_{plan.klasa.rocznik}{plan.klasa.litera}.txt"
            with open(nazwa_planu, 'w', encoding='utf-8') as f:
                f.write(f"Plan lekcji dla klasy {plan.klasa.rocznik}{plan.klasa.litera}\n")
                f.write("-" * 100 + "\n")

                for dzien in DNI_TYGODNIA:
                    f.write(f"\n{dzien}:\n")
                    for i, (start, koniec) in enumerate(GODZINY_LEKCJI):
                        linia = f"{start}-{koniec}: "
                        if dzien in plan.lekcje and i in plan.lekcje[dzien]:
                            lekcje = []
                            for lekcja in plan.lekcje[dzien][i]:
                                grupy_str = ", ".join(g.nazwa for g in lekcja.grupy)
                                lekcje.append(
                                    f"{lekcja.przedmiot} ({grupy_str}) - {lekcja.nauczyciel.imie_nazwisko} - {lekcja.sala.nazwa}"
                                )
                            linia += " | ".join(lekcje)
                        f.write(linia + "\n")
            logger.info(f"Zapisano plan dla klasy {plan.klasa.rocznik}{plan.klasa.litera} do pliku {nazwa_planu}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania planu do pliku: {e}")

    def sprawdz_duplikaty_lekcji(self, plan: PlanLekcji, dzien: str, godzina: int, przedmiot: str,
                                 nauczyciel: Nauczyciel, sala: Sala) -> bool:
        """Sprawdza czy nie ma duplikatów lekcji w danym terminie."""
        if dzien not in plan.lekcje or godzina not in plan.lekcje[dzien]:
            return True

        for lekcja in plan.lekcje[dzien][godzina]:
            # Sprawdź czy ten sam przedmiot nie jest już w tym czasie
            if lekcja.przedmiot == przedmiot:
                return False
            # Sprawdź czy nauczyciel nie ma już lekcji
            if lekcja.nauczyciel == nauczyciel:
                return False
            # Sprawdź czy sala nie jest już zajęta
            if lekcja.sala == sala:
                return False
        return True

    def znajdz_wolny_termin(self, plan: PlanLekcji, przedmiot: str, liczba_grup: int) -> Optional[
        Tuple[str, int, Sala, Nauczyciel]]:
        """Znajduje wolny termin na lekcję."""
        try:
            # Zbierz wszystkie możliwe terminy
            mozliwe_terminy = []
            for dzien in DNI_TYGODNIA:
                # Policz aktualną liczbę lekcji w dniu
                aktualne_lekcje = sum(1 for g in plan.lekcje.get(dzien, {}).values() for _ in g)

                # Preferuj dni z mniejszą liczbą lekcji
                if aktualne_lekcje >= 8:  # Maksymalna liczba lekcji w dniu
                    continue

                # Znajdź optymalną godzinę w tym dniu
                opt_godzina = self.znajdz_optymalna_godzine(plan, dzien)

                # Sprawdź wszystkie godziny, zaczynając od optymalnej
                for offset in range(len(GODZINY_LEKCJI)):
                    godzina = (opt_godzina + offset) % len(GODZINY_LEKCJI)

                    if not self.czy_mozna_dodac_lekcje(plan, dzien, godzina, przedmiot):
                        continue

                    if not self.sprawdz_okienka(plan, dzien, godzina):
                        continue

                    # Szukanie dostępnej sali
                    sale = self.znajdz_sale_dla_przedmiotu(przedmiot, liczba_grup)
                    for sala in sale:
                        if not self.sprawdz_dostepnosc_sali(sala, dzien, godzina):
                            continue

                        # Szukanie dostępnego nauczyciela
                        nauczyciel = self.znajdz_nauczyciela_dla_przedmiotu(przedmiot, dzien, godzina)
                        if nauczyciel and self.sprawdz_duplikaty_lekcji(plan, dzien, godzina, przedmiot, nauczyciel,
                                                                        sala):
                            # Oblicz priorytet dla tego terminu
                            priorytet = (
                                aktualne_lekcje,  # Preferuj dni z mniejszą liczbą lekcji
                                abs(godzina - opt_godzina),  # Preferuj godziny bliżej optymalnej
                                nauczyciel.przydzielone_godziny  # Preferuj nauczycieli z mniejszą liczbą godzin
                            )
                            mozliwe_terminy.append((priorytet, (dzien, godzina, sala, nauczyciel)))

            if mozliwe_terminy:
                # Wybierz termin z najlepszym priorytetem
                return min(mozliwe_terminy, key=lambda x: x[0])[1]

            return None

        except Exception as e:
            logger.error(f"Błąd podczas szukania wolnego terminu: {e}")
            return None

    def generuj_plan_dla_klasy(self, klasa: Klasa) -> Optional[PlanLekcji]:
        try:
            plan = PlanLekcji(klasa=klasa, lekcje={dzien: {} for dzien in DNI_TYGODNIA})
            logger.info(f"Rozpoczęto generowanie planu dla klasy {klasa.rocznik}{klasa.litera}")

            # Najpierw zaplanuj religię
            if not self.planuj_religie(plan):
                logger.error(f"Nie udało się zaplanować religii dla klasy {klasa.rocznik}{klasa.litera}")
                return None

            # Następnie przydzielamy przedmioty dzielone na grupy
            for przedmiot in PRZEDMIOTY_DZIELONE:
                godziny_do_przydzielenia = PRZEDMIOTY_ROCZNIKI[przedmiot][klasa.rocznik - 1]

                for _ in range(godziny_do_przydzielenia):
                    try:
                        # Szukamy terminu dla obu grup
                        termin = self.znajdz_wolny_termin(plan, przedmiot, 1)  # 1 grupa na raz
                        if not termin:
                            logger.warning(
                                f"Nie znaleziono terminu dla przedmiotu {przedmiot} w klasie {klasa.rocznik}{klasa.litera}")
                            continue

                        dzien, godzina, sala, nauczyciel = termin

                        # Dodajemy lekcję dla pierwszej grupy
                        lekcja_grupa1 = Lekcja(
                            przedmiot=przedmiot,
                            nauczyciel=nauczyciel,
                            sala=sala,
                            grupy=[klasa.grupa1],
                            godzina=godzina,
                            dzien=dzien
                        )
                        plan.dodaj_lekcje(lekcja_grupa1)
                        self.zwieksz_godziny_nauczyciela(nauczyciel)

                        # Szukamy sali i nauczyciela dla drugiej grupy
                        termin2 = self.znajdz_wolny_termin(plan, przedmiot, 1)
                        if termin2:
                            dzien2, godzina2, sala2, nauczyciel2 = termin2

                            # Dodajemy lekcję dla drugiej grupy
                            lekcja_grupa2 = Lekcja(
                                przedmiot=przedmiot,
                                nauczyciel=nauczyciel2,
                                sala=sala2,
                                grupy=[klasa.grupa2],
                                godzina=godzina2,
                                dzien=dzien2
                            )
                            plan.dodaj_lekcje(lekcja_grupa2)
                            self.zwieksz_godziny_nauczyciela(nauczyciel)
                        else:
                            logger.warning(
                                f"Nie znaleziono terminu dla drugiej grupy przedmiotu {przedmiot} w klasie {klasa.rocznik}{klasa.litera}")
                    except Exception as e:
                        logger.error(f"Błąd podczas przydzielania przedmiotu dzielonego {przedmiot}: {e}")
                        continue

            # Następnie przydzielamy pozostałe przedmioty
            for przedmiot, godziny in PRZEDMIOTY_ROCZNIKI.items():
                if przedmiot in PRZEDMIOTY_DZIELONE or przedmiot == 'religia':
                    continue

                godziny_do_przydzielenia = godziny[klasa.rocznik - 1]
                for _ in range(godziny_do_przydzielenia):
                    try:
                        termin = self.znajdz_wolny_termin(plan, przedmiot, 2)  # cała klasa
                        if not termin:
                            logger.warning(
                                f"Nie znaleziono terminu dla przedmiotu {przedmiot} w klasie {klasa.rocznik}{klasa.litera}")
                            continue

                        dzien, godzina, sala, nauczyciel = termin

                        lekcja = Lekcja(
                            przedmiot=przedmiot,
                            nauczyciel=nauczyciel,
                            sala=sala,
                            grupy=[klasa.grupa1, klasa.grupa2],  # cała klasa
                            godzina=godzina,
                            dzien=dzien
                        )
                        plan.dodaj_lekcje(lekcja)
                        self.zwieksz_godziny_nauczyciela(nauczyciel)
                    except Exception as e:
                        logger.error(f"Błąd podczas przydzielania przedmiotu {przedmiot}: {e}")
                        continue

            logger.info(f"Zakończono generowanie planu dla klasy {klasa.rocznik}{klasa.litera}")
            # Weryfikacja planu przed zwróceniem
            if not self.weryfikuj_plan(plan):
                logger.error(f"Wygenerowany plan nie przeszedł weryfikacji dla klasy {klasa.rocznik}{klasa.litera}")
                return None

            if not self.sprawdz_okienka_w_planie(plan):
                logger.warning(f"Plan dla klasy {klasa.rocznik}{klasa.litera} zawiera duże przerwy między lekcjami")

            return plan

        except Exception as e:
            logger.error(f"Błąd podczas generowania planu: {e}")
            return None

    def generuj_wszystkie_plany(self) -> List[PlanLekcji]:
        """Generuje plany lekcji dla wszystkich klas z lepszą kontrolą błędów i postępu."""
        try:
            logger.info("Rozpoczęto generowanie planów dla wszystkich klas")
            self.plany = []
            self.reset_przydzielone_godziny()
            nieudane_klasy = []

            # Sortuj klasy według liczby godzin (najpierw trudniejsze przypadki)
            posortowane_klasy = sorted(
                self.klasy,
                key=lambda k: GODZINY_W_TYGODNIU[k.rocznik],
                reverse=True
            )

            max_proby_globalne = 3  # Maksymalna liczba całkowitych restartów
            proba_globalna = 1

            print(f"\nGenerowanie planów (próba {proba_globalna}/{max_proby_globalne}):")
            print("=" * 50)

            while proba_globalna <= max_proby_globalne:
                total_klasy = len(posortowane_klasy)
                problematyczni_nauczyciele = set()  # Zbiór problematycznych nauczycieli

                for idx, klasa in enumerate(posortowane_klasy, 1):
                    print(f"\rKlasa {klasa.rocznik}{klasa.litera} ({idx}/{total_klasy}) ", end="")

                    # Dodaj informację o próbie globalnej
                    if proba_globalna > 1:
                        print(f"[Restart {proba_globalna}/{max_proby_globalne}] ", end="")

                    start_time = time.time()
                    plan = self.generuj_plan_dla_klasy(klasa)
                    czas_generowania = time.time() - start_time

                    if plan is not None:
                        self.plany.append(plan)
                        print(f"✓ ({czas_generowania:.1f}s)")
                    else:
                        nieudane_klasy.append(f"{klasa.rocznik}{klasa.litera}")
                        print(f"✗ ({czas_generowania:.1f}s)")

                        # Sprawdź logi, aby znaleźć problematycznego nauczyciela
                        with open('generator_planu.log', 'r') as f:
                            ostatnie_linie = f.readlines()[-5:]  # Sprawdź ostatnie 5 linii
                            for linia in ostatnie_linie:
                                if "Duplikat nauczyciela" in linia:
                                    nauczyciel = linia.split("Duplikat nauczyciela")[-1].strip()
                                    problematyczni_nauczyciele.add(nauczyciel)

                if len(nieudane_klasy) == 0:
                    break  # Sukces - wszystkie plany wygenerowane

                # Pokaż statystyki przed kolejną próbą
                print("\nStatystyki tej próby:")
                print(f"- Wygenerowano {len(self.plany)}/{total_klasy} planów")
                if problematyczni_nauczyciele:
                    print("- Problematyczni nauczyciele:")
                    for n in problematyczni_nauczyciele:
                        print(f"  * {n}")

                if proba_globalna < max_proby_globalne:
                    print(f"\nRozpoczynam próbę {proba_globalna + 1}/{max_proby_globalne}...")
                    self.plany = []
                    self.reset_przydzielone_godziny()
                    nieudane_klasy = []
                    proba_globalna += 1
                    print("=" * 50)
                else:
                    break

            print("\nPodsumowanie końcowe:")
            print(f"- Wykonano {proba_globalna} prób globalnych")
            print(f"- Wygenerowano {len(self.plany)}/{len(self.klasy)} planów")
            if len(self.plany) < len(self.klasy):
                print("- Nie udało się wygenerować planów dla klas:")
                print(f"  {', '.join(sorted(set(nieudane_klasy)))}")
                if problematyczni_nauczyciele:
                    print("- Nauczyciele powodujący najwięcej problemów:")
                    for n in problematyczni_nauczyciele:
                        print(f"  * {n}")

            return self.plany

        except Exception as e:
            logger.error(f"Błąd podczas generowania wszystkich planów: {e}")
            print(f"\nWystąpił błąd: {e}")
            return []

    def wizualizuj_plan(self, plan: PlanLekcji) -> None:
        """Wyświetla plan lekcji dla danej klasy."""
        try:
            print(f"\nPlan lekcji dla klasy {plan.klasa.rocznik}{plan.klasa.litera}")
            print("-" * 100)

            for dzien in DNI_TYGODNIA:
                print(f"\n{dzien}:")
                for i, (start, koniec) in enumerate(GODZINY_LEKCJI):
                    print(f"{start}-{koniec}: ", end="")
                    if dzien in plan.lekcje and i in plan.lekcje[dzien]:
                        for lekcja in plan.lekcje[dzien][i]:
                            grupy_str = ", ".join(g.nazwa for g in lekcja.grupy)
                            print(
                                f"{lekcja.przedmiot} ({grupy_str}) - {lekcja.nauczyciel.imie_nazwisko} - {lekcja.sala.nazwa}",
                                end=" | ")
                    print()
        except Exception as e:
            logger.error(f"Błąd podczas wizualizacji planu: {e}")
            print("Wystąpił błąd podczas wyświetlania planu.")

    def policz_lekcje_w_dniu(self, plan: PlanLekcji, dzien: str) -> Dict[int, int]:
        """Zlicza liczbę lekcji w każdej godzinie danego dnia."""
        godziny = {i: 0 for i in range(len(GODZINY_LEKCJI))}
        if dzien in plan.lekcje:
            for godzina, lekcje in plan.lekcje[dzien].items():
                godziny[godzina] = len(lekcje)
        return godziny

    def planuj_religie(self, plan: PlanLekcji) -> bool:
        """Specjalna funkcja do planowania religii."""
        try:
            godziny_do_przydzielenia = PRZEDMIOTY_ROCZNIKI['religia'][plan.klasa.rocznik - 1]

            # Próbuj najpierw ostatnie godziny
            for dzien in DNI_TYGODNIA:
                if dzien not in plan.lekcje:
                    plan.lekcje[dzien] = {}

                # Spróbuj ostatnią godzinę
                godzina = len(GODZINY_LEKCJI) - 1
                sale = self.znajdz_sale_dla_przedmiotu('religia', 2)
                for sala in sale:
                    if self.sprawdz_dostepnosc_sali(sala, dzien, godzina):
                        nauczyciel = self.znajdz_nauczyciela_dla_przedmiotu('religia', dzien, godzina)
                        if nauczyciel:
                            lekcja = Lekcja(
                                przedmiot='religia',
                                nauczyciel=nauczyciel,
                                sala=sala,
                                grupy=[plan.klasa.grupa1, plan.klasa.grupa2],
                                godzina=godzina,
                                dzien=dzien
                            )
                            plan.dodaj_lekcje(lekcja)
                            self.zwieksz_godziny_nauczyciela(nauczyciel)  # <- ZMIANA TUTAJ
                            godziny_do_przydzielenia -= 1
                            if godziny_do_przydzielenia == 0:
                                return True

            # Jeśli nie udało się na końcu, spróbuj na początku dnia
            for dzien in DNI_TYGODNIA:
                godzina = 0
                sale = self.znajdz_sale_dla_przedmiotu('religia', 2)
                for sala in sale:
                    if self.sprawdz_dostepnosc_sali(sala, dzien, godzina):
                        nauczyciel = self.znajdz_nauczyciela_dla_przedmiotu('religia', dzien, godzina)
                        if nauczyciel:
                            lekcja = Lekcja(
                                przedmiot='religia',
                                nauczyciel=nauczyciel,
                                sala=sala,
                                grupy=[plan.klasa.grupa1, plan.klasa.grupa2],
                                godzina=godzina,
                                dzien=dzien
                            )
                            plan.dodaj_lekcje(lekcja)
                            self.zwieksz_godziny_nauczyciela(nauczyciel)  # <- ZMIANA TUTAJ
                            godziny_do_przydzielenia -= 1
                            if godziny_do_przydzielenia == 0:
                                return True

            return godziny_do_przydzielenia == 0
        except Exception as e:
            logger.error(f"Błąd podczas planowania religii: {e}")
            return False


if __name__ == "__main__":
    try:
        print("Inicjalizacja generatora planu lekcji...")
        generator = GeneratorPlanu()

        print("\nGenerowanie planów lekcji...")
        plany = generator.generuj_wszystkie_plany()

        if plany:
            print("\nZapisywanie wygenerowanych planów do plików...")
            for plan in plany:
                generator.zapisz_plan_do_pliku(plan)

            print("\nCzy chcesz wyświetlić szczegóły wygenerowanych planów? (t/n)")
            if input().lower() == 't':
                for plan in plany:
                    generator.wizualizuj_plan(plan)
                    input("Naciśnij Enter, aby zobaczyć następny plan...")
        else:
            print("\nNie udało się wygenerować żadnego planu lekcji.")

    except Exception as e:
        logger.error(f"Błąd główny programu: {e}")
        print("Wystąpił błąd podczas działania programu. Sprawdź logi dla szczegółów.")
