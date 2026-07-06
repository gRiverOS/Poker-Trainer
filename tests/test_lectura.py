"""Tests del drill D3 lectura de manos: ganador, empates, categorías y ponderación."""

import random
from collections import Counter

from src.cartas import cartas
from src.drills.lectura import Resultado, Situacion, feedback, generar_situacion


def situacion(board: str, *manos: str) -> Situacion:
    return Situacion(tuple(cartas(board)), tuple(tuple(cartas(m)) for m in manos))


def test_gana_la_mano_correcta():
    s = situacion("Qh Jh 7c 2d 9s", "Ah Kd", "Qs Qc")  # trío de damas vs carta alta
    assert s.correcta == "2"
    assert s.categoria_ganadora == "trío"


def test_empate_cuando_juega_el_board():
    # Escalera real en el board: ambos juegan las cinco comunes
    s = situacion("Ah Kh Qh Jh Th", "2c 7d", "3s 8c")
    assert s.correcta == "e"
    assert s.ganadores == [0, 1]


def test_empate_parcial_no_es_empate_si_alguien_gana():
    # Dos manos empatan pero la tercera gana
    s = situacion("Qh Jh 7c 2d 9s", "Ah Kd", "As Kc", "Qs Qc")
    assert s.correcta == "3"


def test_el_color_escondido_gana_a_la_pareja_visible():
    s = situacion("Kh 8h 2h 7c 3d", "Ks Qd", "Ah 5h")  # top pair vs color
    assert s.correcta == "2"
    assert s.categoria_ganadora == "color"


def test_resultado_acierto_y_progreso():
    s = situacion("Qh Jh 7c 2d 9s", "Ah Kd", "Qs Qc")
    bien, mal = Resultado(s, "2"), Resultado(s, "1")
    assert bien.acierto and not mal.acierto
    assert bien.categoria == "trío"
    assert bien.contexto == "2 manos"
    assert "|" in bien.mano_texto


def test_feedback_describe_todas_las_manos():
    s = situacion("Kh 8h 2h 7c 3d", "Ks Qd", "Ah 5h")
    texto = feedback(Resultado(s, "1"))
    assert "✗" in texto and "color" in texto
    assert texto.count("Mano") >= 2 and "mejor 5" in texto


def test_generar_situacion_valida():
    rng = random.Random(5)
    for _ in range(50):
        s = generar_situacion(rng)
        assert len(s.board) == 5
        assert len(s.manos) in (2, 3, 4)
        todas = list(s.board) + [c for m in s.manos for c in m]
        assert len(set(todas)) == len(todas)


def test_ponderacion_sesga_hacia_categorias_debiles():
    # Con peso altísimo para "pareja" y mínimo para el resto, las situaciones
    # cuya mano ganadora es una pareja deben aparecer más que sin ponderar.
    pesos_sesgados = {"pareja": 3.0}
    base = {}
    rng_a, rng_b = random.Random(9), random.Random(9)

    def proporcion_pareja(rng, pesos):
        cuenta = Counter(generar_situacion(rng, pesos).categoria_ganadora for _ in range(300))
        return cuenta["pareja"] / 300

    # pesos_sesgados: pareja=3.0 y todo lo demás cae al peso sin datos (2.0)
    assert proporcion_pareja(rng_a, pesos_sesgados) > proporcion_pareja(rng_b, base)
