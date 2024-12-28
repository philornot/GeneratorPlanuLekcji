import logging
import sys
from generator import GeneratorPlanu

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('generator_planu.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    try:
        print("Inicjalizacja generatora planu lekcji...")
        generator = GeneratorPlanu()

        print("\nGenerowanie planów lekcji...")
        plany = generator.generuj_wszystkie_plany(max_prob=3)

        if plany:
            print("\nZapisywanie wygenerowanych planów do plików...")
            generator.zapisz_plany()

            print("\nCzy chcesz wyświetlić szczegóły wygenerowanych planów? (t/n)")
            if input().lower() == 't':
                generator.wizualizuj_plany()
        else:
            print("\nNie udało się wygenerować żadnego planu lekcji.")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Błąd główny programu: {e}", exc_info=True)
        print("Wystąpił błąd podczas działania programu. Sprawdź logi dla szczegółów.")
        return 1


if __name__ == "__main__":
    sys.exit(main())