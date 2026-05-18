# Demo Runbook

## Goal

실패를 일부러 만들지 않는다. Codex가 점검 배너 요청을 받은 뒤 `AGENTS.md`의 checkpoint 규칙을 따라 구현하고, 완료 전 `npm run maintenance:complete`를 통과하는 장면을 보여준다.

핵심 메시지:

> LLM이 코드를 바꾸는 것보다 중요한 것은, 변경 결과가 config, API, UI, design, docs, ops log, report 하네스를 통과했다는 증거가 남는 것이다.

## Preflight

1. 터미널을 `mini-status-harness/`에서 연다.
2. 4173 포트가 비어 있는지 확인한다.
3. 서버를 실행한다.

```powershell
npm start
```

4. 브라우저에서 `http://localhost:4173/`을 연다.
5. 다른 터미널에서 베이스라인 완료 게이트를 확인한다.

```powershell
npm run maintenance:complete
```

maintenance off 상태에서도 `harness`, `test:design`, `test:ops-log`, `report:check`가 모두 통과해야 한다.

## Demo Request

발표 중 Codex에 아래 요청문을 그대로 입력한다.

```text
현재 상태 페이지에 예정 점검 배너를 추가해줘.

조건:
- 점검 시간은 2026-05-20 19:00-20:00 KST
- 영향 서비스는 API Gateway
- 사용자가 첫 화면에서 바로 볼 수 있어야 함
- 운영 공지 문구도 함께 업데이트해줘
- ops audit log도 남겨줘
- 결과 리포트에 통과한 하네스 목록, 로그, 화면 snapshot 근거도 포함해줘

작업 방식:
- AGENTS.md의 레이어별 checkpoint 규칙을 따라줘.
- config, API contract, UI, design, docs, ops-log, report 체크를 필요한 순서대로 실행해줘.
- 완료 전 반드시 npm run maintenance:complete를 실행해줘.
- maintenance:complete가 통과하기 전에는 완료 보고하지 마.
```

## Live Flow

1. 초기 화면: 점검 배너 없는 상태 페이지를 보여준다.
2. 베이스라인: `npm run maintenance:complete` 통과를 보여준다.
3. 요청 입력: Codex에 Demo Request를 입력한다.
4. 작업 관찰: Codex가 config, UI, docs, ops log, report를 수정하고 checkpoint를 실행하는 과정을 보여준다.
5. 완료 게이트: 최종 `npm run maintenance:complete` 통과 로그를 보여준다.
6. 화면 확인: `http://localhost:4173/`을 새로고침하고 API Gateway 예정 점검 배너를 확인한다.
7. 리포트 확인: `reports/latest/index.html`을 열어 하네스 목록, 로그, HTML snapshot, 화면 이미지 참조, ops-log 요약을 보여준다.

## Narration Points

- "여기서 중요한 건 실패가 났느냐가 아닙니다."
- "LLM이 만든 변경이 config, API, UI, design, docs, ops log, report까지 같은 이야기를 하고 있는지 하네스가 확인합니다."
- "`maintenance:complete`는 자동 watch가 아니라 Codex 작업 규칙에 포함된 최종 완료 게이트입니다."
- "Codex는 이 게이트를 실행하고 통과해야만 완료 보고를 할 수 있습니다."
- "최종 HTML 리포트는 코드 변경의 결과뿐 아니라 검증 증거까지 남기는 산출물입니다."

## If There Is No Failure

그대로 진행한다. 실패 장면은 필수 시연 요소가 아니다.

Codex가 한 번에 모든 레이어를 맞췄다면 다음처럼 설명한다.

> 이번에는 Codex가 한 번에 모든 레이어를 맞췄습니다. 중요한 건 실패가 났느냐가 아니라, 완료 전에 이 모든 하네스를 통과했다는 증거가 남는다는 점입니다.

## Reset

시연 후에는 베이스라인 정의에 맞게 되돌린다.

- `status.config.json`의 `maintenance.enabled: false`
- 배너 DOM/render/style 제거
- `docs/ops-notice.md`, `CHANGELOG.md` 초기화
- `ops/maintenance-events.ndjson` 제거 또는 비우기
- `reports/latest/index.html`을 실행 전 placeholder로 복구
