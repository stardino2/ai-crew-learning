# Plan: split-presentation-demo

## Goal
발표자료(`slides/`, `speaker/`, `docs/cline-usage.md`)를 `presentation/` 폴더로 분리하고, `.husky/pre-commit`의 harness 검사를 demo 스코프 변경 시에만 적용한다.

## Changes
- `git mv slides → presentation/slides`
- `git mv speaker → presentation/speaker`
- `git mv docs/cline-usage.md → presentation/cline-usage.md`
- `.husky/pre-commit` — staged 파일 기준 scope 판정 가드 삽입
- `AGENTS.md`, `README.md`, `speaker/script.md`, `cline-usage.md` 경로 참조 업데이트
- `plans/active/reorganize-folders.md` → `plans/completed/` 이동 (이미 반영 완료)

## Harness pillar mapping
- Architectural constraints: hook이 demo 코드에만 엄격히 적용됨을 더 명확히 함
- Garbage collection: stale plan 파일(reorganize-folders) 정리
