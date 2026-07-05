"""Tests del drill D1 preflop (RFI): situaciones, acción correcta y feedback."""

import random

from src.cartas import cartas
from src.drills.preflop import Resultado, Situacion, accion_correcta, feedback, generar_situacion
from src.rangos import POSICIONES_RFI, cargar_rfi

CHART = cargar_rfi()


def situacion(pos: str, texto: str) -> Situacion:
    c1, c2 = cartas(texto)
    return Situacion(pos, (c1, c2))


def test_generar_situacion_valida():
    rng = random.Random(1)
    for _ in range(100):
        s = generar_situacion(rng)
        assert s.posicion in POSICIONES_RFI
        assert len(set(s.mano)) == 2


def test_generar_situacion_reproducible():
    a = generar_situacion(random.Random(7))
    b = generar_situacion(random.Random(7))
    assert a == b


def test_aa_se_abre_desde_utg():
    assert accion_correcta(situacion("UTG", "Ah Ad"), CHART) == "open"


def test_basura_se_bota_desde_utg():
    assert accion_correcta(situacion("UTG", "7h 2c"), CHART) == "fold"


def test_mano_marginal_depende_de_la_posicion():
    # K7o: fold en CO, open en BTN según el chart de la fuente
    assert accion_correcta(situacion("CO", "Kh 7c"), CHART) == "fold"
    assert accion_correcta(situacion("BTN", "Kh 7c"), CHART) == "open"


def test_feedback_menciona_rango_y_veredicto():
    s = situacion("UTG", "Ah Ad")
    bueno = Resultado(s, "open", "open")
    malo = Resultado(s, "fold", "open")
    assert "✓" in feedback(bueno, CHART) and "✗" in feedback(malo, CHART)
    assert CHART["UTG"]["rango"] in feedback(bueno, CHART)


def test_resultado_acierto():
    s = situacion("BTN", "Ah 2c")
    assert Resultado(s, "open", "open").acierto
    assert not Resultado(s, "fold", "open").acierto
