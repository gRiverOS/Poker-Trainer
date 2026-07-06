"""D3 — Lectura de manos: board completo + 2-4 manos, ¿cuál gana?

Entrena velocidad de lectura. El feedback muestra qué formó cada mano (su
categoría y su mejor 5), así también se practica "cuál es mi mejor mano de 5"
de forma pasiva. La repetición ponderada agrupa por la categoría de la mano
ganadora: si te cuesta ver los fulles, aparecen más fulles.
"""

import random
from dataclasses import dataclass
from functools import cached_property

from src.cartas import Carta, mazo
from src.evaluador import NOMBRES, mejor_5
from src.progreso import PESO_SIN_DATOS

CANTIDAD_MANOS = (2, 3, 4)
INTENTOS_PONDERACION = 20


@dataclass(frozen=True)
class Situacion:
    board: tuple[Carta, ...]  # 5 cartas
    manos: tuple[tuple[Carta, Carta], ...]  # 2 a 4 manos

    @cached_property
    def evaluaciones(self) -> list:
        """[(puntaje, mejor_5)] por mano, en orden."""
        return [mejor_5(list(m) + list(self.board)) for m in self.manos]

    @property
    def ganadores(self) -> list[int]:
        puntajes = [e[0] for e in self.evaluaciones]
        tope = max(puntajes)
        return [i for i, p in enumerate(puntajes) if p == tope]

    @property
    def correcta(self) -> str:
        """Respuesta correcta: "1".."4", o "e" si hay empate."""
        g = self.ganadores
        return "e" if len(g) > 1 else str(g[0] + 1)

    @property
    def categoria_ganadora(self) -> str:
        return NOMBRES[self.evaluaciones[self.ganadores[0]][0][0]]


@dataclass(frozen=True)
class Resultado:
    situacion: Situacion
    respuesta: str  # "1".."4" o "e"

    @property
    def correcta(self) -> str:
        return self.situacion.correcta

    @property
    def acierto(self) -> bool:
        return self.respuesta == self.correcta

    # --- interfaz común de progreso ---

    @property
    def categoria(self) -> str:
        return self.situacion.categoria_ganadora

    @property
    def contexto(self) -> str:
        return f"{len(self.situacion.manos)} manos"

    @property
    def mano_texto(self) -> str:
        board = " ".join(str(c) for c in self.situacion.board)
        manos = " / ".join(" ".join(str(c) for c in m) for m in self.situacion.manos)
        return f"{board} | {manos}"

    @property
    def respuesta_texto(self) -> str:
        return self.respuesta

    @property
    def correcta_texto(self) -> str:
        return self.correcta


def _candidata(rng: random.Random) -> Situacion:
    k = rng.choice(CANTIDAD_MANOS)
    cartas = rng.sample(mazo(), 5 + 2 * k)
    manos = tuple(tuple(cartas[5 + 2 * i : 7 + 2 * i]) for i in range(k))
    return Situacion(tuple(cartas[:5]), manos)


def generar_situacion(rng: random.Random, pesos: dict[str, float] | None = None) -> Situacion:
    """Genera una situación; con pesos, sesga hacia categorías ganadoras débiles.

    Muestreo por rechazo: acepta una candidata con probabilidad proporcional a
    peso(categoría ganadora). Tras INTENTOS_PONDERACION intentos devuelve la
    última (el sesgo es preferencia, no garantía).
    """
    if not pesos:
        return _candidata(rng)
    tope = max(max(pesos.values()), PESO_SIN_DATOS)
    for _ in range(INTENTOS_PONDERACION):
        candidata = _candidata(rng)
        peso = pesos.get(candidata.categoria_ganadora, PESO_SIN_DATOS)
        if rng.random() < peso / tope:
            return candidata
    return candidata


def feedback(resultado: Resultado) -> str:
    s = resultado.situacion
    veredicto = "✓ Correcto" if resultado.acierto else "✗ Incorrecto"
    if s.correcta == "e":
        empatadas = " y ".join(str(i + 1) for i in s.ganadores)
        titulo = f"{veredicto}: empatan las manos {empatadas}."
    else:
        titulo = f"{veredicto}: gana la mano {s.correcta} con {s.categoria_ganadora}."
    lineas = [titulo]
    for i, (puntos, cinco) in enumerate(s.evaluaciones):
        mano = " ".join(str(c) for c in s.manos[i])
        mejor = " ".join(str(c) for c in cinco)
        lineas.append(f"  Mano {i + 1} ({mano}): {NOMBRES[puntos[0]]} — mejor 5: {mejor}")
    return "\n".join(lineas)
