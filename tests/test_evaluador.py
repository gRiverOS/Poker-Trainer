"""Tests de regresión del evaluador de manos.

Casos conocidos y verificables a mano: es la pieza donde un bug silencioso
invalida todo lo demás. Cada caso nuevo que falle en el futuro se agrega aquí.
"""

import pytest

from src.cartas import cartas
from src.evaluador import Categoria, evaluar_5, evaluar_7, mejor_5


def puntaje(texto: str):
    return evaluar_5(cartas(texto))


def categoria(texto: str) -> Categoria:
    return puntaje(texto)[0]


# --- Detección de las 9 categorías ---


@pytest.mark.parametrize(
    "mano, esperada",
    [
        ("Ah Kh Qh Jh Th", Categoria.ESCALERA_COLOR),  # escalera real
        ("9s 8s 7s 6s 5s", Categoria.ESCALERA_COLOR),
        ("Ah Ad Ac As Kh", Categoria.POKER),
        ("3h 3d 3c 2s 2h", Categoria.FULL),
        ("Ah Jh 9h 6h 2h", Categoria.COLOR),
        ("Ts 9h 8d 7c 6s", Categoria.ESCALERA),
        ("5s 4h 3d 2c Ah", Categoria.ESCALERA),  # la rueda A-2-3-4-5
        ("Qh Qd Qc 8s 3h", Categoria.TRIO),
        ("Jh Jd 4c 4s 9h", Categoria.DOBLE_PAREJA),
        ("Ah Ad 9c 6s 3h", Categoria.PAREJA),
        ("Ah Jd 9c 6s 3h", Categoria.CARTA_ALTA),
    ],
)
def test_categorias(mano, esperada):
    assert categoria(mano) == esperada


def test_casi_escalera_no_es_escalera():
    # A-K-2-3-4 no envuelve: el as es alto o bajo, nunca puente
    assert categoria("Ah Kd 2c 3s 4h") == Categoria.CARTA_ALTA


# --- Desempates dentro de la misma categoría ---


def test_escalera_real_gana_a_escalera_color_menor():
    assert puntaje("Ah Kh Qh Jh Th") > puntaje("9s 8s 7s 6s 5s")


def test_la_rueda_es_la_escalera_mas_baja():
    assert puntaje("6s 5h 4d 3c 2h") > puntaje("5s 4h 3d 2c Ah")


def test_kicker_decide_entre_parejas_iguales():
    assert puntaje("Ah Ad Kc 6s 3h") > puntaje("As Ac Qc 6d 3d")


def test_pareja_mas_alta_gana():
    assert puntaje("Kh Kd 2c 3s 4h") > puntaje("Qh Qd Ac Ks 9h")


def test_doble_pareja_compara_la_pareja_alta_primero():
    assert puntaje("9h 9d 5c 5s 2h") > puntaje("8h 8d 7c 7s Ah")


def test_full_compara_el_trio_primero():
    assert puntaje("3h 3d 3c 2s 2h") > puntaje("2c 2d 2s Ah Ad")


def test_color_compara_las_cinco_cartas():
    assert puntaje("Ah Jh 9h 6h 3h") > puntaje("As Js 9s 6s 2s")


def test_empate_exacto_entre_palos_distintos():
    assert puntaje("Ah Kd Qc Js 9h") == puntaje("As Kh Qd Jc 9s")


def test_poker_desempata_por_kicker():
    assert puntaje("7h 7d 7c 7s Ah") > puntaje("7h 7d 7c 7s Kh")


# --- Mejor mano de 5 entre 7 (2 propias + board) ---


def test_evaluar_7_encuentra_el_color_escondido():
    # Escalera en la mesa, pero el color vale más
    siete = cartas("Ah Th 8h 7s 6h 5h 4c")
    assert evaluar_7(siete)[0] == Categoria.COLOR


def test_evaluar_7_dos_trios_forman_el_mejor_full():
    # Con 777 y 888 el mejor full es 888-77, no 777-88
    siete = cartas("7h 7d 7c 8s 8h 8d Kh")
    assert evaluar_7(siete) == (Categoria.FULL, (8, 7))


def test_mejor_5_devuelve_las_cartas_correctas():
    siete = cartas("Ah Kh Qh Jh Th 2c 3d")
    puntos, mano = mejor_5(siete)
    assert puntos[0] == Categoria.ESCALERA_COLOR
    assert {str(c) for c in mano} == {"Ah", "Kh", "Qh", "Jh", "Th"}


def test_el_board_juega_solo_si_es_lo_mejor():
    # Board con escalera al as; las cartas propias no mejoran nada
    siete = cartas("2h 3d Ts Js Qs Kc Ad")
    assert evaluar_7(siete) == (Categoria.ESCALERA, (14,))


# --- Validación de entrada ---


def test_evaluar_5_exige_5_cartas():
    with pytest.raises(ValueError):
        evaluar_5(cartas("Ah Kd"))


def test_evaluar_5_rechaza_repetidas():
    with pytest.raises(ValueError):
        evaluar_5(cartas("Ah Kd Qc Js") + cartas("Ah"))


# --- Regresión exhaustiva: consistencia interna sobre el mazo ---


def test_toda_mano_tiene_categoria_valida():
    # Muestreo determinista de manos de 5 cartas: el evaluador nunca revienta
    # y siempre devuelve una categoría del enum
    from itertools import combinations, islice

    from src.cartas import mazo

    for mano in islice(combinations(mazo(), 5), 0, 20000, 7):
        cat, desempates = evaluar_5(mano)
        assert cat in Categoria
        assert all(2 <= v <= 14 for v in desempates)
