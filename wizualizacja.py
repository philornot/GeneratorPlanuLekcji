import os
import logging
from typing import List

from stale import GODZINY_LEKCJI, DNI_TYGODNIA
from modele import PlanLekcji

logger = logging.getLogger(__name__)


class WizualizatorPlanu:
    """Klasa odpowiedzialna za wizualizację planów lekcji."""

    @staticmethod
    def zapisz_plan_do_pliku(plan: PlanLekcji, sciezka: str = "plany_lekcji") -> None:
        """Zapisuje plan lekcji do pliku tekstowego."""
        try:
            # Upewnij się, że katalog istnieje
            if not os.path.exists(sciezka):
                os.makedirs(sciezka)

            nazwa_planu = f"{sciezka}/plan_{plan.klasa.rocznik}{plan.klasa.litera}.txt"
            with open(nazwa_planu, 'w', encoding='utf-8') as f:
                # Nagłówek
                f.write(f"Plan lekcji dla klasy {plan.klasa.rocznik}{plan.klasa.litera}\n")
                f.write("-" * 100 + "\n")

                # Dla każdego dnia
                for dzien in DNI_TYGODNIA:
                    f.write(f"\n{dzien}:\n")

                    # Dla każdej godziny lekcyjnej
                    for i, (start, koniec) in enumerate(GODZINY_LEKCJI):
                        linia = f"{start}-{koniec}: "

                        # Jeśli są lekcje w tym terminie
                        if dzien in plan.lekcje and i in plan.lekcje[dzien]:
                            lekcje = []
                            for lekcja in plan.lekcje[dzien][i]:
                                # Formatowanie informacji o lekcji
                                grupy_str = ", ".join(g.nazwa for g in lekcja.grupy)
                                lekcje.append(
                                    f"{lekcja.przedmiot} ({grupy_str}) - "
                                    f"{lekcja.nauczyciel.imie_nazwisko} - "
                                    f"{lekcja.sala.nazwa}"
                                )
                            linia += " | ".join(lekcje)

                        f.write(linia + "\n")

            logger.info(f"Zapisano plan dla klasy {plan.klasa.rocznik}{plan.klasa.litera} "
                        f"do pliku {nazwa_planu}")

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania planu do pliku: {e}")

    @staticmethod
    def zapisz_wszystkie_plany(plany: List[PlanLekcji], sciezka: str = "plany_lekcji") -> None:
        """Zapisuje wszystkie plany do plików."""
        try:
            if not os.path.exists(sciezka):
                os.makedirs(sciezka)

            for plan in plany:
                WizualizatorPlanu.zapisz_plan_do_pliku(plan, sciezka)

            logger.info(f"Zapisano {len(plany)} planów do katalogu {sciezka}")

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wszystkich planów: {e}")

    @staticmethod
    def wizualizuj_plan(plan: PlanLekcji) -> None:
        """Wyświetla plan lekcji w konsoli."""
        try:
            print(f"\nPlan lekcji dla klasy {plan.klasa.rocznik}{plan.klasa.litera}")
            print("-" * 100)

            for dzien in DNI_TYGODNIA:
                print(f"\n{dzien}:")
                for i, (start, koniec) in enumerate(GODZINY_LEKCJI):
                    print(f"{start}-{koniec}: ", end="")

                    if dzien in plan.lekcje and i in plan.lekcje[dzien]:
                        lekcje = []
                        for lekcja in plan.lekcje[dzien][i]:
                            grupy_str = ", ".join(g.nazwa for g in lekcja.grupy)
                            lekcje.append(
                                f"{lekcja.przedmiot} ({grupy_str}) - "
                                f"{lekcja.nauczyciel.imie_nazwisko} - "
                                f"{lekcja.sala.nazwa}"
                            )
                        print(" | ".join(lekcje), end="")
                    print()  # Nowa linia po każdej godzinie

        except Exception as e:
            logger.error(f"Błąd podczas wizualizacji planu: {e}")
            print("Wystąpił błąd podczas wyświetlania planu.")

    @staticmethod
    def generuj_raport_statystyk(plany: List[PlanLekcji], sciezka: str = "plany_lekcji") -> None:
        """Generuje raport statystyk dla wszystkich planów."""
        try:
            nazwa_pliku = f"{sciezka}/raport_statystyk.txt"

            with open(nazwa_pliku, 'w', encoding='utf-8') as f:
                f.write("RAPORT STATYSTYK PLANÓW LEKCJI\n")
                f.write("=" * 50 + "\n\n")

                # Ogólne statystyki
                f.write(f"Liczba wygenerowanych planów: {len(plany)}\n\n")

                # Statystyki dla każdej klasy
                for plan in plany:
                    f.write(f"\nKlasa {plan.klasa.rocznik}{plan.klasa.litera}:\n")
                    f.write("-" * 30 + "\n")

                    # Liczba godzin w poszczególne dni
                    for dzien in DNI_TYGODNIA:
                        if dzien in plan.lekcje:
                            liczba_lekcji = sum(len(lekcje) for lekcje in plan.lekcje[dzien].values())
                            f.write(f"- {dzien}: {liczba_lekcji} lekcji\n")
                        else:
                            f.write(f"- {dzien}: 0 lekcji\n")

                    # Sprawdź okienka
                    okienka = []
                    for dzien in DNI_TYGODNIA:
                        if dzien in plan.lekcje:
                            godziny = sorted(plan.lekcje[dzien].keys())
                            for i in range(len(godziny) - 1):
                                if godziny[i + 1] - godziny[i] > 1:
                                    okienka.append(f"{dzien} ({godziny[i]} -> {godziny[i + 1]})")

                    if okienka:
                        f.write("\nZnalezione okienka:\n")
                        for okienko in okienka:
                            f.write(f"- {okienko}\n")
                    else:
                        f.write("\nBrak okienek w planie\n")

            logger.info(f"Wygenerowano raport statystyk: {nazwa_pliku}")

        except Exception as e:
            logger.error(f"Błąd podczas generowania raportu statystyk: {e}")