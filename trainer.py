"""CLI del entrenador: `uv run trainer.py --drill preflop [--n 10] [--semilla 42]`."""

import argparse
import random

from src import progreso
from src.cartas import mostrar
from src.drills import lectura, pot_odds, preflop
from src.equity import equity_monte_carlo
from src.rangos import POSICIONES_RFI, cargar_defensa_bb, cargar_rfi, combos

DRILLS = ("preflop", "pot_odds", "lectura")

VERDE = "\033[1;32m"
GRIS = "\033[90m"
RESET = "\033[0m"


def cuadricula(posicion: str, chart: dict) -> str:
    """Cuadrícula 13×13 del rango RFI de una posición, con colores ANSI."""
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
            color = VERDE if nombre in manos else GRIS
            celdas.append(f"{color}{nombre:<3}{RESET}")
        filas.append(" ".join(celdas))
    n = combos(manos)
    encabezado = [
        f"Rango RFI de {posicion} (cash 6-max 100bb) — {n} de 1326 combos ({round(100 * n / 1326)}%)",
        chart[posicion]["rango"],
        f"{VERDE}verde{RESET} = open, {GRIS}gris{RESET} = fold · diagonal: parejas · arriba: suited · abajo: offsuit",
        "",
    ]
    return "\n".join(encabezado + filas)


def _leer(prompt: str) -> str | None:
    """input() que devuelve None si la sesión se corta (EOF o 'q')."""
    try:
        texto = input(prompt).strip().lower()
    except EOFError:
        print()
        return None
    return None if texto == "q" else texto


def _cerrar_sesion(resultados, drill: str, extra: str = "") -> None:
    if not resultados:
        print("Sesión vacía, nada que guardar.")
        return
    r = progreso.resumen(resultados)
    print(f"— Resumen: {r['aciertos']}/{r['total']} aciertos ({r['pct']}%){extra}")
    for cat, datos in r["por_categoria"].items():
        print(f"  {cat}: {datos['aciertos']}/{datos['total']} ({datos['pct']}%)")
    progreso.registrar(resultados, drill=drill)
    print(f"Historial actualizado: {progreso.RUTA_HISTORIAL}")


def sesion_preflop(n: int, rng: random.Random) -> None:
    rfi = cargar_rfi()
    defensa = cargar_defensa_bb()
    pesos = progreso.cargar_pesos("preflop")
    resultados = []
    print(
        f"D1 — Preflop (cash 6-max 100bb). {n} situaciones, dos escenarios mezclados:\n"
        "  · RFI (nadie abrió): 'o' (open) o 'f' (fold)\n"
        "  · Defensa de BB (alguien abrió ~2.5bb): 'f' (fold), 'c' (call) o '3' (3-bet)\n"
        "  'q' para salir.\n"
    )

    for i in range(1, n + 1):
        s = preflop.generar_situacion(rng, pesos)
        if s.es_defensa:
            prompt = f"[{i}/{n}] BB vs open de {s.abridor} — {mostrar(s.mano)} ({s.notacion}) [f/c/3]: "
            mapa = {"f": "fold", "c": "call", "3": "3bet", "r": "3bet"}
        else:
            prompt = f"[{i}/{n}] {s.posicion} — {mostrar(s.mano)} ({s.notacion}) [o/f]: "
            mapa = {"o": "open", "f": "fold"}
        respuesta = _leer(prompt)
        if respuesta is None:
            break
        if respuesta not in mapa:
            print(f"  Respuesta inválida, situación saltada (usa {'/'.join(sorted(set(mapa)))} o 'q').\n")
            continue
        resultado = preflop.Resultado(s, mapa[respuesta], preflop.accion_correcta(s, rfi, defensa))
        resultados.append(resultado)
        print(f"  {preflop.feedback(resultado, rfi, defensa)}\n")

    _cerrar_sesion(resultados, drill="preflop")


def sesion_pot_odds(n: int, rng: random.Random) -> None:
    pesos = progreso.cargar_pesos("pot_odds")
    resultados = []
    print(
        f"D2 — Pot odds y equity (heads-up vs mano aleatoria). {n} situaciones.\n"
        "Estima tu equity (%, enter para saltar la estimación) y decide 'c' (call), 'f' (fold) o 'q' (salir).\n"
    )

    for i in range(1, n + 1):
        s = pot_odds.generar_situacion(rng, pesos)
        print(f"[{i}/{n}] {s.calle}: tu mano {mostrar(s.mano)} — board {mostrar(s.board)}")
        print(f"      pot {s.pot:g}bb, el rival apuesta {s.apuesta:g}bb. ¿Pagas?")

        estimacion_texto = _leer("      tu equity estimada (%): ")
        if estimacion_texto is None:
            break
        estimacion = None
        if estimacion_texto:
            try:
                estimacion = float(estimacion_texto.replace("%", "").replace(",", "."))
            except ValueError:
                print("      Estimación ilegible, la salto.")

        decision = _leer("      call o fold (c/f): ")
        if decision is None:
            break
        if decision not in ("c", "f"):
            print("      Respuesta inválida, situación saltada.\n")
            continue

        equity_real = 100 * equity_monte_carlo(s.mano, s.board, n=10_000, rng=rng)
        resultado = pot_odds.Resultado(s, "call" if decision == "c" else "fold", equity_real, estimacion)
        resultados.append(resultado)
        print(f"  {pot_odds.feedback(resultado)}\n")

    errores = [r.error_estimacion for r in resultados if r.error_estimacion is not None]
    extra = f" — error medio de estimación: {sum(errores) / len(errores):.1f} puntos" if errores else ""
    _cerrar_sesion(resultados, drill="pot_odds", extra=extra)


def sesion_lectura(n: int, rng: random.Random) -> None:
    pesos = progreso.cargar_pesos("lectura")
    resultados = []
    print(
        f"D3 — Lectura de manos. {n} situaciones.\n"
        "¿Qué mano gana al showdown? Responde con el número, 'e' si empatan, o 'q' para salir.\n"
    )

    for i in range(1, n + 1):
        s = lectura.generar_situacion(rng, pesos)
        print(f"[{i}/{n}] Board: {mostrar(s.board)}")
        for j, mano in enumerate(s.manos, start=1):
            print(f"      Mano {j}: {mostrar(mano)}")

        validas = tuple(str(j) for j in range(1, len(s.manos) + 1)) + ("e",)
        respuesta = _leer(f"      ¿quién gana? ({'/'.join(validas)}): ")
        if respuesta is None:
            break
        if respuesta not in validas:
            print("      Respuesta inválida, situación saltada.\n")
            continue
        resultado = lectura.Resultado(s, respuesta)
        resultados.append(resultado)
        print(f"  {lectura.feedback(resultado)}\n")

    _cerrar_sesion(resultados, drill="lectura")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrenador de Texas Hold'em")
    parser.add_argument("--drill", choices=DRILLS)
    parser.add_argument("--rango", type=str.upper, choices=POSICIONES_RFI, metavar="POSICION",
                        help="muestra la cuadrícula del rango RFI de una posición (UTG, MP, CO, BTN, SB)")
    parser.add_argument("--n", type=int, default=10, help="situaciones por sesión")
    parser.add_argument("--semilla", type=int, default=None, help="semilla para reproducir una sesión")
    args = parser.parse_args()

    if args.rango:
        print(cuadricula(args.rango, cargar_rfi()))
        return
    if not args.drill:
        parser.error("indica --drill para entrenar o --rango para ver un chart")

    rng = random.Random(args.semilla)
    sesiones = {"preflop": sesion_preflop, "pot_odds": sesion_pot_odds, "lectura": sesion_lectura}
    sesiones[args.drill](args.n, rng)


if __name__ == "__main__":
    main()
