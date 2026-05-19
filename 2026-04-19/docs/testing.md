# Testing Guide

## Setup

```bash
npm install
npx vitest run          # single run
npx vitest              # watch mode
```

Tests live in `demo/tests/` and are discovered by `vitest.config.js`.

## What to test

Only `demo/src/engine/` functions need unit tests.
UI code (`demo/src/ui/`) is verified manually (see `docs/ui-verification.md`).

## Invariants every engine function must satisfy

### `generateLotto(rng)`
- Returns an array of exactly 6 numbers
- All numbers are integers in range [1, 45]
- No duplicates
- Sorted in ascending order
- Given the same `rng` seed, always returns the same result

### `seededRandom(seed)`
- Returns a function `() => number`
- Each call returns a float in `[0, 1)`
- Same seed → identical sequence of values

## Example test pattern

```js
import { describe, it, expect } from "vitest";
import { generateLotto } from "../src/engine/lotto.js";
import { seededRandom } from "../src/engine/random.js";

describe("generateLotto", () => {
  it("returns 6 sorted unique numbers in [1,45]", () => {
    const result = generateLotto();
    expect(result).toHaveLength(6);
    expect(result).toEqual([...new Set(result)].sort((a, b) => a - b));
    result.forEach(n => {
      expect(n).toBeGreaterThanOrEqual(1);
      expect(n).toBeLessThanOrEqual(45);
    });
  });

  it("is deterministic with a seeded rng", () => {
    const rng = seededRandom(42);
    const first = generateLotto(rng);
    const rng2 = seededRandom(42);
    const second = generateLotto(rng2);
    expect(first).toEqual(second);
  });
});
```
