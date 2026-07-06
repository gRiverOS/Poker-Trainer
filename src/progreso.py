"""Persistencia de resultados por sesión (append a historial CSV en output/).

Formato una-fila-por-respuesta para poder graficar tendencia después. Cada
drill aporta resultados con la misma interfaz: categoria (para agrupar el
resumen), contexto, mano_texto, respuesta_texto, correcta_texto y acierto.
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RUTA_HISTORIAL = Path(__file__).parent.parent / "output" / "historial.csv"
COLUMNAS = ["timestamp", "drill", "contexto", "mano", "respuesta", "correcta", "acierto"]


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
                [marca, drill, r.contexto, r.mano_texto, r.respuesta_texto, r.correcta_texto, int(r.acierto)]
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
