"""Tests del drill D1 preflop (RFI + defensa de BB): situaciones, acción correcta y feedback."""

import random

from src.cartas import cartas
from src.drills.preflop import (
    ESCENARIOS,
    Resultado,
    Situacion,
    accion_correcta,
    feedback,
    generar_situacion,
    tip_defensa,
    tip_rfi,
)
from src.rangos import POSICIONES_RFI, cargar_defensa_bb, cargar_rfi

CHART = cargar_rfi()
DEFENSA = cargar_defensa_bb()


def situacion(pos: str, texto: str, abridor: str | None = None) -> Situacion:
    c1, c2 = cartas(texto)
    return Situacion(pos, (c1, c2), abridor)


def test_generar_situacion_valida():
    rng = random.Random(1)
    vistos = set()
    for _ in range(200):
        s = generar_situacion(rng)
        assert len(set(s.mano)) == 2
        if s.es_defensa:
            assert s.posicion == "BB" and s.abridor in POSICIONES_RFI
            vistos.add("defensa")
        else:
            assert s.posicion in POSICIONES_RFI and s.abridor is None
            vistos.add("rfi")
    assert vistos == {"rfi", "defensa"}  # la mezcla genera ambos escenarios


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
    texto = tip_rfi(situacion("BTN", "Jd 6c"), CHART)
    assert "J9o" in texto and "ninguna posición" in texto


def test_tip_fold_indica_desde_donde_si_se_abre():
    # A9o en MP es fold, pero CO sí la abre (A8o+)
    texto = tip_rfi(situacion("MP", "Ah 9c"), CHART)
    assert "ATo" in texto and "recién desde CO" in texto


def test_tip_fold_menciona_version_suited_cuando_aplica():
    texto = tip_rfi(situacion("BTN", "Qh 8c"), CHART)
    assert "Q8s" in texto and "suited" in texto


def test_tip_open_de_pareja_explica_el_set():
    texto = tip_rfi(situacion("CO", "5c 5d"), CHART)
    assert "parejas" in texto and "set" in texto


def test_tip_open_menciona_el_borde_del_rango():
    texto = tip_rfi(situacion("UTG", "Ts 9s"), CHART)
    assert "escaleras" in texto and "T9s" in texto


def test_feedback_incluye_tip_solo_al_errar():
    s = situacion("BTN", "Jd 6c")
    con_error = Resultado(s, "open", "fold")
    sin_error = Resultado(s, "fold", "fold")
    assert "Tip:" in feedback(con_error, CHART, DEFENSA)
    assert "Tip:" not in feedback(sin_error, CHART, DEFENSA)


# --- Defensa de BB ---


def bb(texto: str, abridor: str) -> Situacion:
    return situacion("BB", texto, abridor)


def test_defensa_aa_siempre_3bet():
    for abridor in POSICIONES_RFI:
        assert accion_correcta(bb("Ah Ad", abridor), CHART, DEFENSA) == "3bet"


def test_defensa_basura_siempre_fold():
    for abridor in POSICIONES_RFI:
        assert accion_correcta(bb("7h 2c", abridor), CHART, DEFENSA) == "fold"


def test_defensa_depende_del_abridor():
    # T9o: fold vs open de UTG, call vs open de BTN
    assert accion_correcta(bb("Ts 9c", "UTG"), CHART, DEFENSA) == "fold"
    assert accion_correcta(bb("Ts 9c", "BTN"), CHART, DEFENSA) == "call"


def test_defensa_call_con_descuento():
    # 54s se paga incluso vs UTG (suited conectada con descuento)
    assert accion_correcta(bb("5s 4s", "UTG"), CHART, DEFENSA) == "call"


def test_defensa_categoria_para_ponderacion():
    r = Resultado(bb("Ah Ad", "BTN"), "3bet", "3bet")
    assert r.categoria == "BB vs BTN"
    assert "BB vs BTN" in ESCENARIOS


def test_tip_defensa_valor_y_bluff():
    assert "valor" in tip_defensa(bb("Ah Ad", "BTN"), DEFENSA)
    assert "bluff" in tip_defensa(bb("Ah 5h", "BTN"), DEFENSA)  # A5s: 3-bet de bluff


def test_tip_defensa_call_menciona_descuento():
    assert "descuento" in tip_defensa(bb("5s 4s", "UTG"), DEFENSA)


def test_tip_defensa_fold_menciona_vs_quien_se_defiende():
    # T9o se defiende vs BTN pero no vs UTG
    texto = tip_defensa(bb("Ts 9c", "UTG"), DEFENSA)
    assert "BTN" in texto


def test_feedback_defensa_muestra_ambos_rangos():
    r = Resultado(bb("Ah Ad", "BTN"), "call", "3bet")
    texto = feedback(r, CHART, DEFENSA)
    assert "3-bet BB vs BTN" in texto and "Call" in texto and "Tip:" in texto
