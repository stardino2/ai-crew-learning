# Plan: reorganize-folders

## Goal
`scripts/` 에 섞인 발표자 문서 분리 및 legacy `slides/outline.md` 제거.

## Changes
- `scripts/lecture-script.md` → `speaker/script.md`
- `scripts/demo-run.md` → `speaker/checklist.md`
- `slides/outline.md` → deleted (superseded by slides/index.html)
- Reference updates: README.md, speaker/script.md, docs/cline-usage.md, AGENTS.md
