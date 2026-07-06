"""Tests de equity.py: casos exactos por construcción, validación contra
valores de referencia publicados (PokerStove/calculadoras estándar) y
consistencia Monte Carlo vs enumeración.
"""

import random

import pytest

from src.cartas import cartas
from src.equity import equity_enumerada, equity_monte_carlo, equity_necesaria

RNG = lambda: random.Random(42)  # noqa: E731


# --- Pot odds ---


def test_equity_necesaria_apuesta_media():
    # pot 10, apuesta 5: pagar 5 por un pozo final de 20 → 25%
    assert equity_necesaria(10, 5) == pytest.approx(0.25)


def test_equity_necesaria_apuesta_pot():
    assert equity_necesaria(10, 10) == pytest.approx(1 / 3)


def test_equity_necesaria_rechaza_no_positivos():
    with pytest.raises(ValueError):
        equity_necesaria(0, 5)


# --- Casos exactos por construcción ---


def test_nuts_en_river_es_100():
    # Escalera real vs cualquier rival: no hay carta que nos gane
    eq = equity_enumerada(cartas("Ah Kh"), cartas("Qh Jh Th 2c 7d"))
    assert eq == pytest.approx(1.0)


def test_board_juega_para_ambos_es_50():
    # Escalera real completa en el board: todos empatan, medio pozo
    eq = equity_enumerada(cartas("2c 7d"), cartas("Ah Kh Qh Jh Th"))
    assert eq == pytest.approx(0.5)


def test_rival_conocido_river_es_binario():
    # Nuestro color gana a la pareja del rival en river cerrado
    eq = equity_enumerada(cartas("Ah Kh"), cartas("Qh 7h 2h 8c 3d"), rival=cartas("As Ad"))
    assert eq == pytest.approx(1.0)


def test_enumeracion_rechaza_espacios_grandes():
    with pytest.raises(ValueError, match="enumeración"):
        equity_enumerada(cartas("Ah Kh"), [])  # preflop vs rival desconocido


# --- Validación contra calculadoras de referencia (valores publicados) ---
# AA vs KK ≈ 81.9%, AKs vs QQ ≈ 46.0%, AA vs mano aleatoria ≈ 85.2%
# Monte Carlo n=8000 → error típico ~±0.6, tolerancia ±2 puntos.


def test_aa_vs_kk_preflop():
    eq = equity_monte_carlo(cartas("Ah Ad"), [], n=8000, rng=RNG(), rival=cartas("Kh Kd"))
    assert eq == pytest.approx(0.819, abs=0.02)


def test_aks_vs_qq_preflop():
    eq = equity_monte_carlo(cartas("Ah Kh"), [], n=8000, rng=RNG(), rival=cartas("Qs Qd"))
    assert eq == pytest.approx(0.460, abs=0.02)


def test_aa_vs_mano_aleatoria():
    eq = equity_monte_carlo(cartas("Ah Ad"), [], n=8000, rng=RNG())
    assert eq == pytest.approx(0.852, abs=0.02)


def test_proyecto_de_color_puro_en_flop_vs_pareja():
    # Flush draw puro (sin overcards) vs top pair: clásico 9 outs ≈ 36% (regla del 4)
    eq = equity_monte_carlo(cartas("7h 5h"), cartas("Kh 8h 2c"), n=8000, rng=RNG(), rival=cartas("Ks Qd"))
    assert eq == pytest.approx(0.36, abs=0.03)


def test_flush_draw_con_overcard_suma_outs():
    # Ah5h en el mismo spot: los 3 ases también son outs (~12 outs ≈ 46-48%)
    eq = equity_monte_carlo(cartas("Ah 5h"), cartas("Kh 8h 2c"), n=8000, rng=RNG(), rival=cartas("Ks Qd"))
    assert eq == pytest.approx(0.47, abs=0.03)


# --- Consistencia interna ---


def test_monte_carlo_coincide_con_enumeracion_en_river():
    mano, board = cartas("Ah Kd"), cartas("Qs Jc 7h 2d 9s")
    exacta = equity_enumerada(mano, board)
    aproximada = equity_monte_carlo(mano, board, n=8000, rng=RNG())
    assert aproximada == pytest.approx(exacta, abs=0.02)


def test_monte_carlo_reproducible_con_semilla():
    mano, board = cartas("Ah Kd"), cartas("Qs Jc 7h")
    a = equity_monte_carlo(mano, board, n=2000, rng=random.Random(7))
    b = equity_monte_carlo(mano, board, n=2000, rng=random.Random(7))
    assert a == b


def test_rechaza_cartas_repetidas():
    with pytest.raises(ValueError, match="repetidas"):
        equity_monte_carlo(cartas("Ah Kd"), cartas("Ah 7c 2d"), n=100, rng=RNG())
