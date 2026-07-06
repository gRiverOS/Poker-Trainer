# Poker Trainer

Entrenador personal de Texas Hold'em: drills cortos con feedback inmediato
(preflop por posición, pot odds/equity, lectura de manos).

Estado: **F3 — drills preflop RFI y pot odds/equity jugables** (cash 6-max
100bb) — ver [docs/diseno_entrenador.md](docs/diseno_entrenador.md).

```sh
uv run trainer.py --drill preflop        # D1: ¿open o fold? (10 manos)
uv run trainer.py --drill pot_odds       # D2: estima equity y decide call/fold
uv run pytest                            # tests
```

El historial de sesiones queda en `output/historial.csv`. Los charts de
referencia (con fuente citada) viven en `data/rangos_preflop/`.
