# CLAUDE.md — Poker Trainer

Contexto del proyecto para Claude Code. Actualizado 2026-07-05.

## Qué es este proyecto

**Poker Trainer** — entrenador personal de Texas Hold'em para el aprendizaje de
Gustavo. Drills cortos con feedback inmediato: te presenta una situación, decides,
te dice si acertaste y por qué. No es un solver ni una sala de juego.

El documento de referencia es **`docs/diseno_entrenador.md`** — leerlo antes de
implementar cualquier cosa. Define módulos, arquitectura y fases.

## Estado actual

**Fase F0 — diseño.** No hay código todavía. Lo único versionado es el diseño,
este archivo y el README.

Próximo paso: F0/F1 — esqueleto con `pyproject.toml` (uv) + `src/cartas.py` +
`src/evaluador.py` con tests de regresión.

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

## Decisiones abiertas (resolver antes de F2)

- **¿Cash o torneo?** Propuesta en el diseño: cash 100bb (charts públicos más estándar).
- **¿6-max o full ring?** Propuesta: 6-max.
- **¿Evaluador propio o librería (`treys`)?** Propuesta: propio para el MVP (escribirlo
  es parte del aprendizaje); migrar a librería solo si el Monte Carlo de D2 queda lento.
- **Fuente de los charts preflop:** elegir un set público de referencia y citarlo en
  `data/` — el criterio de "correcto" debe ser trazable, no opinión del código.

## Fases (resumen — detalle en el diseño)

| Fase | Entregable |
|------|-----------|
| F0 | Diseño + esqueleto del repo (✅ diseño; esqueleto pendiente) |
| F1 | `cartas.py` + `evaluador.py` + tests de regresión |
| F2 | Drill D1 preflop con charts en `data/` + persistencia de progreso |
| F3 | D2 pot odds/equity (Monte Carlo, validar contra calculadoras de referencia) |
| F4 | D3 lectura de manos + repetición ponderada por error |
| F5 | (Opcional) D4 postflop o UI web |

## Convenciones de trabajo

- Documentar + commitear por paso (misma cadencia del Shoe-Tracker).
- Mantener este CLAUDE.md y el diseño al día cuando cambie una decisión.
- `output/` (historial de sesiones de entrenamiento) va gitignored.

## Repositorio

GitHub: `https://github.com/gRiverOS/Poker-Trainer`
