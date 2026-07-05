# Diseño — Entrenador personal de Texas Hold'em

Documento de diseño inicial. Borrador 2026-07-05. Sin código todavía.

## 1. Objetivo

Herramienta personal para **mejorar la toma de decisiones en Texas Hold'em**, vía
drills cortos y repetibles con feedback inmediato. No es un solver ni una sala de
juego: es un entrenador — te presenta una situación, decides, te dice si tu decisión
fue correcta y por qué.

**Métrica de éxito personal:** % de aciertos por tipo de drill, con tendencia al alza
sesión a sesión. El progreso se persiste (CSV/SQLite) para poder graficarlo después.

## 2. Qué entrena (módulos de drill)

Ordenados por impacto en el juego real y por simplicidad de implementación:

### D1 — Preflop por posición (el MVP)
- Se te reparte una mano en una posición aleatoria (UTG, MP, CO, BTN, SB, BB).
- Decides: **fold / open-raise / call / 3-bet**.
- Se compara contra un chart de rangos de referencia (charts GTO públicos
  simplificados, formato dato — no hardcodeado en el código).
- Es el drill con mejor razón esfuerzo/beneficio: el preflop es ~la mitad de las
  decisiones de una sesión real y los rangos son tablas estáticas.

### D2 — Pot odds y equity rápida
- Situación: pot, apuesta a pagar, tus outs visibles.
- Decides: call/fold, o estimas tu equity (regla del 4 y 2).
- El motor calcula la equity real por enumeración o Monte Carlo y te muestra el error
  de tu estimación.

### D3 — Lectura de manos (hand ranking)
- Board completo + 2-4 manos: ¿cuál gana? ¿cuál es tu mejor mano de 5 cartas?
- Entrena velocidad de lectura; útil como calentamiento.

### D4 — Spots postflop guiados (fase posterior)
- Escenarios curados (c-bet, probe, river bluff-catch) con explicación del concepto.
- Requiere contenido editorial, no solo motor — por eso va al final.

## 3. Arquitectura (mínima, estilo scripts/)

Mismo enfoque que el Shoe-Tracker: **Python + `uv`**, módulos puros importables,
CLI como interfaz inicial.

```
poker-trainer/
├── pyproject.toml          # uv, deps mínimas
├── src/
│   ├── cartas.py           # Carta, mazo, parsing "Ah Kd" (base compartida)
│   ├── evaluador.py        # ranking de manos de 5/7 cartas (puro, testeable)
│   ├── equity.py           # enumeración + Monte Carlo (reusa evaluador)
│   ├── rangos.py           # carga charts preflop desde data/
│   ├── drills/
│   │   ├── preflop.py      # D1
│   │   ├── pot_odds.py     # D2
│   │   └── lectura.py      # D3
│   └── progreso.py         # persistencia de resultados por sesión
├── data/
│   └── rangos_preflop/     # charts como CSV/JSON, editables sin tocar código
├── tests/
│   └── test_evaluador.py   # regresión del evaluador (como test_baccarat_rules.py)
└── output/                 # historial de sesiones (gitignored)
```

Principios (heredados del Shoe-Tracker):
- **Reglas puras separadas de la interfaz** — `evaluador.py` y `equity.py` no saben
  que existe un CLI (mismo patrón que `baccarat_rules.py`).
- **Tests de regresión desde el día uno** para el evaluador de manos: es la pieza
  donde un bug silencioso invalida todo lo demás.
- **Datos como datos**: los rangos preflop viven en `data/`, no en el código.
- **Anti-overengineering**: sin UI web, sin base de datos relacional, sin solver.
  CLI + CSV hasta que el uso real pida más.

### Decisión técnica pendiente: evaluador propio vs librería
- **Opción A — librería (`treys` o similar):** evaluador 7-cartas rápido y probado;
  menos aprendizaje, más velocidad para Monte Carlo.
- **Opción B — propio:** escribirlo es en sí un ejercicio excelente para internalizar
  el ranking de manos (que es parte de lo que quieres entrenar).
- Propuesta: **B para el MVP** (D1 y D3 no necesitan velocidad), migrar a A si el
  Monte Carlo de D2 queda lento.

### Decisión: sin MLX ni aceleración GPU/ML (2026-07-05)

Se evaluó usar Apple MLX y se descartó:

- **D1 y D3** son lookups de tablas y lógica de comparación — cero cómputo pesado.
- **D2 (Monte Carlo)** calcula la equity de *una* situación mientras el usuario
  entrena; decenas de miles de simulaciones en Python puro toman segundos y sobran.
  Además el evaluador de manos es lógica con branching (escalera, color, full...),
  justo lo que peor se vectoriza en GPU. **Si D2 queda lento, la escalación es
  `treys` (lookup tables en CPU), no vectorización GPU** — ya anotado arriba.
- Usos donde MLX sí calzaría contradicen el proyecto: entrenar un modelo que juegue
  es construir un solver (fuera de alcance explícito), y un LLM local generando el
  feedback rompe el principio de que "correcto" sea trazable a charts citables.

Revisitar solo si el alcance cambia (p. ej. se decide construir un solver — hoy no).

## 4. Loop de entrenamiento

1. `uv run trainer.py --drill preflop` → sesión de N situaciones.
2. Cada respuesta: feedback inmediato (correcto/incorrecto + regla aplicable).
3. Al cerrar: resumen de la sesión (% acierto, errores por posición/tipo de mano)
   y append al historial en `output/`.
4. **Repetición ponderada por error**: las categorías donde más fallas aparecen más
   seguido en la siguiente sesión (spaced repetition simplificada — un peso por
   categoría basta, sin algoritmo SM-2 completo).

## 5. Fases

| Fase | Entregable | Criterio de salida |
|------|-----------|--------------------|
| F0 | Este diseño + repo con esqueleto y `pyproject.toml` | Compila `uv run`, tests verdes vacíos |
| F1 | `cartas.py` + `evaluador.py` + tests de regresión | Evaluador correcto contra casos conocidos |
| F2 | **D1 preflop** con charts en `data/` + `progreso.py` | Sesión completa jugable con feedback y resumen |
| F3 | D2 pot odds/equity (Monte Carlo) | Equity coincide con calculadoras de referencia |
| F4 | D3 lectura de manos + repetición ponderada | — |
| F5 | (Opcional) D4 postflop, o UI web si el CLI queda corto | — |

## 6. Preguntas abiertas

- **¿Cash o torneo?** Los rangos preflop cambian (stack depth, antes). Propuesta:
  partir con **cash 100bb** (los charts públicos más estándar) y parametrizar después.
- **Fuente de los charts:** elegir un set de rangos de referencia público y citarlo
  en `data/` (que el criterio de "correcto" sea trazable, no opinión del código).
- **¿6-max o full ring?** Propuesta: 6-max (más material de referencia, menos
  posiciones que memorizar al inicio).
