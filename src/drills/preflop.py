"""D1 — Preflop por posición: RFI y defensa de BB.

Dos escenarios:
- RFI (abridor=None): nadie abrió, estás en UTG..SB — ¿open o fold?
- Defensa (abridor=posición): estás en BB y alguien abrió — ¿fold, call o 3-bet?

Lógica pura del drill: generar situaciones, decidir la acción correcta según
los charts y armar feedback + tip. La interacción (input/print) vive en
trainer.py. Los tips se construyen solo con hechos de los charts (trazables).
"""

import random
from dataclasses import dataclass

from src.cartas import Carta, mazo
from src.progreso import PESO_SIN_DATOS
from src.rangos import ORDEN_LETRAS, POSICIONES_RFI, notacion

ACCIONES_RFI = ("open", "fold")
ACCIONES_DEFENSA = ("3bet", "call", "fold")
# categorías del drill: 5 posiciones RFI + 5 defensas de BB
ESCENARIOS = tuple(POSICIONES_RFI) + tuple(f"BB vs {p}" for p in POSICIONES_RFI)


@dataclass(frozen=True)
class Situacion:
    posicion: str
    mano: tuple[Carta, Carta]
    abridor: str | None = None  # posición que abrió (escenario defensa de BB)

    @property
    def notacion(self) -> str:
        return notacion(*self.mano)

    @property
    def es_defensa(self) -> bool:
        return self.abridor is not None


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
        s = self.situacion
        return f"BB vs {s.abridor}" if s.es_defensa else s.posicion

    @property
    def contexto(self) -> str:
        return self.categoria

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
    """Genera RFI o defensa de BB; los escenarios donde más fallas salen más."""
    pesos = pesos or {}
    ponderaciones = [pesos.get(e, PESO_SIN_DATOS) for e in ESCENARIOS]
    escenario = rng.choices(ESCENARIOS, weights=ponderaciones)[0]
    c1, c2 = rng.sample(mazo(), 2)
    if escenario.startswith("BB vs "):
        return Situacion("BB", (c1, c2), abridor=escenario.removeprefix("BB vs "))
    return Situacion(escenario, (c1, c2))


def accion_correcta(situacion: Situacion, rfi: dict, defensa_bb: dict | None = None) -> str:
    if situacion.es_defensa:
        entrada = defensa_bb[situacion.abridor]
        if situacion.notacion in entrada["3bet"]["manos"]:
            return "3bet"
        if situacion.notacion in entrada["call"]["manos"]:
            return "call"
        return "fold"
    return "open" if situacion.notacion in rfi[situacion.posicion]["manos"] else "fold"


# --- Tips: explicación corta construida desde los charts ---


def _minimo_kicker(manos: set[str], alta: str, sufijo: str) -> str | None:
    """Kicker más bajo con que la carta alta aparece en el set: (J, o) → "9" si hay J9o+."""
    for letra in ORDEN_LETRAS[: ORDEN_LETRAS.index(alta)]:
        if f"{alta}{letra}{sufijo}" in manos:
            return letra
    return None


def _posiciones_que_abren(nota: str, chart: dict) -> list[str]:
    return [p for p in POSICIONES_RFI if nota in chart[p]["manos"]]


def _es_premium(nota: str) -> bool:
    """Mano de valor claro: pareja TT+ o dos cartas T o mayores."""
    if len(nota) == 2:
        return ORDEN_LETRAS.index(nota[0]) >= ORDEN_LETRAS.index("T")
    return all(ORDEN_LETRAS.index(c) >= ORDEN_LETRAS.index("T") for c in nota[:2])


def _tipo(sufijo: str) -> str:
    return "suited" if sufijo == "s" else "offsuit"


def tip_rfi(situacion: Situacion, chart: dict) -> str:
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
        borde = f" El mínimo con {alta} {_tipo(sufijo)} en {pos} es {alta}{minimo}{sufijo}." if minimo else ""
        return f"{nota} se abre en {pos}: {motivo}.{borde}"

    partes = []
    if not es_pareja:
        minimo = _minimo_kicker(manos, alta, sufijo)
        if minimo:
            partes.append(f"en {pos} el mínimo con {alta} {_tipo(sufijo)} es {alta}{minimo}{sufijo} y tu kicker no llega")
        else:
            partes.append(f"en {pos} ninguna mano de {alta} alta {_tipo(sufijo)} se abre")
        if sufijo == "o" and f"{nota[:2]}s" in manos:
            partes.append(f"la versión suited ({nota[:2]}s) sí se abre: los palos compartidos suman equity")
    if abren:
        partes.append(f"{nota} se abre recién desde {abren[0]}")
    else:
        partes.append(f"{nota} no se abre desde ninguna posición")
    return f"{nota} va al fold: " + "; ".join(partes) + "."


def tip_defensa(situacion: Situacion, defensa_bb: dict) -> str:
    nota, abridor = situacion.notacion, situacion.abridor
    entrada = defensa_bb[abridor]
    tres, pagar = entrada["3bet"]["manos"], entrada["call"]["manos"]

    if nota in tres:
        if _es_premium(nota):
            return (
                f"{nota} se 3betea de valor vs {abridor}: con una mano premium quieres "
                f"inflar el pozo de inmediato — solo pagar la desperdicia en un pozo chico."
            )
        return (
            f"{nota} se 3betea como bluff vs {abridor}: no es premium, pero bloquea "
            f"manos fuertes del rival y juega bien si te pagan. Mezclar bluffs hace "
            f"que tus 3-bets de valor cobren."
        )
    if nota in pagar:
        return (
            f"{nota} paga vs {abridor}: con 1bb ya invertido el call sale con descuento "
            f"y cierras la acción — por eso la BB defiende mucho más ancho que las demás posiciones."
        )
    partes = [f"ni con descuento alcanza vs open de {abridor}"]
    if len(nota) == 3:
        alta, sufijo = nota[0], nota[2]
        minimo = _minimo_kicker(tres | pagar, alta, sufijo)
        if minimo:
            partes.append(f"el mínimo con {alta} {_tipo(sufijo)} que se defiende es {alta}{minimo}{sufijo}")
    defendida_vs = [p for p in POSICIONES_RFI if nota in defensa_bb[p]["3bet"]["manos"] | defensa_bb[p]["call"]["manos"]]
    if defendida_vs:
        partes.append(f"vs un open de {defendida_vs[0]} sí se defendería")
    else:
        partes.append("no se defiende contra ningún open")
    return f"{nota} va al fold: " + "; ".join(partes) + "."


def feedback(resultado: Resultado, rfi: dict, defensa_bb: dict | None = None) -> str:
    s = resultado.situacion
    veredicto = "✓ Correcto" if resultado.acierto else "✗ Incorrecto"
    # jerarquía: veredicto → tip (si hubo error) → evidencia de los charts
    if s.es_defensa:
        entrada = defensa_bb[s.abridor]
        accion = {"3bet": "se 3betea", "call": "se paga", "fold": "se bota"}[resultado.correcta]
        lineas = [f"{veredicto}: {s.notacion} {accion} desde BB contra un open de {s.abridor}."]
        if not resultado.acierto:
            lineas.append(f"Tip: {tip_defensa(s, defensa_bb)}")
        lineas += [
            f"3-bet BB vs {s.abridor}: {entrada['3bet']['rango']}",
            f"Call  BB vs {s.abridor}: {entrada['call']['rango']}",
        ]
    else:
        entrada = rfi[s.posicion]
        dentro = "está en" if resultado.correcta == "open" else "no está en"
        lineas = [f"{veredicto}: {s.notacion} {dentro} el rango de open de {s.posicion}."]
        if not resultado.acierto:
            lineas.append(f"Tip: {tip_rfi(s, rfi)}")
        lineas.append(f"Rango {s.posicion}: {entrada['rango']}")
    return "\n".join(lineas)