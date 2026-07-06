"""D1 — Preflop por posición (escenario RFI: nadie abrió, ¿open o fold?).

Lógica pura del drill: generar situaciones, decidir la acción correcta según
el chart y armar el feedback. La interacción (input/print) vive en trainer.py.

Alcance MVP: solo RFI. Enfrentar un open (call/3-bet) requiere charts por par
de posiciones y queda como extensión de D1.
"""

import random
from dataclasses import dataclass

from src.cartas import Carta, mazo
from src.rangos import POSICIONES_RFI, notacion

ACCIONES = ("open", "fold")


@dataclass(frozen=True)
class Situacion:
    posicion: str
    mano: tuple[Carta, Carta]

    @property
    def notacion(self) -> str:
        return notacion(*self.mano)


@dataclass(frozen=True)
class Resultado:
    situacion: Situacion
    respuesta: str
    correcta: str

    @property
    def acierto(self) -> bool:
        return self.respuesta == self.correcta

    # --- interfaz común de progreso ---

    @property
    def categoria(self) -> str:
        return self.situacion.posicion

    @property
    def contexto(self) -> str:
        return self.situacion.posicion

    @property
    def mano_texto(self) -> str:
        return self.situacion.notacion

    @property
    def respuesta_texto(self) -> str:
        return self.respuesta

    @property
    def correcta_texto(self) -> str:
        return self.correcta


def generar_situacion(rng: random.Random) -> Situacion:
    posicion = rng.choice(POSICIONES_RFI)
    c1, c2 = rng.sample(mazo(), 2)
    return Situacion(posicion, (c1, c2))


def accion_correcta(situacion: Situacion, chart: dict) -> str:
    en_rango = situacion.notacion in chart[situacion.posicion]["manos"]
    return "open" if en_rango else "fold"


def feedback(resultado: Resultado, chart: dict) -> str:
    s = resultado.situacion
    entrada = chart[s.posicion]
    veredicto = "✓ Correcto" if resultado.acierto else "✗ Incorrecto"
    dentro = "está en" if resultado.correcta == "open" else "no está en"
    return (
        f"{veredicto}: {s.notacion} {dentro} el rango de open de {s.posicion}.\n"
        f"  Rango {s.posicion}: {entrada['rango']}"
    )
