"""D2 — Pot odds y equity rápida.

Situación: pot, apuesta del rival a pagar, tu mano y el board (flop o turn).
Estimas tu equity (p. ej. con la regla del 4 y 2 contando tus outs) y decides
call o fold. El motor calcula la equity real (Monte Carlo contra mano
aleatoria) y te muestra el error de tu estimación y si tu decisión fue
rentable según las pot odds.

Zona gris: si la equity real queda a menos de ZONA_GRIS puntos de la equity
necesaria, la decisión es demasiado justa para corregirla (además el Monte
Carlo tiene ruido de ~±1 punto) — cualquier respuesta cuenta como acierto.
"""

import random
from dataclasses import dataclass

from src.cartas import Carta, mazo
from src.equity import equity_necesaria
from src.progreso import PESO_SIN_DATOS

POTS_BB = (4, 6, 8, 10, 15, 20)
FRACCIONES = (1 / 3, 1 / 2, 2 / 3, 1)
ZONA_GRIS = 2.0  # puntos porcentuales


@dataclass(frozen=True)
class Situacion:
    mano: tuple[Carta, Carta]
    board: tuple[Carta, ...]
    pot: float  # en bb, antes de la apuesta del rival
    apuesta: float  # en bb

    @property
    def calle(self) -> str:
        return "flop" if len(self.board) == 3 else "turn"

    @property
    def necesaria(self) -> float:
        """Equity necesaria para el call, en porcentaje."""
        return 100 * equity_necesaria(self.pot, self.apuesta)


@dataclass(frozen=True)
class Resultado:
    situacion: Situacion
    decision: str  # "call" | "fold"
    equity_real: float  # en porcentaje
    estimacion: float | None = None  # en porcentaje, opcional

    @property
    def correcta(self) -> str | None:
        """Decisión rentable, o None si el spot cae en la zona gris."""
        margen = self.equity_real - self.situacion.necesaria
        if abs(margen) < ZONA_GRIS:
            return None
        return "call" if margen > 0 else "fold"

    @property
    def acierto(self) -> bool:
        return self.correcta is None or self.decision == self.correcta

    @property
    def error_estimacion(self) -> float | None:
        if self.estimacion is None:
            return None
        return abs(self.estimacion - self.equity_real)

    # --- interfaz común de progreso ---

    @property
    def categoria(self) -> str:
        return self.situacion.calle

    @property
    def contexto(self) -> str:
        return f"{self.situacion.calle} pot={self.situacion.pot} apuesta={self.situacion.apuesta}"

    @property
    def mano_texto(self) -> str:
        mano = " ".join(str(c) for c in self.situacion.mano)
        board = " ".join(str(c) for c in self.situacion.board)
        return f"{mano} | {board}"

    @property
    def respuesta_texto(self) -> str:
        est = f" est={self.estimacion:g}%" if self.estimacion is not None else ""
        return f"{self.decision}{est}"

    @property
    def correcta_texto(self) -> str:
        return self.correcta or "limite"


def generar_situacion(rng: random.Random, pesos: dict[str, float] | None = None) -> Situacion:
    """Genera una situación; con pesos, la calle donde más fallas sale más."""
    if pesos:
        ponderaciones = [pesos.get(c, PESO_SIN_DATOS) for c in ("flop", "turn")]
        cuantas_board = rng.choices((3, 4), weights=ponderaciones)[0]
    else:
        cuantas_board = rng.choice((3, 4))
    cartas = rng.sample(mazo(), 2 + cuantas_board)
    pot = float(rng.choice(POTS_BB))
    apuesta = round(pot * rng.choice(FRACCIONES), 1)
    return Situacion(tuple(cartas[:2]), tuple(cartas[2:]), pot, apuesta)


def feedback(resultado: Resultado) -> str:
    s = resultado.situacion
    lineas = []
    veredicto = "✓ Correcto" if resultado.acierto else "✗ Incorrecto"
    if resultado.correcta is None:
        veredicto += " (spot al límite: cualquier decisión vale)"
    lineas.append(
        f"{veredicto}: equity real {resultado.equity_real:.1f}% vs "
        f"{s.necesaria:.1f}% necesaria (pot {s.pot:g}bb + apuesta {s.apuesta:g}bb)."
    )
    if resultado.error_estimacion is not None:
        lineas.append(
            f"  Tu estimación: {resultado.estimacion:g}% — error de {resultado.error_estimacion:.1f} puntos."
        )
    return "\n".join(lineas)
