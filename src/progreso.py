"""Persistencia de resultados por sesión y pesos para repetición ponderada.

Formato una-fila-por-respuesta para poder graficar tendencia después. Cada
drill aporta resultados con la misma interfaz: categoria (para agrupar y
ponderar), contexto, mano_texto, respuesta_texto, correcta_texto y acierto.

Repetición ponderada (spaced repetition simplificada, ver diseño §4): cada
categoría recibe peso = 1 + 2·tasa_de_error histórica, así las categorías
donde más fallas aparecen más seguido. Sin datos, una categoría parte con
peso 2.0 (equivale a asumir 50% de error: exploración neutra).
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RUTA_HISTORIAL = Path(__file__).parent.parent / "output" / "historial.csv"
COLUMNAS = ["timestamp", "drill", "categoria", "contexto", "mano", "respuesta", "correcta", "acierto"]
PESO_SIN_DATOS = 2.0


def registrar(resultados, drill: str, ruta: Path = RUTA_HISTORIAL, ahora: datetime | None = None) -> None:
    """Appendea los resultados de una sesión al historial (crea el CSV si no existe)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not ruta.exists()
    marca = (ahora or datetime.now()).isoformat(timespec="seconds")
    with ruta.open("a", newline="") as f:
        escritor = csv.writer(f)
        if nuevo:
            escritor.writerow(COLUMNAS)
        for r in resultados:
            escritor.writerow(
                [
                    marca,
                    drill,
                    r.categoria,
                    r.contexto,
                    r.mano_texto,
                    r.respuesta_texto,
                    r.correcta_texto,
                    int(r.acierto),
                ]
            )


def resumen(resultados) -> dict:
    """Resumen de una sesión: % de acierto total y por categoría del drill."""
    total = len(resultados)
    aciertos = sum(r.acierto for r in resultados)
    por_categoria: dict[str, list[int]] = defaultdict(list)
    for r in resultados:
        por_categoria[r.categoria].append(int(r.acierto))
    return {
        "total": total,
        "aciertos": aciertos,
        "pct": round(100 * aciertos / total, 1) if total else 0.0,
        "por_categoria": {
            cat: {"total": len(v), "aciertos": sum(v), "pct": round(100 * sum(v) / len(v), 1)}
            for cat, v in sorted(por_categoria.items())
        },
    }


def cargar_pesos(drill: str, ruta: Path = RUTA_HISTORIAL) -> dict[str, float]:
    """Peso por categoría según el historial del drill: 1 + 2·tasa_de_error.

    Categorías sin historial no aparecen; el consumidor usa PESO_SIN_DATOS.
    """
    if not ruta.exists():
        return {}
    aciertos: dict[str, list[int]] = defaultdict(list)
    with ruta.open(newline="") as f:
        for fila in csv.DictReader(f):
            if fila["drill"] == drill:
                aciertos[fila["categoria"]].append(int(fila["acierto"]))
    return {
        cat: 1 + 2 * (1 - sum(v) / len(v))
        for cat, v in aciertos.items()
    }
