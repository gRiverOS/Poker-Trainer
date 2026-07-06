"""Cálculo de equity por enumeración exacta y Monte Carlo (reusa el evaluador).

Equity = probabilidad de ganar el pozo al showdown contra un rival, contando
los empates como medio pozo. Módulo puro, heads-up (un rival): es lo que el
drill D2 necesita. Medido: ~0,1 ms por muestra → 10.000 muestras ≈ 1 s, así
que Python puro alcanza de sobra (la escalación a `treys` quedó descartada
mientras esto no cambie).
"""

import random
from itertools import combinations

from src.cartas import Carta, mazo
from src.evaluador import evaluar_7

LIMITE_ENUMERACION = 50_000


def equity_necesaria(pot: float, apuesta: float) -> float:
    """Equity mínima para que pagar sea rentable: apuesta / (pot + 2·apuesta).

    El pot es lo que había ANTES de la apuesta del rival.
    """
    if pot <= 0 or apuesta <= 0:
        raise ValueError("pot y apuesta deben ser positivos")
    return apuesta / (pot + 2 * apuesta)


def _restantes(usadas: list[Carta]) -> list[Carta]:
    fuera = set(usadas)
    if len(fuera) != len(usadas):
        raise ValueError("Cartas repetidas entre mano, board y rival")
    return [c for c in mazo() if c not in fuera]


def _puntos(mi_mano, board, rival) -> float:
    mio = evaluar_7(list(mi_mano) + list(board))
    suyo = evaluar_7(list(rival) + list(board))
    return 1.0 if mio > suyo else 0.5 if mio == suyo else 0.0


def equity_enumerada(mi_mano, board, rival=None) -> float:
    """Equity exacta enumerando manos del rival y/o runouts del board.

    Solo para espacios chicos (river con rival desconocido, flop/turn con
    rival conocido). Si el espacio supera LIMITE_ENUMERACION, usa Monte Carlo.
    """
    mi_mano, board = list(mi_mano), list(board)
    if len(mi_mano) != 2 or len(board) > 5:
        raise ValueError("Se requieren 2 cartas propias y 0-5 de board")
    restantes = _restantes(mi_mano + board + (list(rival) if rival else []))

    rivales = [tuple(rival)] if rival else list(combinations(restantes, 2))
    total = 0.0
    casos = 0
    for manos_rival in rivales:
        libres = [c for c in restantes if c not in manos_rival]
        faltan = 5 - len(board)
        runouts = list(combinations(libres, faltan)) if faltan else [()]
        casos += len(runouts)
        if casos > LIMITE_ENUMERACION:
            raise ValueError(
                f"Espacio de enumeración supera {LIMITE_ENUMERACION}: usa equity_monte_carlo"
            )
        for runout in runouts:
            total += _puntos(mi_mano, board + list(runout), manos_rival)
    return total / casos


def equity_monte_carlo(mi_mano, board, n: int = 10_000, rng: random.Random | None = None, rival=None) -> float:
    """Equity aproximada muestreando rival y runout. Error típico ~±1% con n=10.000."""
    if n <= 0:
        raise ValueError("n debe ser positivo")
    mi_mano, board = list(mi_mano), list(board)
    rng = rng or random.Random()
    restantes = _restantes(mi_mano + board + (list(rival) if rival else []))
    faltan = 5 - len(board)
    por_muestra = faltan + (0 if rival else 2)

    total = 0.0
    for _ in range(n):
        if por_muestra:
            sorteo = rng.sample(restantes, por_muestra)
        else:
            sorteo = []
        manos_rival = tuple(rival) if rival else tuple(sorteo[:2])
        runout = sorteo[2:] if rival is None else sorteo
        total += _puntos(mi_mano, board + list(runout), manos_rival)
    return total / n
