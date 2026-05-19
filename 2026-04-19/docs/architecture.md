# Architecture

## Engine ↔ UI Boundary

The codebase is split into two strict layers:

```
demo/src/engine/   ← pure functions only (no DOM, no globals, no side effects)
demo/src/ui/       ← DOM manipulation and event binding only
```

### Engine (testable)
- `lotto.js` — `generateLotto(rng)` picks 6 unique numbers from 1–45
- `random.js` — `seededRandom(seed)` returns a deterministic PRNG function

Rules:
- Functions take inputs, return outputs. No mutation of external state.
- No `document`, `window`, or `localStorage` references.
- Every exported function must have a corresponding test in `demo/tests/`.

### UI (manual verification)
- `renderer.js` — reads engine output, writes to DOM (ball colors, animation)
- `input.js` — listens to button/form events, calls engine, passes result to renderer

Rules:
- No business logic here. All computation happens in engine.
- Manual screenshot verification is sufficient (see `docs/ui-verification.md`).

## Why this split?

This is **Architectural constraints** (OpenAI Harness pillar ②).
The boundary forces testability and prevents accidental coupling.
Cline/Codex must not add DOM calls inside `engine/`.
