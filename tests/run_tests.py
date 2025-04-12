# tests/run_tests.py
# !/usr/bin/env python3
import pytest
import sys
import os
import subprocess
from pathlib import Path
import importlib.util

# Dodanie głównego katalogu projektu do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))


def install_package(package_name):
    """Instaluje pakiet Python za pomocą pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Błąd podczas instalacji pakietu {package_name}")
        return False


def run_tests():
    """Uruchamia wszystkie testy z raportowaniem"""
    # Stwórz katalog na raporty jeśli nie istnieje
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    # Rejestracja markera slow
    pytest.ini_options = {"markers": "slow: marks tests as slow (deselect with '-m \"not slow\"')"}

    # Argumenty dla pytest
    args = [
        # Ścieżka do testów
        str(Path(__file__).parent),
        # Szczegółowość logów
        "-v",
        # Pokaż 5 najwolniejszych testów
        "--durations=5",
        # Pokaż postęp
        "-xvs",
    ]

    # Sprawdź, czy pytest-html jest zainstalowany
    has_html = importlib.util.find_spec("pytest_html") is not None
    if not has_html:
        print("Pakiet pytest-html nie jest zainstalowany.")
        user_choice = input("Czy chcesz zainstalować pytest-html, aby generować raporty HTML? (t/n): ")

        if user_choice.lower() in ['t', 'tak', 'y', 'yes', 'ta', 'ye']:
            print("Instalowanie pytest-html...")
            if install_package("pytest-html"):
                print("Zainstalowano pytest-html pomyślnie!")
                has_html = True
            else:
                print("Nie udało się zainstalować pytest-html. Raporty HTML nie będą generowane.")
        else:
            print("Pominięto instalację pytest-html. Raporty HTML nie będą generowane.")

    if has_html:
        # Użyj ścieżki systemowej
        html_path = report_dir / "report.html"
        args.append(f"--html={html_path}")
        print(f"Raport HTML zostanie zapisany w: {html_path}")

    # Jeśli podano argumenty z linii poleceń, użyj ich
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    # Uruchom testy
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(run_tests())