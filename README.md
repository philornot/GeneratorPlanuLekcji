# Generator Planu Lekcji - Zadanie

## 1. Struktura Szkoły

### Klasy
- 4 roczniki (klasy 1-4)
- 5 klas w każdym roczniku (A-E)
- Każda klasa dzieli się na 2 grupy (np. 1A1 i 1A2)
- Łącznie: 20 klas = 40 grup

### Godziny Lekcyjne
- 9 godzin lekcyjnych dziennie:
  1. 08:00 - 08:45
  2. 08:50 - 09:35
  3. 09:45 - 10:30
  4. 10:45 - 11:30
  5. 11:40 - 12:25
  6. 12:55 - 13:40
  7. 13:50 - 14:35
  8. 14:40 - 15:25
  9. 15:30 - 16:15

### Wymiar Godzin Tygodniowo
- Klasy 1: 25h/tydzień
- Klasy 2: 32h/tydzień
- Klasy 3: 35h/tydzień
- Klasy 4: 28h/tydzień

## 2. Przedmioty

### Lista Przedmiotów z Wymiarem Godzinowym
Format: (1kl, 2kl, 3kl, 4kl) - godziny tygodniowo per klasa

Przedmioty dla całej klasy:
- Polski: (4, 4, 4, 4)
- Matematyka: (4, 4, 4, 3)
- Niemiecki: (2, 2, 2, 2)
- Francuski: (2, 2, 2, 2)
- Hiszpański: (2, 2, 2, 2)
- Fizyka: (1, 2, 2, 2)
- Biologia: (1, 2, 2, 1)
- Chemia: (1, 2, 2, 1)
- Historia: (2, 2, 2, 2)
- HiT: (1, 1, 0, 0)
- Przedsiębiorczość: (0, 1, 1, 0)
- Religia: (2, 2, 2, 2)

Przedmioty dzielone na grupy:
- Angielski: (3, 3, 3, 3)
- Informatyka: (1, 1, 1, 1)
- WF: (3, 3, 3, 3)

## 3. Infrastruktura

### Sale Zwykłe
- 26 sal ogólnych (numery 1-28, bez 14 i 24)
- Każda mieści całą klasę lub pojedynczą grupę
- Mogą odbywać się w nich wszystkie przedmioty oprócz informatyki i WF

### Sale Specjalne
Informatyka:
- Sala 14: mieści 1 grupę
- Sala 24: mieści 1 grupę
- UWAGA: Informatyka może odbywać się TYLKO w tych salach

WF:
- Siłownia: 1 grupa
- Mała sala gimnastyczna: 3 grupy
- Duża hala: 6 grup

## 4. Zasady Układania Planu

### Zasady Ogólne
1. Każda klasa musi mieć zajęcia we wszystkie dni robocze (pon-pt)

2. Liczba lekcji w ciągu dnia (nie licząc religii):
   - Minimum: 5 lekcji
   - Maksimum: 8 lekcji
   - UWAGA: religia nie wlicza się do tego limitu, gdyż jest nieobowiązkowa
   - Przykład 1: jeśli klasa ma 5 lekcji + religię, to jest to poprawny plan
   - Przykład 2: jeśli klasa ma 4 lekcje + religię, to jest to błędny plan
   - Przykład 3: jeśli klasa ma 8 lekcji + religię, to jest to poprawny plan
   - Przykład 4: jeśli klasa ma 9 lekcji (bez religii), to jest to błędny plan

3. Plan każdej grupy musi być ciągły:
   - Jeśli grupa ma lekcje w danym dniu, nie może mieć "okienek" (pustych godzin) między nimi
   - Przykład poprawny: lekcje 1-5, potem koniec
   - Przykład błędny: lekcje 1-3, przerwa, lekcje 5-7

2. Grupy mogą mieć różne godziny rozpoczęcia i zakończenia:
   - Grupa 1 może mieć lekcje 1-5
   - Grupa 2 może mieć lekcje 3-7
   - ALE: jeśli grupa ma lekcje, muszą być one ciągłe

### Przedmioty Dzielone (Angielski, Informatyka, WF)
1. Gdy jedna grupa ma przedmiot dzielony:
   - Druga grupa MUSI mieć w tym czasie inny przedmiot dzielony lub być wolna
   - Jeśli grupa jest wolna, ta godzina musi być jej pierwszą lub ostatnią w danym dniu

2. Przykłady poprawne:
   ```
   8:00 - Grupa 1: Angielski, Grupa 2: WF
   8:50 - Grupa 1: WF, Grupa 2: Informatyka
   ```
   lub
   ```
   8:00 - Grupa 1: Angielski, Grupa 2: wolne
   8:50 - Grupa 1: Polski, Grupa 2: Polski
   9:45 - Grupa 1: Matematyka, Grupa 2: Matematyka
   ```

3. Przykłady błędne:
   ```
   8:00 - Grupa 1: Angielski, Grupa 2: wolne
   8:50 - Grupa 1: Polski, Grupa 2: wolne
   9:45 - Grupa 1: Matematyka, Grupa 2: Polski
   ```

### Szczególne Wymagania Przedmiotów

1. Religia:
   - Musi być pierwszą LUB ostatnią lekcją w danym dniu dla całej klasy
   - Przykład 1: jeśli klasa ma lekcje 1-6, religia może być na 1. lub 6. lekcji
   - Przykład 2: jeśli klasa kończy o 13:40, religia nie może być o 15:30

2. Matematyka i fizyka:
   - Nie mogą być pierwszą ani ostatnią lekcją w planie klasy danego dnia
   - Przykład: jeśli klasa ma lekcje 2-7, matematyka nie może być na 2. ani 7. lekcji

3. Maksymalna liczba godzin pod rząd:
   - Matematyka: maks. 2h
   - Polski: maks. 2h
   - Informatyka: maks. 2h
   - WF: maks. 1h dla danej grupy dziennie

## 5. Nauczyciele

### Liczebność i Przydział Przedmiotów
- Szkoła ma stałą liczbę 40 nauczycieli
- System podczas inicjalizacji przydziela każdemu nauczycielowi 1-2 przedmioty do nauczania
- Przydział przedmiotów jest stały w trakcie generowania planu
- System musi tak dobrać przedmioty nauczycielom, by zaspokoić potrzeby szkoły
- Przykład: jeśli szkoła potrzebuje dużo godzin matematyki, więcej nauczycieli powinno uczyć tego przedmiotu

### Zasady Ogólne
- Nauczyciel nie może prowadzić dwóch lekcji jednocześnie
- Jeśli nauczyciel uczy dwóch przedmiotów, muszą być one ze sobą powiązane (np. matematyka-fizyka, biologia-chemia)

### Dostępność
- Część nauczycieli (40 osób) pracuje też w innych szkołach:
  - 13 osób dostępnych 2 dni w tygodniu
  - 27 osób dostępnych 3 dni w tygodniu
- Pozostali nauczyciele dostępni cały tydzień

## 6. Struktura Projektu
1. `stale.py`: stałe, enumeracje, podstawowe struktury
2. `infrastruktura.py`: zarządzanie salami i klasami
3. `nauczyciele.py`: generowanie i zarządzanie kadrą
4. `generator_planu.py`: główna logika generowania planu

## 7. Wymagana Wizualizacja
Plan dla każdej klasy powinien pokazywać:
- Godziny zajęć
- Nazwy przedmiotów
- Przydzielone sale
- Nauczycieli
- Podział na grupy (jeśli występuje)