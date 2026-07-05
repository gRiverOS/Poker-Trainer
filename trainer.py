"""CLI del entrenador: `uv run trainer.py --drill preflop [--n 10] [--semilla 42]`."""

import argparse
import random

from src import progreso
from src.drills import preflop
from src.rangos import cargar_rfi

DRILLS = ("preflop", "pot_odds", "lectura")


def sesion_preflop(n: int, rng: random.Random) -> None:
    chart = cargar_rfi()
    resultados = []
    print(f"D1 — Preflop RFI (cash 6-max 100bb). {n} situaciones; responde 'o' (open), 'f' (fold) o 'q' (salir).\n")

    for i in range(1, n + 1):
        situacion = preflop.generar_situacion(rng)
        cartas_texto = " ".join(str(c) for c in situacion.mano)
        try:
            respuesta = input(f"[{i}/{n}] {situacion.posicion} — {cartas_texto} ({situacion.notacion}): ").strip().lower()
        except EOFError:
            print()
            break
        if respuesta == "q":
            break
        if respuesta not in ("o", "f"):
            print("  Respuesta inválida, situación saltada (usa 'o', 'f' o 'q').\n")
            continue
        elegida = "open" if respuesta == "o" else "fold"
        resultado = preflop.Resultado(situacion, elegida, preflop.accion_correcta(situacion, chart))
        resultados.append(resultado)
        print(f"  {preflop.feedback(resultado, chart)}\n")

    if not resultados:
        print("Sesión vacía, nada que guardar.")
        return

    r = progreso.resumen(resultados)
    print(f"— Resumen: {r['aciertos']}/{r['total']} aciertos ({r['pct']}%)")
    for pos, datos in r["por_posicion"].items():
        print(f"  {pos}: {datos['aciertos']}/{datos['total']} ({datos['pct']}%)")
    progreso.registrar(resultados, drill="preflop")
    print(f"Historial actualizado: {progreso.RUTA_HISTORIAL}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrenador de Texas Hold'em")
    parser.add_argument("--drill", choices=DRILLS, required=True)
    parser.add_argument("--n", type=int, default=10, help="situaciones por sesión")
    parser.add_argument("--semilla", type=int, default=None, help="semilla para reproducir una sesión")
    args = parser.parse_args()

    if args.drill != "preflop":
        print(f"Drill '{args.drill}' aún no implementado (llega en F3/F4).")
        return
    sesion_preflop(args.n, random.Random(args.semilla))


if __name__ == "__main__":
    main()
