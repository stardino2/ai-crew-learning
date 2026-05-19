/**
 * generateLotto(rng) → number[6]
 *
 * Picks 6 unique integers from [1, 45] using the provided rng function.
 * Returns them sorted in ascending order.
 *
 * @param {() => number} rng - Random number generator returning [0, 1)
 */
export function generateLotto(rng = Math.random) {
  const picked = new Set();
  while (picked.size < 6) {
    picked.add(Math.floor(rng() * 45) + 1);
  }
  return [...picked].sort((a, b) => a - b);
}
