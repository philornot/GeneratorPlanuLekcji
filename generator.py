import logging
from typing import List, Dict, Set, Optional
import time

from stale import GODZINY_LEKCJI, DNI_TYGODNIA, PRZEDMIOTY_ROCZNIKI, PRZEDMIOTY_DZIELONE
from modele import PlanLekcji, Lekcja
from walidacja import WalidatorPlanu
from planowanie import PlanowaniePrzedmiotow
from wizualizacja import WizualizatorPlanu
from infrastruktura import Sala, Klasa, Grupa, generuj_sale, generuj_klasy
from nauczyciele import Nauczyciel, generuj_nauczycieli

logger = logging.getLogger(__name__)


class GeneratorPlanu:
    """Główna klasa odpowiedzialna za generowanie planów lekcji."""

    def __init__(self):
        """Inicjalizuje generator i jego komponenty."""
        try:
            # Generowanie podstawowych danych
            self.sale = generuj_sale()
            self.klasy = generuj_klasy()
            self.nauczyciele = generuj_nauczycieli()

            # Inicjalizacja komponentów
            self.walidator = WalidatorPlanu()
            self.planowanie = PlanowaniePrzedmiotow(self.sale, self.nauczyciele)
            self.wizualizator = WizualizatorPlanu()

            # Stan generatora
            self.plany: List[PlanLekcji] = []
            logger.info("Zainicjalizowano generator planu")

        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji generatora: {e}")
            raise

    def generuj_plan_dla_klasy(self, plany_wygenerowane: List[PlanLekcji], klasa: Klasa) -> Optional[PlanLekcji]:
        """Generuje plan dla pojedynczej klasy."""
        try:
            plan = PlanLekcji(klasa=klasa, lekcje={dzien: {} for dzien in DNI_TYGODNIA})
            logger.info(f"Rozpoczęto generowanie planu dla klasy {klasa.rocznik}{klasa.litera}")

            # 1. Najpierw przedmioty z dużą liczbą godzin i sztywnymi ograniczeniami
            for przedmiot in ['matematyka', 'polski', 'fizyka', 'historia', 'chemia']:
                if not self.planowanie.planuj_przedmiot(plany_wygenerowane, plan, przedmiot):
                    return None

            # 2. Przedmioty dzielone na grupy
            for przedmiot in PRZEDMIOTY_DZIELONE:
                if not self.planowanie.planuj_przedmiot_dzielony(plany_wygenerowane, plan, przedmiot):
                    return None

            # 3. Pozostałe przedmioty (oprócz religii)
            for przedmiot, godziny in PRZEDMIOTY_ROCZNIKI.items():
                if przedmiot not in PRZEDMIOTY_DZIELONE and przedmiot not in ['religia', 'matematyka', 'polski',
                                                                              'fizyka', 'historia', 'chemia']:
                    if not self.planowanie.planuj_przedmiot(plany_wygenerowane, plan, przedmiot):
                        return None

            # 4. Na końcu religia (musi być przed/po innych lekcjach)
            if not self.planowanie.planuj_religie(plany_wygenerowane, plan):
                logger.error(f"Nie udało się zaplanować religii dla klasy {klasa.rocznik}{klasa.litera}")
                return None

            # Weryfikacja całego planu
            if not self.walidator.weryfikuj_plan(plan):
                logger.error(f"Plan nie przeszedł weryfikacji dla klasy {klasa.rocznik}{klasa.litera}")
                return None

            if not self.walidator.sprawdz_okienka_w_planie(plan):
                logger.warning(f"Plan zawiera duże przerwy między lekcjami dla klasy {klasa.rocznik}{klasa.litera}")

            logger.info(f"Zakończono generowanie planu dla klasy {klasa.rocznik}{klasa.litera}")
            return plan

        except Exception as e:
            logger.error(f"Błąd podczas generowania planu dla klasy {klasa.rocznik}{klasa.litera}: {e}")
            return None

    def generuj_wszystkie_plany(self, max_prob: int = 3) -> List[PlanLekcji]:
        """Generuje plany lekcji dla wszystkich klas."""
        try:
            logger.info("Rozpoczęto generowanie planów dla wszystkich klas")
            self.plany = []
            nieudane_klasy = []

            # Sortuj klasy według liczby godzin (najpierw trudniejsze przypadki)
            posortowane_klasy = sorted(
                self.klasy,
                key=lambda k: PRZEDMIOTY_ROCZNIKI['religia'][k.rocznik - 1],
                reverse=True
            )

            proba = 1
            print(f"\nGenerowanie planów (próba {proba}/{max_prob}):")
            print("=" * 50)

            while proba <= max_prob:
                self.planowanie.reset()  # Reset stanu między próbami
                total_klasy = len(posortowane_klasy)
                problematyczne_klasy = set()

                for idx, klasa in enumerate(posortowane_klasy, 1):
                    print(f"\rKlasa {klasa.rocznik}{klasa.litera} ({idx}/{total_klasy}) ", end="")
                    if proba > 1:
                        print(f"[Restart {proba}/{max_prob}] ", end="")

                    start_time = time.time()
                    plan = self.generuj_plan_dla_klasy(self.plany, klasa)
                    czas_generowania = time.time() - start_time

                    if plan is not None:
                        self.plany.append(plan)
                        print(f"✓ ({czas_generowania:.1f}s)")
                    else:
                        problematyczne_klasy.add(f"{klasa.rocznik}{klasa.litera}")
                        print(f"✗ ({czas_generowania:.1f}s)")

                if not problematyczne_klasy:
                    break  # Sukces - wszystkie plany wygenerowane

                # Pokaż statystyki przed kolejną próbą
                print("\nStatystyki tej próby:")
                print(f"- Wygenerowano {len(self.plany)}/{total_klasy} planów")
                print("- Problematyczne klasy:")
                for klasa in sorted(problematyczne_klasy):
                    print(f"  * {klasa}")

                if proba < max_prob:
                    print(f"\nRozpoczynam próbę {proba + 1}/{max_prob}...")
                    self.plany = []
                    nieudane_klasy = list(problematyczne_klasy)
                    proba += 1
                    print("=" * 50)
                else:
                    nieudane_klasy = list(problematyczne_klasy)
                    break

            # Podsumowanie końcowe
            print("\nPodsumowanie końcowe:")
            print(f"- Wykonano {proba} prób")
            print(f"- Wygenerowano {len(self.plany)}/{len(self.klasy)} planów")

            if nieudane_klasy:
                print("- Nie udało się wygenerować planów dla klas:")
                print(f"  {', '.join(sorted(nieudane_klasy))}")

            return self.plany

        except Exception as e:
            logger.error(f"Błąd podczas generowania wszystkich planów: {e}")
            return []

    def zapisz_plany(self, sciezka: str = "plany_lekcji") -> None:
        """Zapisuje wszystkie wygenerowane plany do plików."""
        try:
            self.wizualizator.zapisz_wszystkie_plany(self.plany, sciezka)
            self.wizualizator.generuj_raport_statystyk(self.plany, sciezka)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania planów: {e}")

    def wizualizuj_plany(self) -> None:
        """Wyświetla wszystkie wygenerowane plany."""
        try:
            for plan in self.plany:
                self.wizualizator.wizualizuj_plan(plan)
                input("Naciśnij Enter, aby zobaczyć następny plan...")
        except Exception as e:
            logger.error(f"Błąd podczas wizualizacji planów: {e}")