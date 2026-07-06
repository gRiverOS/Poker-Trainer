# Poker Trainer

Entrenador personal de Texas Hold'em: drills cortos con feedback inmediato
(preflop por posición, pot odds/equity, lectura de manos).

Estado: **F4 — los tres drills del MVP jugables** (cash 6-max 100bb), con
repetición ponderada por error — ver
[docs/diseno_entrenador.md](docs/diseno_entrenador.md).

```sh
uv run trainer.py --drill preflop        # D1: ¿open o fold? (10 manos)
uv run trainer.py --drill pot_odds       # D2: estima equity y decide call/fold
uv run trainer.py --drill lectura        # D3: ¿qué mano gana al showdown?
uv run trainer.py --rango BTN            # cuadrícula 13×13 del rango de una posición
uv run pytest                            # tests
```

Las categorías donde más fallas aparecen más seguido en la sesión siguiente
(un peso por categoría, calculado desde tu historial).

El historial de sesiones queda en `output/historial.csv`. Los charts de
referencia (con fuente citada) viven en `data/rangos_preflop/`.
