"""Tests de la cuadrícula de rangos del CLI."""

from src.rangos import cargar_rfi
from trainer import VERDE, cuadricula

CHART = cargar_rfi()


def test_cuadricula_contiene_las_169_manos():
    salida = cuadricula("BTN", CHART)
    for nombre in ("AA", "22", "AKs", "AKo", "72o", "T9s"):
        assert nombre in salida


def test_cuadricula_pinta_exactamente_el_rango():
    # celdas verdes (más 1 del encabezado de la leyenda) == manos del rango
    for pos in ("UTG", "BTN"):
        salida = cuadricula(pos, CHART)
        assert salida.count(VERDE) == len(CHART[pos]["manos"]) + 1


def test_cuadricula_menciona_combos_y_fuente_del_rango():
    salida = cuadricula("UTG", CHART)
    assert "1326" in salida
    assert CHART["UTG"]["rango"] in salida


def test_cuadricula_sin_color_no_emite_ansi():
    salida = cuadricula("BTN", CHART, color=False)
    assert "\033[" not in salida
    assert "AA" in salida and "72o" in salida
