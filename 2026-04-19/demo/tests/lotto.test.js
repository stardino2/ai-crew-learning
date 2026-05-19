import { describe, it, expect } from "vitest";
import { generateLotto } from "../src/engine/lotto.js";
import { seededRandom } from "../src/engine/random.js";

describe("generateLotto", () => {
  it("returns exactly 6 numbers", () => {
    expect(generateLotto()).toHaveLength(6);
  });

  it("all numbers are in range [1, 45]", () => {
    const result = generateLotto();
    result.forEach((n) => {
      expect(n).toBeGreaterThanOrEqual(1);
      expect(n).toBeLessThanOrEqual(45);
    });
  });

  it("has no duplicates", () => {
    const result = generateLotto();
    expect(new Set(result).size).toBe(6);
  });

  it("is sorted in ascending order", () => {
    const result = generateLotto();
    const sorted = [...result].sort((a, b) => a - b);
    expect(result).toEqual(sorted);
  });

  it("is deterministic with a seeded rng", () => {
    const first = generateLotto(seededRandom(42));
    const second = generateLotto(seededRandom(42));
    expect(first).toEqual(second);
  });

  it("produces different results for different seeds", () => {
    const a = generateLotto(seededRandom(1));
    const b = generateLotto(seededRandom(999));
    expect(a).not.toEqual(b);
  });
});
