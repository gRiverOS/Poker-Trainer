"""Carta, mazo y parsing de notación tipo "Ah Kd".

Base compartida por el evaluador y los drills. Notación estándar de poker:
valores 2-9, T, J, Q, K, A; palos s (picas), h (corazones), d (diamantes),
c (tréboles). El as vale 14 (la rueda A-5 la maneja el evaluador).
"""

from dataclasses import dataclass

VALOR_DE = {letra: valor for valor, letra in enumerate("23456789TJQKA", start=2)}
LETRA_DE = {valor: letra for letra, valor in VALOR_DE.items()}
PALOS = "shdc"


@dataclass(frozen=True, order=True)
class Carta:
    valor: int  # 2..14 (as = 14)
    palo: str  # 's', 'h', 'd' o 'c'

    def __str__(self) -> str:
        return f"{LETRA_DE[self.valor]}{self.palo}"


def carta(texto: str) -> Carta:
    """Parsea una carta: "Ah" → Carta(14, 'h'). Acepta "AH", "ah", etc."""
    texto = texto.strip()
    if len(texto) != 2:
        raise ValueError(f"Carta inválida: {texto!r} (formato esperado: 'Ah', 'Td', '9c')")
    letra, palo = texto[0].upper(), texto[1].lower()
    if letra not in VALOR_DE:
        raise ValueError(f"Valor inválido en {texto!r}: use 2-9, T, J, Q, K o A")
    if palo not in PALOS:
        raise ValueError(f"Palo inválido en {texto!r}: use s, h, d o c")
    return Carta(VALOR_DE[letra], palo)


def cartas(texto: str) -> list[Carta]:
    """Parsea varias cartas separadas por espacios: "Ah Kd" → [Carta, Carta]."""
    resultado = [carta(pedazo) for pedazo in texto.split()]
    if len(set(resultado)) != len(resultado):
        raise ValueError(f"Cartas repetidas en {texto!r}")
    return resultado


def mazo() -> list[Carta]:
    """Mazo nuevo de 52 cartas, sin barajar (barajar es problema del que reparte)."""
    return [Carta(valor, palo) for valor in range(2, 15) for palo in PALOS]
