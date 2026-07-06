"""Tests de rangos.py: notación 169, expansión de tokens y carga del chart RFI."""

import pytest

from src.cartas import carta
from src.rangos import POSICIONES_RFI, cargar_defensa_bb, cargar_rfi, combos, expandir, notacion


# --- Notación de dos cartas ---


def test_notacion_pareja():
    assert notacion(carta("7s"), carta("7d")) == "77"


def test_notacion_suited_y_offsuit():
    assert notacion(carta("Ah"), carta("Kh")) == "AKs"
    assert notacion(carta("Ah"), carta("Kd")) == "AKo"


def test_notacion_ordena_la_alta_primero():
    assert notacion(carta("9c"), carta("Ts")) == "T9o"
    assert notacion(carta("2h"), carta("Ah")) == "A2s"


# --- Expansión de tokens ---


def test_expandir_pareja_con_plus():
    assert expandir("JJ+") == {"JJ", "QQ", "KK", "AA"}
    assert len(expandir("22+")) == 13


def test_expandir_pareja_sola():
    assert expandir("TT") == {"TT"}


def test_expandir_suited_con_plus():
    assert expandir("ATs+") == {"ATs", "AJs", "AQs", "AKs"}
    assert len(expandir("A2s+")) == 12  # A2s..AKs


def test_expandir_offsuit_con_plus():
    assert expandir("K7o+") == {"K7o", "K8o", "K9o", "KTo", "KJo", "KQo"}


def test_expandir_mano_exacta():
    assert expandir("T9s") == {"T9s"}
    assert expandir("54s") == {"54s"}


def test_expandir_rango_compuesto():
    manos = expandir("22+, ATs+, KQo")
    assert manos == expandir("22+") | expandir("ATs+") | {"KQo"}


def test_expandir_guion_parejas():
    assert expandir("22-99") == expandir("22+") - expandir("TT+")


def test_expandir_guion_kickers():
    assert expandir("A6s-A9s") == {"A6s", "A7s", "A8s", "A9s"}
    assert expandir("K9o-KJo") == {"K9o", "KTo", "KJo"}


def test_expandir_guion_acepta_ambos_ordenes():
    # la convención de los charts escribe descendente: A5s-A2s
    assert expandir("A5s-A2s") == expandir("A2s-A5s") == {"A2s", "A3s", "A4s", "A5s"}
    assert expandir("99-22") == expandir("22-99")


@pytest.mark.parametrize("token", ["", "A", "AK", "KAs", "A1s+", "Axo", "22s", "TT-", "A2s-K9s", "AKs-AAs"])
def test_tokens_invalidos(token):
    with pytest.raises(ValueError):
        expandir(token)


def test_combos():
    assert combos({"AA"}) == 6
    assert combos({"AKs"}) == 4
    assert combos({"AKo"}) == 12
    assert combos(expandir("22+")) == 78


# --- Carga del chart RFI real ---


def test_chart_rfi_carga_las_5_posiciones():
    chart = cargar_rfi()
    assert set(chart) == set(POSICIONES_RFI)
    assert all(chart[p]["manos"] for p in POSICIONES_RFI)
    assert all("preflopwizard" in chart[p]["fuente"] for p in POSICIONES_RFI)


def test_chart_rfi_se_ensancha_hacia_el_boton():
    chart = cargar_rfi()
    tamanos = [combos(chart[p]["manos"]) for p in ("UTG", "MP", "CO", "BTN")]
    assert tamanos == sorted(tamanos) and len(set(tamanos)) == 4


def test_chart_rfi_casos_conocidos():
    chart = cargar_rfi()
    assert "AA" in chart["UTG"]["manos"]  # AA se abre desde todos lados
    assert "72o" not in chart["BTN"]["manos"]  # la peor mano no se abre ni en BTN
    assert "A2o" in chart["BTN"]["manos"]  # BTN abre cualquier as
    assert "A2o" not in chart["CO"]["manos"]


# --- Chart de defensa de BB ---


def test_defensa_bb_carga_los_5_abridores():
    chart = cargar_defensa_bb()
    assert set(chart) == set(POSICIONES_RFI)
    for abridor in POSICIONES_RFI:
        assert chart[abridor]["3bet"]["manos"] and chart[abridor]["call"]["manos"]


def test_defensa_bb_3bet_y_call_no_se_pisan():
    chart = cargar_defensa_bb()
    for abridor in POSICIONES_RFI:
        assert not chart[abridor]["3bet"]["manos"] & chart[abridor]["call"]["manos"]


def test_defensa_bb_se_ensancha_contra_opens_tardios():
    chart = cargar_defensa_bb()

    def defensa_total(abridor):
        return combos(chart[abridor]["3bet"]["manos"] | chart[abridor]["call"]["manos"])

    tamanos = [defensa_total(p) for p in ("UTG", "MP", "CO", "BTN")]
    assert tamanos == sorted(tamanos) and len(set(tamanos)) == 4
    assert defensa_total("SB") > defensa_total("CO")  # BvB se defiende ancho
