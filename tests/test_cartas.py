"""Tests de cartas.py: parsing, mazo e igualdad."""

import pytest

from src.cartas import Carta, carta, cartas, mazo


def test_parsing_basico():
    assert carta("Ah") == Carta(14, "h")
    assert carta("Td") == Carta(10, "d")
    assert carta("2c") == Carta(2, "c")


def test_parsing_tolerante_a_mayusculas():
    assert carta("AH") == carta("ah") == carta("Ah")


def test_parsing_varias():
    assert cartas("Ah Kd") == [Carta(14, "h"), Carta(13, "d")]


@pytest.mark.parametrize("texto", ["", "A", "10h", "Ax", "1h", "Ahh"])
def test_parsing_invalido(texto):
    with pytest.raises(ValueError):
        carta(texto)


def test_cartas_repetidas():
    with pytest.raises(ValueError, match="repetidas"):
        cartas("Ah Kd Ah")


def test_mazo_completo():
    m = mazo()
    assert len(m) == 52
    assert len(set(m)) == 52  # sin duplicados


def test_str_roundtrip():
    assert all(carta(str(c)) == c for c in mazo())
