# models/room_optimizer.py
from typing import Optional

from .lesson import Lesson
from .schedule import Schedule


def znajdz_optymalna_sale(schedule: Schedule, lesson: Lesson) -> Optional[str]:
    """Znajduje optymalną salę dla lekcji"""
    plan_klasy = schedule.classes[lesson.class_name].schedule

    # Spróbuj wykorzystać tę samą salę co poprzednio
    poprzednia_godzina = lesson.hour - 1
    if poprzednia_godzina > 0:
        poprzednie_lekcje = plan_klasy[lesson.day][poprzednia_godzina]
        if poprzednie_lekcje:
            poprzednia_sala = poprzednie_lekcje[0].room_id
            if schedule.classrooms[poprzednia_sala].can_accommodate(lesson):
                return poprzednia_sala

    # Znajdź najbliższą dostępną salę
    dostepne_sale = []
    for room_id, sala in schedule.classrooms.items():
        if sala.can_accommodate(lesson):
            dostepne_sale.append((room_id, sala))

    if not dostepne_sale:
        return None

    # Sortuj według piętra
    home_room = schedule.classes[lesson.class_name].home_room
    posortowane_sale = sorted(
        dostepne_sale,
        key=lambda x: abs(x[1].floor - int(home_room) if home_room.isdigit() else 0)
    )

    return posortowane_sale[0][0]
