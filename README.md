# Generator Planu Lekcji - Zadanie

## Wstęp
Zadanie polega na stworzeniu systemu generującego plan lekcji dla liceum ogólnokształcącego. System powinien uwzględniać wszystkie ograniczenia i wymagania szkoły, takie jak dostępność sal, nauczycieli oraz specjalne zasady dotyczące przedmiotów.

## 1. Struktura Szkoły

### 1.1 Klasy
- 4 roczniki (klasy 1-4)
- 5 klas w każdym roczniku (oznaczenia A-E)
- Łącznie 20 klas
- Każda klasa jest podzielona na 2 grupy (np. 1A1 i 1A2)

### 1.2 Godziny Lekcyjne
Szkoła pracuje od 8:00 do 16:15. Plan dzienny składa się z 9 lekcji:
1. 08:00 - 08:45
2. 08:50 - 09:35
3. 09:45 - 10:30
4. 10:45 - 11:30
5. 11:40 - 12:25
6. 12:55 - 13:40
7. 13:50 - 14:35
8. 14:40 - 15:25
9. 15:30 - 16:15

### 1.3 Liczba Godzin Tygodniowo per Rocznik
- Klasy pierwsze: 25h
- Klasy drugie: 32h
- Klasy trzecie: 35h
- Klasy czwarte: 28h

## 2. Przedmioty i Ich Wymiar Godzinowy

### 2.1 Przedmioty i Liczba Godzin Tygodniowo
Format: (godziny_1kl, godziny_2kl, godziny_3kl, godziny_4kl)
- Polski: (4, 4, 4, 4)
- Matematyka: (4, 4, 4, 3)
- Angielski: (3, 3, 3, 3) - zajęcia w grupach
- Niemiecki: (2, 2, 2, 2)
- Francuski: (2, 2, 2, 2)
- Hiszpański: (2, 2, 2, 2)
- Fizyka: (1, 2, 2, 2)
- Informatyka: (1, 1, 1, 1) - zajęcia w grupach
- Biologia: (1, 2, 2, 1)
- Chemia: (1, 2, 2, 1)
- Historia: (2, 2, 2, 2)
- WF: (3, 3, 3, 3) - zajęcia w grupach
- HiT: (1, 1, 0, 0)
- Przedsiębiorczość: (0, 1, 1, 0)
- Religia: (2, 2, 2, 2)

### 2.2 Przedmioty Dzielone na Grupy
- Angielski
- Informatyka
- WF

## 3. Infrastruktura

### 3.1 Sale Lekcyjne
- 26 zwykłych sal (numerowane 1-28, z wyłączeniem 14 i 24)
- Każda zwykła sala może pomieścić całą klasę (2 grupy) lub jedną grupę
- Sale 14 i 24 to pracownie informatyczne (mieszczą po 1 grupie)

### 3.2 Sale WF
- Siłownia (pojemność: 1 grupa)
- Mała sala gimnastyczna (pojemność: 3 grupy)
- Duża hala (pojemność: 6 grup)

## 4. Ograniczenia i Zasady

### 4.1 Ogólne Zasady
- Brak "okienek" (wolnych godzin) w planie dla uczniów
- Klasy mogą zaczynać i kończyć o różnych porach
- WF: maksimum 1h dziennie dla klasy

### 4.2 Szczególne Wymagania dla Przedmiotów
- Religia: tylko na początku lub końcu dnia
- Matematyka i fizyka: nie mogą być na pierwszej ani ostatniej lekcji
- Przedmioty, które mogą być maksymalnie 2h pod rząd:
  - Matematyka
  - Polski
  - Informatyka

### 4.3 Grupy i Podziały
- Podczas lekcji dzielonych każda grupa może mieć:
  - Angielski
  - Informatykę
  - WF
  - Pustą lekcję (tylko jako pierwsza lub ostatnia w planie danego dnia)

## 5. Kadra

### 5.1 Wymagania
- System powinien automatycznie generować odpowiednią liczbę nauczycieli na podstawie zapotrzebowania
- Nauczyciel może uczyć maksymalnie 2 przedmioty (zgodnie z możliwymi kombinacjami)
- Nauczyciel nie może prowadzić dwóch różnych przedmiotów jednocześnie

### 5.2 Ograniczenia dla Nauczycieli
- Każdy nauczyciel może uczyć maksymalnie 2 różnych przedmiotów
- Nauczyciel nie może prowadzić dwóch różnych lekcji w tym samym czasie

### 5.3 Dostępność Nauczycieli
- 40 nauczycieli pracuje w innych szkołach:
  - 13 pracuje 2 dni w tygodniu
  - 27 pracuje 3 dni w tygodniu
- Pozostali nauczyciele są dostępni przez cały tydzień

## 6. Wymagania Implementacyjne

### 6.1 Struktura Projektu
Projekt powinien zawierać następujące pliki:
1. `stale.py` - stałe, enumeracje i podstawowe struktury
2. `infrastruktura.py` - zarządzanie salami i klasami
3. `nauczyciele.py` - generowanie i zarządzanie kadrą
4. `generator_planu.py` - główna logika generowania planu

### 6.2 Wymagane Funkcjonalności
1. Generowanie planu zajęć dla wszystkich klas
2. Automatyczne przydzielanie sal i nauczycieli
3. Sprawdzanie wszystkich ograniczeń
4. Wizualizacja wygenerowanego planu

## 7. Format Wyniku
System powinien generować czytelny plan lekcji dla każdej klasy, zawierający:
- Godziny zajęć
- Nazwy przedmiotów
- Przydzielone sale
- Nauczycieli
- Podział na grupy (jeśli dotyczy)