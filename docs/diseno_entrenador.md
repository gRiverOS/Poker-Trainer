# Diseño — Entrenador personal de Texas Hold'em

Documento de diseño inicial (borrador 2026-07-05) — **actualizado el mismo día
al cierre de F4**: D1 (RFI + defensa de BB), D2 y D3 implementados y jugables,
con repetición ponderada. Las decisiones que este documento dejaba abiertas
están resueltas (ver §6). El estado vivo del proyecto se lleva en `CLAUDE.md`.

## 1. Objetivo

Herramienta personal para **mejorar la toma de decisiones en Texas Hold'em**, vía
drills cortos y repetibles con feedback inmediato. No es un solver ni una sala de
juego: es un entrenador — te presenta una situación, decides, te dice si tu decisión
fue correcta y por qué.

**Métrica de éxito personal:** % de aciertos por tipo de drill, con tendencia al alza
sesión a sesión. El progreso se persiste (CSV/SQLite) para poder graficarlo después.

## 2. Qué entrena (módulos de drill)

Ordenados por impacto en el juego real y por simplicidad de implementación:

### D1 — Preflop por posición (el MVP) ✅
- Se te reparte una mano en una posición aleatoria.
- Dos escenarios mezclados en la misma sesión:
  - **RFI** (nadie abrió; UTG/MP/CO/BTN/SB): open o fold. La BB no aparece:
    sin open previo, o alguien abre antes o la BB gana las ciegas sin decidir.
  - **Defensa de BB** (alguien abrió ~2.5bb): fold, call o 3-bet.
- Se compara contra charts de referencia en `data/` (formato dato — no
  hardcodeado). Al errar, un "Tip" de largo tuit explica el porqué, construido
  solo con hechos del chart (mínimo kicker, suited vs offsuit, desde qué
  posición se abre/defiende la mano).
- Alcance: defender desde posiciones distintas de BB (p. ej. CO vs open de
  UTG) queda fuera.
- Es el drill con mejor razón esfuerzo/beneficio: el preflop es ~la mitad de las
  decisiones de una sesión real y los rangos son tablas estáticas.

### D2 — Pot odds y equity rápida ✅
- Situación: pot, apuesta a pagar, tu mano y el board (flop o turn).
- Estimas tu equity (opcional; regla del 4 y 2 contando tus outs) y decides
  call/fold contra una mano aleatoria.
- El motor calcula la equity real (Monte Carlo 10k muestras ≈ 1 s) y muestra el
  error de tu estimación y la equity necesaria por pot odds. Spots a <2 puntos
  del límite aceptan cualquier respuesta (zona gris: el MC tiene ruido ±1).

### D3 — Lectura de manos (hand ranking) ✅
- Board completo + 2-4 manos: ¿cuál gana? (con empates — responde 'e').
- El "¿cuál es tu mejor mano de 5?" se entrena de forma pasiva: el feedback
  muestra la categoría y el mejor 5 de cada mano.
- Entrena velocidad de lectura; útil como calentamiento.

### D4 — Spots postflop guiados (fase posterior)
- Escenarios curados (c-bet, probe, river bluff-catch) con explicación del concepto.
- Requiere contenido editorial, no solo motor — por eso va al final.

## 3. Arquitectura (mínima, estilo scripts/)

Mismo enfoque que el Shoe-Tracker: **Python + `uv`**, módulos puros importables,
CLI como interfaz inicial.

```
poker-trainer/
├── pyproject.toml          # uv, sin deps de runtime (pytest como dev)
├── trainer.py              # CLI: sesiones de drills y --rango POS (cuadrícula 13×13)
├── src/
│   ├── cartas.py           # Carta, mazo, parsing "Ah Kd", símbolos ♠♥♦♣ para pantalla
│   ├── evaluador.py        # ranking 5/7 cartas: (Categoria, desempates) comparable
│   ├── equity.py           # enumeración exacta + Monte Carlo (reusa evaluador)
│   ├── rangos.py           # notación 169, expansión de tokens, carga de charts
│   ├── drills/
│   │   ├── preflop.py      # D1: RFI + defensa BB, tips trazables al chart
│   │   ├── pot_odds.py     # D2: equity vs pot odds, zona gris
│   │   └── lectura.py      # D3: quién gana, con empates
│   └── progreso.py         # historial CSV + pesos de repetición ponderada
├── data/
│   └── rangos_preflop/     # charts JSON con fuente citada, editables sin tocar código
├── tests/                  # regresión: evaluador, rangos, drills, progreso, CLI
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

### Decisión técnica RESUELTA: evaluador propio vs librería
- **Se eligió B (propio)** y quedó validado doblemente:
  - Correctitud: 5.000 repartos aleatorios comparados contra `treys`,
    0 discrepancias (validación puntual, `treys` no es dependencia).
  - Velocidad: ~0,1 ms por muestra de Monte Carlo medido → 10k muestras ≈ 1 s.
    **La migración a librería queda descartada mientras eso no cambie.**

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
4. **Repetición ponderada por error** ✅: las categorías donde más fallas aparecen
   más seguido en la siguiente sesión. Implementada tal como se diseñó: un peso
   por categoría (= 1 + 2·tasa de error histórica; 2.0 sin datos), sin SM-2.
   Categorías: posición/escenario en D1, calle en D2, categoría de la mano
   ganadora en D3 (muestreo por rechazo).

## 5. Fases

| Fase | Entregable | Criterio de salida |
|------|-----------|--------------------|
| F0 ✅ | Este diseño + repo con esqueleto y `pyproject.toml` | Compila `uv run`, tests verdes vacíos |
| F1 ✅ | `cartas.py` + `evaluador.py` + tests de regresión | Evaluador correcto contra casos conocidos (+ cotejo vs `treys`) |
| F2 ✅ | **D1 preflop** con charts en `data/` + `progreso.py` | Sesión completa jugable con feedback y resumen |
| F3 ✅ | D2 pot odds/equity (Monte Carlo) | Equity coincide con calculadoras de referencia (±2 pts) |
| F4 ✅ | D3 lectura de manos + repetición ponderada | — |
| F4+ ✅ | Extensión D1: defensa de BB (fold/call/3-bet) | Sesión mixta RFI+defensa jugable |
| F5 | (Opcional) D4 postflop, o UI web si el CLI queda corto | — |

Todas las fases del MVP se completaron el 2026-07-05.

## 6. Preguntas abiertas — todas resueltas (2026-07-05)

- **¿Cash o torneo?** → **Cash 100bb**, confirmado por Gustavo.
- **¿6-max o full ring?** → **6-max**, confirmado por Gustavo.
- **Fuente de los charts** → dos niveles de trazabilidad, documentados en
  `data/rangos_preflop/`:
  - RFI: **Preflop Wizard**, citado con URL y fecha en el JSON. ✅ trazable.
  - Defensa de BB: ⚠️ **aproximación de consenso sin fuente única citable**
    (ninguna fuente pública publica esa defensa por posición en texto).
    Construida según principios publicados por GTO Wizard/Upswing/Preflop
    Wizard y marcada como tal en el JSON. Mejora pendiente: reemplazar por un
    export citable editando solo el archivo de datos.
