# src/utils/visualization.py

import logging
from typing import Dict
from colorama import init, Fore, Style

logger = logging.getLogger(__name__)
init()  # inicjalizacja colorama

def display_fitness_result(result: 'FitnessResult'):
    """Wyświetla wyniki oceny w czytelnej formie"""
    print("\n" + "="*50)
    print(f"{Fore.CYAN}OCENA PLANU LEKCJI{Style.RESET_ALL}")
    print("="*50)

    # Wynik całkowity
    print(f"\n{Fore.GREEN}Wynik całkowity: {result.total_score:.2f}/100{Style.RESET_ALL}")

    # Szczegółowe wyniki
    print("\n🎯 Szczegółowe wyniki:")
    for criterion, score in result.detailed_scores.items():
        color = Fore.GREEN if score >= 90 else Fore.YELLOW if score >= 70 else Fore.RED
        print(f"{color}{criterion:20}: {score:.2f}/100{Style.RESET_ALL}")

    # Kary
    if result.penalties:
        print(f"\n{Fore.RED}❌ Kary:{Style.RESET_ALL}")
        for penalty, value in result.penalties.items():
            print(f"  • {penalty}: -{value:.2f}")

    # Nagrody
    if result.rewards:
        print(f"\n{Fore.GREEN}✅ Nagrody:{Style.RESET_ALL}")
        for reward, value in result.rewards.items():
            print(f"  • {reward}: +{value:.2f}")

    print("\n" + "="*50)