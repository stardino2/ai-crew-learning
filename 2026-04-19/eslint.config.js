// ESLint config — syntax validation only (no external plugin imports)
// This ensures the config works in git worktrees without node_modules setup.
export default [
  {
    files: ["demo/src/**/*.js", "demo/tests/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": "warn",
    },
  },
];
