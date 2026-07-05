"""CLI del entrenador: `uv run trainer.py --drill preflop`."""

import argparse

DRILLS = ("preflop", "pot_odds", "lectura")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrenador de Texas Hold'em")
    parser.add_argument("--drill", choices=DRILLS, required=True)
    args = parser.parse_args()
    print(f"Drill '{args.drill}' aún no implementado (F0: solo esqueleto).")


if __name__ == "__main__":
    main()
