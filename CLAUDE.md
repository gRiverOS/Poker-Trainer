# CLAUDE.md — Poker Trainer

Contexto del proyecto para Claude Code. Actualizado 2026-07-05.

## Qué es este proyecto

**Poker Trainer** — entrenador personal de Texas Hold'em para el aprendizaje de
Gustavo. Drills cortos con feedback inmediato: te presenta una situación, decides,
te dice si acertaste y por qué. No es un solver ni una sala de juego.

El documento de referencia es **`docs/diseno_entrenador.md`** — leerlo antes de
implementar cualquier cosa. Define módulos, arquitectura y fases.

## Estado actual

**Fase F4 completada** (2026-07-05): drill D3 lectura de manos jugable
(`uv run trainer.py --drill lectura`): board completo + 2-4 manos, ¿cuál
gana? (con empates), feedback mostrando la categoría y el mejor 5 de cada
mano. **Repetición ponderada activa en los 3 drills**: peso por categoría
= 1 + 2·tasa_de_error histórica (posición en D1, calle en D2, categoría de
la mano ganadora en D3 vía muestreo por rechazo); el historial ahora guarda
la columna `categoria`.

Los tres drills del MVP (D1, D2, D3) están jugables. Pendientes opcionales:
- Extensión de D1: enfrentar un open (call/3-bet) — requiere charts por par
  de posiciones.
- F5 (opcional): D4 postflop guiado (requiere contenido curado) o UI web.
- Gráfico de tendencia desde `output/historial.csv`.

## Decisiones tomadas

- **Alcance:** entrenador personal (no comercial), Texas Hold'em.
- **Formato:** CLI en Python primero; UI web solo si el CLI queda corto (F5, opcional).
- **Stack:** Python + `uv` (mismo enfoque del Shoe-Tracker).
- **Principios:** reglas puras separadas de la interfaz (el evaluador no sabe que
  existe un CLI); tests de regresión del evaluador desde el día uno; charts de
  rangos como datos en `data/`, nunca hardcodeados; anti-overengineering (CLI +
  CSV hasta que el uso real pida más).
- **Orden de los drills:** D1 preflop por posición (MVP) → D2 pot odds/equity →
  D3 lectura de manos → D4 postflop guiado (requiere contenido curado, va al final).
- **Sin MLX ni aceleración GPU/ML** (evaluado 2026-07-05): el cómputo del proyecto
  no tiene forma de problema GPU — D1/D3 son lookups y comparaciones; el Monte Carlo
  de D2 es de una situación a la vez y el evaluador tiene demasiado branching para
  vectorizar bien. Si D2 queda lento, la ruta es `treys` (CPU), no MLX. Un LLM local
  para el feedback chocaría con la trazabilidad de los charts. Detalle en el diseño §3.

## Decisiones cerradas en F1/F2 (2026-07-05)

- **Cash 100bb, 6-max** — confirmado por Gustavo (era la propuesta del diseño).
- **Evaluador propio** — implementado en F1 y validado contra `treys` (5.000
  repartos, 0 discrepancias). En F3 se midió: ~0,1 ms/muestra, Monte Carlo de
  10k ≈ 1 s → `treys` descartado, Python puro alcanza.
- **Fuente de los charts preflop:** Preflop Wizard
  (https://www.preflopwizard.app/blog/preflop-charts), citada en
  `data/rangos_preflop/rfi_cash_6max_100bb.json` con fecha de consulta.

## Fases (resumen — detalle en el diseño)

| Fase | Entregable |
|------|-----------|
| F0 | Diseño + esqueleto del repo ✅ |
| F1 | `cartas.py` + `evaluador.py` + tests de regresión ✅ |
| F2 | Drill D1 preflop (RFI) con charts en `data/` + persistencia de progreso ✅ |
| F3 | D2 pot odds/equity (Monte Carlo, validado contra referencias) ✅ |
| F4 | D3 lectura de manos + repetición ponderada por error ✅ |
| F5 | (Opcional) D4 postflop o UI web |

## Convenciones de trabajo

- Documentar + commitear por paso (misma cadencia del Shoe-Tracker).
- Mantener este CLAUDE.md y el diseño al día cuando cambie una decisión.
- `output/` (historial de sesiones de entrenamiento) va gitignored.

## Repositorio

GitHub: `https://github.com/gRiverOS/Poker-Trainer`
