"""Carga de charts preflop desde data/rangos_preflop/ y notación de rangos.

Los rangos son datos editables, nunca hardcodeados. La notación es la estándar
de charts: "TT" (pareja), "22+" (pareja y mejores), "AKs"/"AJo" (mano exacta
suited/offsuit), "ATs+"/"K7o+" (primera carta fija, kicker desde ahí hacia
arriba). Una mano de 169 se escribe con la carta alta primero: "AKs", "T9o".
"""

import json
from pathlib import Path

from src.cartas import LETRA_DE, Carta

ORDEN_LETRAS = "23456789TJQKA"
RUTA_RFI = Path(__file__).parent.parent / "data" / "rangos_preflop" / "rfi_cash_6max_100bb.json"
POSICIONES_RFI = ("UTG", "MP", "CO", "BTN", "SB")  # BB no decide en pot no abierto


def notacion(c1: Carta, c2: Carta) -> str:
    """Notación 169 de dos cartas: (Ah, Kh) → "AKs", (Ah, Kd) → "AKo", (7s, 7d) → "77"."""
    alta, baja = (c1, c2) if c1.valor >= c2.valor else (c2, c1)
    letras = f"{LETRA_DE[alta.valor]}{LETRA_DE[baja.valor]}"
    if alta.valor == baja.valor:
        return letras
    return letras + ("s" if alta.palo == baja.palo else "o")


def _expandir_token(token: str) -> set[str]:
    plus = token.endswith("+")
    cuerpo = token.rstrip("+")

    if len(cuerpo) == 2 and cuerpo[0] == cuerpo[1]:  # pareja: "TT" o "22+"
        if cuerpo[0] not in ORDEN_LETRAS:
            raise ValueError(f"Token de rango inválido: {token!r}")
        desde = ORDEN_LETRAS.index(cuerpo[0])
        hasta = len(ORDEN_LETRAS) if plus else desde + 1
        return {ORDEN_LETRAS[i] * 2 for i in range(desde, hasta)}

    if len(cuerpo) == 3 and cuerpo[2] in "so":  # no-pareja: "AJo", "ATs+"
        alta, baja, sufijo = cuerpo[0], cuerpo[1], cuerpo[2]
        if alta not in ORDEN_LETRAS or baja not in ORDEN_LETRAS:
            raise ValueError(f"Token de rango inválido: {token!r}")
        i_alta, i_baja = ORDEN_LETRAS.index(alta), ORDEN_LETRAS.index(baja)
        if i_baja >= i_alta:
            raise ValueError(f"Token de rango inválido: {token!r} (carta alta va primero)")
        hasta = i_alta if plus else i_baja + 1
        return {f"{alta}{ORDEN_LETRAS[i]}{sufijo}" for i in range(i_baja, hasta)}

    raise ValueError(f"Token de rango inválido: {token!r}")


def expandir(rango: str) -> set[str]:
    """Expande un rango en notación de chart a su set de manos de 169.

    "22+, ATs+, KQo" → {"22", ..., "AA", "ATs", ..., "AKs", "KQo"}
    """
    tokens = rango.replace(",", " ").split()
    if not tokens:
        raise ValueError("Rango vacío")
    manos: set[str] = set()
    for token in tokens:
        manos |= _expandir_token(token)
    return manos


def combos(manos: set[str]) -> int:
    """Cantidad de combinaciones concretas: pareja=6, suited=4, offsuit=12."""
    return sum(6 if len(m) == 2 else 4 if m[2] == "s" else 12 for m in manos)


def cargar_rfi(ruta: Path = RUTA_RFI) -> dict:
    """Carga el chart RFI: {posición: {"rango": str, "manos": set, "fuente": str}}."""
    datos = json.loads(ruta.read_text())
    fuente = datos["fuente"]
    chart = {}
    for posicion, info in datos["rangos_open"].items():
        chart[posicion] = {
            "rango": info["rango"],
            "manos": expandir(info["rango"]),
            "fuente": fuente,
        }
    faltantes = set(POSICIONES_RFI) - set(chart)
    if faltantes:
        raise ValueError(f"Chart RFI incompleto, faltan posiciones: {sorted(faltantes)}")
    return chart
