"""Tests de progreso.py: registro CSV y resumen de sesión (interfaz común de drills)."""

import csv
from datetime import datetime

from src.cartas import cartas
from src.drills.preflop import Resultado, Situacion
from src.progreso import COLUMNAS, cargar_pesos, registrar, resumen


def resultado(pos: str, texto: str, respuesta: str, correcta: str) -> Resultado:
    c1, c2 = cartas(texto)
    return Resultado(Situacion(pos, (c1, c2)), respuesta, correcta)


RESULTADOS = [
    resultado("UTG", "Ah Ad", "open", "open"),
    resultado("UTG", "7h 2c", "open", "fold"),
    resultado("BTN", "Kh 7c", "open", "open"),
]


def test_resumen():
    r = resumen(RESULTADOS)
    assert r["total"] == 3 and r["aciertos"] == 2 and r["pct"] == 66.7
    assert r["por_categoria"]["UTG"] == {"total": 2, "aciertos": 1, "pct": 50.0}
    assert r["por_categoria"]["BTN"]["pct"] == 100.0


def test_resumen_vacio():
    assert resumen([]) == {"total": 0, "aciertos": 0, "pct": 0.0, "por_categoria": {}}


def test_registrar_crea_y_appendea(tmp_path):
    ruta = tmp_path / "historial.csv"
    marca = datetime(2026, 7, 5, 12, 0, 0)
    registrar(RESULTADOS, drill="preflop", ruta=ruta, ahora=marca)
    registrar(RESULTADOS[:1], drill="preflop", ruta=ruta, ahora=marca)

    filas = list(csv.reader(ruta.open()))
    assert filas[0] == COLUMNAS  # header una sola vez
    assert len(filas) == 1 + 3 + 1
    assert filas[1] == ["2026-07-05T12:00:00", "preflop", "UTG", "UTG", "AA", "open", "open", "1"]
    assert filas[2][7] == "0"  # el error quedó registrado como 0


def test_registrar_resultados_de_pot_odds(tmp_path):
    from src.drills.pot_odds import Resultado as ResultadoPO, Situacion as SituacionPO

    s = SituacionPO(tuple(cartas("Ah Kh")), tuple(cartas("Qs Jc 7h")), 10.0, 5.0)
    r = ResultadoPO(s, "call", equity_real=40.0, estimacion=30.0)
    ruta = tmp_path / "historial.csv"
    registrar([r], drill="pot_odds", ruta=ruta, ahora=datetime(2026, 7, 5, 12, 0, 0))

    filas = list(csv.reader(ruta.open()))
    assert filas[1][1] == "pot_odds"
    assert filas[1][2] == "flop"
    assert filas[1][3] == "flop pot=10.0 apuesta=5.0"
    assert filas[1][5] == "call est=30%"


def test_cargar_pesos(tmp_path):
    ruta = tmp_path / "historial.csv"
    marca = datetime(2026, 7, 5, 12, 0, 0)
    # UTG: 1 acierto de 2 → tasa de error 0.5 → peso 2.0
    # BTN: 1 acierto de 1 → tasa de error 0.0 → peso 1.0
    registrar(RESULTADOS, drill="preflop", ruta=ruta, ahora=marca)
    pesos = cargar_pesos("preflop", ruta=ruta)
    assert pesos == {"UTG": 2.0, "BTN": 1.0}


def test_cargar_pesos_filtra_por_drill(tmp_path):
    ruta = tmp_path / "historial.csv"
    registrar(RESULTADOS, drill="preflop", ruta=ruta, ahora=datetime(2026, 7, 5, 12, 0, 0))
    assert cargar_pesos("lectura", ruta=ruta) == {}


def test_cargar_pesos_sin_historial(tmp_path):
    assert cargar_pesos("preflop", ruta=tmp_path / "no_existe.csv") == {}
