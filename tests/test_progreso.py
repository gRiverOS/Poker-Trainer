"""Tests de progreso.py: registro CSV y resumen de sesión."""

import csv
from datetime import datetime

from src.cartas import cartas
from src.drills.preflop import Resultado, Situacion
from src.progreso import COLUMNAS, registrar, resumen


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
    assert r["por_posicion"]["UTG"] == {"total": 2, "aciertos": 1, "pct": 50.0}
    assert r["por_posicion"]["BTN"]["pct"] == 100.0


def test_resumen_vacio():
    assert resumen([]) == {"total": 0, "aciertos": 0, "pct": 0.0, "por_posicion": {}}


def test_registrar_crea_y_appendea(tmp_path):
    ruta = tmp_path / "historial.csv"
    marca = datetime(2026, 7, 5, 12, 0, 0)
    registrar(RESULTADOS, drill="preflop", ruta=ruta, ahora=marca)
    registrar(RESULTADOS[:1], drill="preflop", ruta=ruta, ahora=marca)

    filas = list(csv.reader(ruta.open()))
    assert filas[0] == COLUMNAS  # header una sola vez
    assert len(filas) == 1 + 3 + 1
    assert filas[1] == ["2026-07-05T12:00:00", "preflop", "UTG", "AA", "open", "open", "1"]
    assert filas[2][6] == "0"  # el error quedó registrado como 0
