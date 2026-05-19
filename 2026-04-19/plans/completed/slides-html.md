# slides-html

**목표:** `slides/outline.md`를 `slides/index.html` (단일 파일 슬라이드 덱)으로 변환

## 작업 범위
- `slides/index.html` 신규 생성 — 7-slide, keyboard nav, inline CSS+JS, CDN 없음
- `slides/outline.md` 라인 4 제거 (스크린샷 삽입 예정 문구 — 텍스트 전용으로 결정)
- `handoff.md` Task B 상태 업데이트 + 폴백 계층 #4 문구 수정
- `scripts/demo-run.md` 폴백 테이블 3행 문구 수정

## 완료 조건
- `slides/index.html` 브라우저에서 7장 렌더, 키보드(←→·1–7)로 탐색
- Slides 3·5·7에서만 pillar 3칩 우상단 노출
- 외부 리소스 0 (오프라인 동작)
- `sh scripts/verify-tasks.sh` green
