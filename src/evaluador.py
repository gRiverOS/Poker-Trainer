"""Ranking de manos de 5/7 cartas.

Módulo puro: no sabe que existe un CLI. El puntaje de una mano es una tupla
`(Categoria, desempates)` comparable directamente con < y ==: mayor tupla,
mejor mano. Los desempates son los valores de las cartas ordenados por
(repeticiones, valor) descendente — p. ej. el full 3-3-3-2-2 desempata (3, 2).
"""

from collections import Counter
from enum import IntEnum
from itertools import combinations

from src.cartas import Carta

Puntaje = tuple["Categoria", tuple[int, ...]]


class Categoria(IntEnum):
    CARTA_ALTA = 0
    PAREJA = 1
    DOBLE_PAREJA = 2
    TRIO = 3
    ESCALERA = 4
    COLOR = 5
    FULL = 6
    POKER = 7
    ESCALERA_COLOR = 8


NOMBRES = {
    Categoria.CARTA_ALTA: "carta alta",
    Categoria.PAREJA: "pareja",
    Categoria.DOBLE_PAREJA: "doble pareja",
    Categoria.TRIO: "trío",
    Categoria.ESCALERA: "escalera",
    Categoria.COLOR: "color",
    Categoria.FULL: "full house",
    Categoria.POKER: "póker",
    Categoria.ESCALERA_COLOR: "escalera de color",
}


def _escalera(valores_distintos: list[int]) -> int | None:
    """Carta alta de la escalera si los 5 valores distintos son consecutivos.

    La rueda (A-2-3-4-5) cuenta como escalera con alta 5, no 14.
    """
    if len(valores_distintos) != 5:
        return None
    alto, bajo = max(valores_distintos), min(valores_distintos)
    if alto - bajo == 4:
        return alto
    if set(valores_distintos) == {14, 5, 4, 3, 2}:
        return 5
    return None


def evaluar_5(mano: list[Carta] | tuple[Carta, ...]) -> Puntaje:
    """Puntaje de una mano de exactamente 5 cartas."""
    if len(mano) != 5:
        raise ValueError(f"evaluar_5 requiere 5 cartas, recibió {len(mano)}")
    if len(set(mano)) != 5:
        raise ValueError("Cartas repetidas en la mano")

    conteo = Counter(c.valor for c in mano)
    grupos = sorted(conteo.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    desempates = tuple(valor for valor, _ in grupos)
    formas = sorted(conteo.values(), reverse=True)
    es_color = len({c.palo for c in mano}) == 1
    alta_escalera = _escalera(sorted(conteo))

    if alta_escalera and es_color:
        return (Categoria.ESCALERA_COLOR, (alta_escalera,))
    if formas[0] == 4:
        return (Categoria.POKER, desempates)
    if formas == [3, 2]:
        return (Categoria.FULL, desempates)
    if es_color:
        return (Categoria.COLOR, desempates)
    if alta_escalera:
        return (Categoria.ESCALERA, (alta_escalera,))
    if formas[0] == 3:
        return (Categoria.TRIO, desempates)
    if formas == [2, 2, 1]:
        return (Categoria.DOBLE_PAREJA, desempates)
    if formas[0] == 2:
        return (Categoria.PAREJA, desempates)
    return (Categoria.CARTA_ALTA, desempates)


def mejor_5(disponibles: list[Carta] | tuple[Carta, ...]) -> tuple[Puntaje, tuple[Carta, ...]]:
    """Mejor mano de 5 cartas entre 5, 6 o 7 disponibles, con su puntaje.

    Para 7 cartas evalúa las 21 combinaciones (fuerza bruta: sobra para los
    drills; si el Monte Carlo de F3 queda lento, la escalación es `treys`).
    """
    if not 5 <= len(disponibles) <= 7:
        raise ValueError(f"mejor_5 requiere 5 a 7 cartas, recibió {len(disponibles)}")
    return max((evaluar_5(combo), combo) for combo in combinations(disponibles, 5))


def evaluar_7(disponibles: list[Carta] | tuple[Carta, ...]) -> Puntaje:
    """Puntaje de la mejor mano de 5 entre 7 cartas (2 propias + 5 del board)."""
    return mejor_5(disponibles)[0]
