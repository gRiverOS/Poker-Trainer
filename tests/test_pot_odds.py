"""Tests del drill D2 pot odds: situaciones, decisión correcta, zona gris y feedback."""

import random

from src.cartas import cartas
from src.drills.pot_odds import ZONA_GRIS, Resultado, Situacion, feedback, generar_situacion


def situacion(pot=10.0, apuesta=5.0, calle=3) -> Situacion:
    mano = tuple(cartas("Ah Kh"))
    board = tuple(cartas("Qs Jc 7h 2d")[:calle])
    return Situacion(mano, board, pot, apuesta)


def test_generar_situacion_valida():
    rng = random.Random(3)
    for _ in range(100):
        s = generar_situacion(rng)
        assert s.calle in ("flop", "turn")
        assert len(set(s.mano) | set(s.board)) == 2 + len(s.board)
        assert s.apuesta <= s.pot


def test_necesaria_en_porcentaje():
    assert situacion(pot=10, apuesta=5).necesaria == 25.0


def test_call_correcto_con_equity_sobrada():
    r = Resultado(situacion(), "call", equity_real=40.0)
    assert r.correcta == "call" and r.acierto


def test_fold_correcto_con_equity_corta():
    r = Resultado(situacion(), "fold", equity_real=15.0)
    assert r.correcta == "fold" and r.acierto
    assert not Resultado(situacion(), "call", equity_real=15.0).acierto


def test_zona_gris_acepta_ambas():
    justo = 25.0 + ZONA_GRIS / 2
    for decision in ("call", "fold"):
        r = Resultado(situacion(), decision, equity_real=justo)
        assert r.correcta is None and r.acierto
        assert r.correcta_texto == "limite"


def test_error_de_estimacion():
    r = Resultado(situacion(), "call", equity_real=40.0, estimacion=32.0)
    assert r.error_estimacion == 8.0
    assert Resultado(situacion(), "call", equity_real=40.0).error_estimacion is None


def test_feedback_menciona_equity_y_estimacion():
    r = Resultado(situacion(), "call", equity_real=40.0, estimacion=32.0)
    texto = feedback(r)
    assert "40.0%" in texto and "25.0%" in texto and "8.0 puntos" in texto


def test_interfaz_de_progreso():
    r = Resultado(situacion(), "call", equity_real=40.0, estimacion=32.0)
    assert r.categoria == "flop"
    assert "pot=10" in r.contexto
    assert "|" in r.mano_texto
    assert r.respuesta_texto == "call est=32%"
