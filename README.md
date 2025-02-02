# Generator Planu Lekcji

Prosty program do generowania planu lekcji dla szkół średnich. Napisany w Pythonie z wykorzystaniem algorytmów genetycznych.

## Co to jest?

To eksperymentalny program, który próbuje automatycznie generować plan lekcji. Nie jest idealny, ale może pomóc w początkowym rozplanowaniu zajęć. Program wykorzystuje algorytmy genetyczne do stopniowej poprawy planu.

## Jak uruchomić?

1. Zainstaluj Pythona (testowane na wersji 3.8+)
2. Zainstaluj wymagane biblioteki:
    ```bash
    pip install -r requirements.txt
    ```
3. Uruchom program:
    ```bash
    python src/main.py
    ```

## Jak używać?

Po uruchomieniu zobaczysz proste GUI z dwoma zakładkami:

### Zakładka "Struktura szkoły"
- Wybierz, ile klas ma każdy rocznik (1-5)
- Dodaj profile klas (np. mat-fiz)
- Określ przedmioty rozszerzone

### Zakładka "Parametry"
- Liczba iteracji (sugeruję zacząć od 100 dla testów)
- Wielkość populacji
- Współczynniki algorytmu (możesz zostawić domyślne)

Kliknij "Generuj plan" i czekaj. Program pokaże:
- Aktualny postęp
- Wykres poprawy jakości planu
- Końcowy plan w formie tabelki

## Ograniczenia

- Program jest w fazie eksperymentalnej
- Może generować niedoskonałe plany
- Nie obsługuje wszystkich możliwych scenariuszy i wymagań
- Interface jest podstawowy
- Może działać wolno przy dużej liczbie klas

## Problemy?

Jeśli program nie działa:
1. Sprawdź, czy masz wszystkie biblioteki
2. Sprawdź logi w folderze `logs/`
3. Spróbuj zmniejszyć liczbę klas/parametrów

## Planowane zmiany

- Poprawki błędów
- Szybsze działanie
- Lepsze UI
- Możliwość eksportu planu

Ten projekt jest realizowany jako hobby przez mało kompetentną osobę, więc nie oczekuj za dużo.