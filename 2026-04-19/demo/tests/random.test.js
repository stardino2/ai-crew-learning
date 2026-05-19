import { describe, it, expect } from "vitest";
import { seededRandom } from "../src/engine/random.js";

describe("seededRandom", () => {
  it("returns values in [0, 1)", () => {
    const rng = seededRandom(1234);
    for (let i = 0; i < 100; i++) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("produces the same sequence for the same seed", () => {
    const rng1 = seededRandom(99);
    const rng2 = seededRandom(99);
    for (let i = 0; i < 20; i++) {
      expect(rng1()).toBe(rng2());
    }
  });

  it("produces different sequences for different seeds", () => {
    const a = Array.from({ length: 10 }, seededRandom(1));
    const b = Array.from({ length: 10 }, seededRandom(2));
    expect(a).not.toEqual(b);
  });
});
