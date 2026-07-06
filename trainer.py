"""CLI del entrenador: `uv run trainer.py --drill preflop [--n 10] [--semilla 42]`.

Capa de presentación. Sistema visual:
- Jerarquía: veredicto (color) > tip (normal) > evidencia de charts (gris dim).
- Mazo clásico de 2 colores: ♥♦ rojos, ♠♣ neutros.
- Layout: situación sin sangría, detalle y feedback con sangría de 2,
  ayuda de input siempre [x/y/z] de menor a mayor agresión.
- ANSI solo si stdout es un terminal y NO_COLOR no está seteado.
"""

import argparse
import os
import random
import sys
from pathlib import Path

from src import progreso
from src.drills import lectura, pot_odds, preflop
from src.equity import equity_monte_carlo
from src.rangos import POSICIONES_RFI, cargar_defensa_bb, cargar_rfi, combos

DRILLS = ("preflop", "pot_odds", "lectura")

USA_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
VERDE = "\033[1;32m"
GRIS = "\033[90m"
RESET = "\033[0m"
PALO_COLOR = {"s": "", "h": "31", "d": "31", "c": ""}  # mazo clásico: ♥♦ rojos, ♠♣ neutros


def _c(codigo: str, texto: str) -> str:
    return f"\033[{codigo}m{texto}{RESET}" if USA_COLOR and codigo else texto


def _mano(cartas_) -> str:
    """Cartas para pantalla, mazo clásico: ♥♦ en rojo, ♠♣ sin color."""
    return " ".join(_c(PALO_COLOR[c.palo], c.bonita) for c in cartas_)


def _pintar_linea(linea: str) -> str:
    """Aplica la jerarquía visual a una línea de feedback de los drills."""
    if linea.startswith(("Rango ", "3-bet ", "Call ", "Mano ")):
        return _c("90", linea)  # evidencia: atenuada
    if linea.startswith("✓"):
        linea = _c("32", "✓ Correcto") + linea[len("✓ Correcto") :]
    elif linea.startswith("✗"):
        linea = _c("31", "✗ Incorrecto") + linea[len("✗ Incorrecto") :]
    limite = "(spot al límite: cualquier decisión vale)"
    if limite in linea:
        linea = linea.replace(limite, _c("33", limite))
    return linea


def _imprimir_feedback(texto: str) -> None:
    for linea in texto.splitlines():
        print(f"  {_pintar_linea(linea.strip())}")
    print()


def _pct_color(pct: float) -> str:
    codigo = "32" if pct >= 80 else "33" if pct >= 50 else "31"
    return _c(codigo, f"{pct:g}%")


def _leer(prompt: str) -> str | None:
    """input() que devuelve None si la sesión se corta (EOF o 'q')."""
    try:
        texto = input(prompt).strip().lower()
    except EOFError:
        print()
        return None
    return None if texto == "q" else texto


def _situaciones(n: int) -> str:
    return "1 situación" if n == 1 else f"{n} situaciones"


def _cerrar_sesion(resultados, drill: str, extra: str = "") -> None:
    if not resultados:
        print("Sesión vacía, nada que guardar.")
        return
    r = progreso.resumen(resultados)
    print(f"— Resumen: {r['aciertos']}/{r['total']} aciertos ({_pct_color(r['pct'])}){extra}")
    ancho = max(len(cat) for cat in r["por_categoria"])
    for cat, d in r["por_categoria"].items():
        print(f"  {cat:<{ancho}}  {d['aciertos']}/{d['total']}  {_pct_color(d['pct'])}")
    progreso.registrar(resultados, drill=drill)
    try:
        ruta = progreso.RUTA_HISTORIAL.relative_to(Path.cwd())
    except ValueError:
        ruta = progreso.RUTA_HISTORIAL
    print(f"Historial actualizado: {ruta}")


def sesion_preflop(n: int, rng: random.Random) -> None:
    rfi = cargar_rfi()
    defensa = cargar_defensa_bb()
    pesos = progreso.cargar_pesos("preflop")
    resultados = []
    print(
        f"D1 — Preflop (cash 6-max 100bb). {_situaciones(n)}, dos escenarios mezclados:\n"
        "  · RFI (nadie abrió): [f/o] fold u open\n"
        "  · Defensa de BB (alguien abrió ~2.5bb): [f/c/3] fold, call o 3-bet\n"
        "  'q' para salir.\n"
    )

    for i in range(1, n + 1):
        s = preflop.generar_situacion(rng, pesos)
        if s.es_defensa:
            prompt = f"[{i}/{n}] BB vs open de {s.abridor} — {_mano(s.mano)} ({s.notacion}) [f/c/3]: "
            mapa = {"f": "fold", "c": "call", "3": "3bet", "r": "3bet"}
        else:
            prompt = f"[{i}/{n}] {s.posicion} — {_mano(s.mano)} ({s.notacion}) [f/o]: "
            mapa = {"f": "fold", "o": "open"}
        respuesta = _leer(prompt)
        if respuesta is None:
            break
        if respuesta not in mapa:
            print(f"  Respuesta inválida, situación saltada (usa {'/'.join(sorted(set(mapa)))} o 'q').\n")
            continue
        resultado = preflop.Resultado(s, mapa[respuesta], preflop.accion_correcta(s, rfi, defensa))
        resultados.append(resultado)
        _imprimir_feedback(preflop.feedback(resultado, rfi, defensa))

    _cerrar_sesion(resultados, drill="preflop")


def sesion_pot_odds(n: int, rng: random.Random) -> None:
    pesos = progreso.cargar_pesos("pot_odds")
    resultados = []
    print(
        f"D2 — Pot odds y equity (heads-up vs mano aleatoria). {_situaciones(n)}.\n"
        "  Estima tu equity (%, enter para saltar) y decide [f/c] fold o call. 'q' para salir.\n"
    )

    for i in range(1, n + 1):
        s = pot_odds.generar_situacion(rng, pesos)
        print(f"[{i}/{n}] {s.calle} — tu mano {_mano(s.mano)} · board {_mano(s.board)}")
        print(f"  pot {s.pot:g}bb, el rival apuesta {s.apuesta:g}bb")

        estimacion_texto = _leer("  tu equity estimada (%): ")
        if estimacion_texto is None:
            break
        estimacion = None
        if estimacion_texto:
            try:
                estimacion = float(estimacion_texto.replace("%", "").replace(",", "."))
            except ValueError:
                print("  Estimación ilegible, la salto.")

        decision = _leer("  ¿pagas? [f/c]: ")
        if decision is None:
            break
        if decision not in ("c", "f"):
            print("  Respuesta inválida, situación saltada.\n")
            continue

        equity_real = 100 * equity_monte_carlo(s.mano, s.board, n=10_000, rng=rng)
        resultado = pot_odds.Resultado(s, "call" if decision == "c" else "fold", equity_real, estimacion)
        resultados.append(resultado)
        _imprimir_feedback(pot_odds.feedback(resultado))

    errores = [r.error_estimacion for r in resultados if r.error_estimacion is not None]
    extra = f" — error medio de estimación: {sum(errores) / len(errores):.1f} puntos" if errores else ""
    _cerrar_sesion(resultados, drill="pot_odds", extra=extra)


def sesion_lectura(n: int, rng: random.Random) -> None:
    pesos = progreso.cargar_pesos("lectura")
    resultados = []
    print(
        f"D3 — Lectura de manos. {_situaciones(n)}.\n"
        "  ¿Qué mano gana al showdown? Responde el número, 'e' si empatan, 'q' para salir.\n"
    )

    for i in range(1, n + 1):
        s = lectura.generar_situacion(rng, pesos)
        print(f"[{i}/{n}] Board: {_mano(s.board)}")
        for j, mano in enumerate(s.manos, start=1):
            print(f"  Mano {j}: {_mano(mano)}")

        validas = tuple(str(j) for j in range(1, len(s.manos) + 1)) + ("e",)
        respuesta = _leer(f"  ¿quién gana? [{'/'.join(validas)}]: ")
        if respuesta is None:
            break
        if respuesta not in validas:
            print("  Respuesta inválida, situación saltada.\n")
            continue
        resultado = lectura.Resultado(s, respuesta)
        resultados.append(resultado)
        _imprimir_feedback(lectura.feedback(resultado))

    _cerrar_sesion(resultados, drill="lectura")


def cuadricula(posicion: str, chart: dict, color: bool = True) -> str:
    """Cuadrícula 13×13 del rango RFI de una posición, con colores ANSI opcionales."""
    verde, gris, reset = (VERDE, GRIS, RESET) if color else ("", "", "")
    manos = chart[posicion]["manos"]
    orden = "AKQJT98765432"
    filas = []
    for i, fila in enumerate(orden):
        celdas = []
        for j, col in enumerate(orden):
            if i == j:
                nombre = fila * 2
            elif j > i:
                nombre = f"{fila}{col}s"
            else:
                nombre = f"{col}{fila}o"
            pintura = verde if nombre in manos else gris
            celdas.append(f"{pintura}{nombre:<3}{reset}")
        filas.append(" ".join(celdas))
    n = combos(manos)
    encabezado = [
        f"Rango RFI de {posicion} (cash 6-max 100bb) — {n} de 1326 combos ({round(100 * n / 1326)}%)",
        chart[posicion]["rango"],
        f"{verde}verde{reset} = open, {gris}gris{reset} = fold · diagonal: parejas · arriba: suited · abajo: offsuit",
        "",
    ]
    return "\n".join(encabezado + filas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrenador de Texas Hold'em")
    parser.add_argument("--drill", choices=DRILLS)
    parser.add_argument("--rango", type=str.upper, choices=POSICIONES_RFI, metavar="POSICION",
                        help="muestra la cuadrícula del rango RFI de una posición (UTG, MP, CO, BTN, SB)")
    parser.add_argument("--n", type=int, default=10, help="situaciones por sesión")
    parser.add_argument("--semilla", type=int, default=None, help="semilla para reproducir una sesión")
    args = parser.parse_args()

    if args.rango:
        print(cuadricula(args.rango, cargar_rfi(), color=USA_COLOR))
        return
    if not args.drill:
        parser.error("indica --drill para entrenar o --rango para ver un chart")

    rng = random.Random(args.semilla)
    sesiones = {"preflop": sesion_preflop, "pot_odds": sesion_pot_odds, "lectura": sesion_lectura}
    sesiones[args.drill](args.n, rng)


if __name__ == "__main__":
    main()
