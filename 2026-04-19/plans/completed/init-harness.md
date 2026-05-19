# Plan: Initialize Harness

**Status:** completed (bootstrap commit)

## What

Set up the complete `lecture0419` repo from scratch:
- Harness structure (AGENTS.md, docs/, plans/, logs/, scripts/)
- Husky pre-commit hook (4-stage guard)
- Demo lotto code (Before state, 11 tests green)
- Lecture materials (handoff.md, slides/outline.md, scripts/demo-run.md)

## Why this plan exists

Bootstrapping the harness requires an initial commit before the hook is fully active.
This plan file satisfies rule 2 (plans/active must exist) retroactively.
Future commits will follow the normal flow: worktree → plan → implement → verify → commit.

## Affected files

All files in `lecture0419/`.
