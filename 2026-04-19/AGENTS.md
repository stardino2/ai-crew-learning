# Lecture0419 — AGENTS Guide

This file is the primary entry point for Codex, Cline, Cursor, Claude Code, and any other coding agent.

## Reading Order

1. `docs/architecture.md` — engine ↔ ui boundary rules
2. `docs/testing.md` — pure function separation, vitest setup
3. `plans/active/*.md` — active work plan (read before making changes)

> 발표자용 내레이션·체크리스트·Cline 프롬프트는 `presentation/` 폴더 참조 (agent가 읽을 필요 없음).

## Work Principles

- **No direct commits to main branch** — always use `git worktree`
- **Write a plan first** — create `plans/active/<task>.md` before any code change
- **Engine changes require tests** — any change to `demo/src/engine/` must come with a matching test update in `demo/tests/`
- **All commits must pass** — `sh scripts/verify-tasks.sh` must succeed before committing
- **Commit messages** — include a short summary and reference the plan file path

## Context

Demo repo for a 10-minute lecture on Harness Engineering (하네스 엔지니어링).
Based on OpenAI's 3 pillars: Context engineering / Architectural constraints / Garbage collection.

The demo shows adding a new engine feature to a lotto number generator.
- `Before` state: basic random lotto (1–45, 6 numbers)
