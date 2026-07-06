"""Tests del drill D1 preflop (RFI): situaciones, acción correcta y feedback."""

import random

from src.cartas import cartas
from src.drills.preflop import Resultado, Situacion, accion_correcta, feedback, generar_situacion, tip
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


# --- Tips (explicación construida desde el chart) ---


def test_tip_fold_menciona_el_minimo_y_donde_se_abre():
    # J6o en BTN: el mínimo offsuit con J es J9o, y no se abre desde ninguna posición
    texto = tip(situacion("BTN", "Jd 6c"), CHART)
    assert "J9o" in texto and "ninguna posición" in texto


def test_tip_fold_indica_desde_donde_si_se_abre():
    # A9o en MP es fold, pero CO sí la abre (A8o+)
    texto = tip(situacion("MP", "Ah 9c"), CHART)
    assert "ATo" in texto and "recién desde CO" in texto


def test_tip_fold_menciona_version_suited_cuando_aplica():
    # K8o en BTN es fold (K7o+... K8o sí está). Usar Q8o: fold en BTN, Q8s sí se abre (Q4s+)
    texto = tip(situacion("BTN", "Qh 8c"), CHART)
    assert "Q8s" in texto and "suited" in texto


def test_tip_open_de_pareja_explica_el_set():
    texto = tip(situacion("CO", "5c 5d"), CHART)
    assert "parejas" in texto and "set" in texto


def test_tip_open_menciona_el_borde_del_rango():
    # T9s en UTG: conectada suited, y es el mínimo con T suited en UTG
    texto = tip(situacion("UTG", "Ts 9s"), CHART)
    assert "escaleras" in texto and "T9s" in texto


def test_feedback_incluye_tip_solo_al_errar():
    s = situacion("BTN", "Jd 6c")
    con_error = Resultado(s, "open", "fold")
    sin_error = Resultado(s, "fold", "fold")
    assert "Tip:" in feedback(con_error, CHART)
    assert "Tip:" not in feedback(sin_error, CHART)
