# Poker Trainer

Entrenador personal de Texas Hold'em: drills cortos con feedback inmediato
(preflop por posición, pot odds/equity, lectura de manos).

Estado: **F1 — cartas y evaluador de manos listos, sin drills todavía** — ver
[docs/diseno_entrenador.md](docs/diseno_entrenador.md).

```sh
uv run pytest              # tests
uv run trainer.py --drill preflop
```
