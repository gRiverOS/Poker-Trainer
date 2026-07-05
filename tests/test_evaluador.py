"""Tests de regresión del evaluador de manos.

F0: solo verifica que el cableado del proyecto funciona (import + pytest).
Los casos de regresión reales llegan en F1 junto con la implementación.
"""

from src import cartas, evaluador


def test_esqueleto_importable():
    assert cartas is not None
    assert evaluador is not None
