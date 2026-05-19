import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["demo/tests/**/*.test.js"],
    environment: "node",
  },
});
