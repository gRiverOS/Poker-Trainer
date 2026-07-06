"""D1 — Preflop por posición (escenario RFI: nadie abrió, ¿open o fold?).

Lógica pura del drill: generar situaciones, decidir la acción correcta según
el chart y armar el feedback. La interacción (input/print) vive en trainer.py.

Alcance MVP: solo RFI. Enfrentar un open (call/3-bet) requiere charts por par
de posiciones y queda como extensión de D1.
"""

import random
from dataclasses import dataclass

from src.cartas import Carta, mazo
from src.progreso import PESO_SIN_DATOS
from src.rangos import ORDEN_LETRAS, POSICIONES_RFI, notacion

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


def generar_situacion(rng: random.Random, pesos: dict[str, float] | None = None) -> Situacion:
    """Genera una situación; con pesos, las posiciones donde más fallas salen más."""
    if pesos:
        ponderaciones = [pesos.get(p, PESO_SIN_DATOS) for p in POSICIONES_RFI]
        posicion = rng.choices(POSICIONES_RFI, weights=ponderaciones)[0]
    else:
        posicion = rng.choice(POSICIONES_RFI)
    c1, c2 = rng.sample(mazo(), 2)
    return Situacion(posicion, (c1, c2))


def accion_correcta(situacion: Situacion, chart: dict) -> str:
    en_rango = situacion.notacion in chart[situacion.posicion]["manos"]
    return "open" if en_rango else "fold"


def _minimo_kicker(manos: set[str], alta: str, sufijo: str) -> str | None:
    """Kicker más bajo con que la carta alta aparece en el rango: (J, o) → "9" si hay J9o+."""
    for letra in ORDEN_LETRAS[: ORDEN_LETRAS.index(alta)]:
        if f"{alta}{letra}{sufijo}" in manos:
            return letra
    return None


def _posiciones_que_abren(nota: str, chart: dict) -> list[str]:
    return [p for p in POSICIONES_RFI if nota in chart[p]["manos"]]


def tip(situacion: Situacion, chart: dict) -> str:
    """Explicación corta (un tuit) de por qué la acción correcta es la correcta.

    Construida solo con hechos del chart: mínimos por kicker, desde qué
    posición se abre la mano y la diferencia suited/offsuit.
    """
    nota, pos = situacion.notacion, situacion.posicion
    manos = chart[pos]["manos"]
    abren = _posiciones_que_abren(nota, chart)
    es_pareja = len(nota) == 2
    alta, sufijo = nota[0], nota[-1]

    if nota in manos:  # la correcta era open
        if es_pareja:
            motivo = "las parejas se abren desde cualquier posición: cualquier flop puede regalarte un set"
        elif sufijo == "s" and abs(ORDEN_LETRAS.index(nota[0]) - ORDEN_LETRAS.index(nota[1])) <= 2:
            motivo = "suited y conectada arma escaleras y colores: juega bien postflop"
        elif sufijo == "s":
            motivo = "los palos compartidos suman proyectos de color y eso la mete al rango"
        else:
            motivo = "dos cartas que dominan a las manos peores que te pagarían"
        minimo = None if es_pareja else _minimo_kicker(manos, alta, sufijo)
        borde = f" El mínimo con {alta} {'suited' if sufijo == 's' else 'offsuit'} en {pos} es {alta}{minimo}{sufijo}." if minimo else ""
        return f"{nota} se abre en {pos}: {motivo}.{borde}"

    # la correcta era fold
    partes = []
    if not es_pareja:
        minimo = _minimo_kicker(manos, alta, sufijo)
        if minimo:
            partes.append(f"en {pos} el mínimo con {alta} {'suited' if sufijo == 's' else 'offsuit'} es {alta}{minimo}{sufijo} y tu kicker no llega")
        else:
            partes.append(f"en {pos} ninguna mano de {alta} alta {'suited' if sufijo == 's' else 'offsuit'} se abre")
        if sufijo == "o" and f"{nota[:2]}s" in manos:
            partes.append(f"la versión suited ({nota[:2]}s) sí se abre: los palos compartidos suman equity")
    if abren:
        partes.append(f"{nota} se abre recién desde {abren[0]}")
    else:
        partes.append(f"{nota} no se abre desde ninguna posición")
    return f"{nota} va al fold: " + "; ".join(partes) + "."


def feedback(resultado: Resultado, chart: dict) -> str:
    s = resultado.situacion
    entrada = chart[s.posicion]
    veredicto = "✓ Correcto" if resultado.acierto else "✗ Incorrecto"
    dentro = "está en" if resultado.correcta == "open" else "no está en"
    lineas = [
        f"{veredicto}: {s.notacion} {dentro} el rango de open de {s.posicion}.",
        f"  Rango {s.posicion}: {entrada['rango']}",
    ]
    if not resultado.acierto:
        lineas.append(f"  Tip: {tip(s, chart)}")
    return "\n".join(lineas)
