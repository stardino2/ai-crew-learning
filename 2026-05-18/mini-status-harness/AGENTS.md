# AGENTS.md

`mini-status-harness/` 디렉토리에서 작업할 때 지켜야 할 규칙.

## 1. 베이스라인 상태를 깨지 마라

저장소 커밋 상태는 **"점검 일정 없음" 베이스라인**이다. 시연의 1단계가 베이스라인에서 출발하기 때문에 이 상태가 깨지면 데모 전체가 망가진다.

베이스라인의 정의:

- `status.config.json`의 `maintenance.enabled === false`
- 모든 `services[].status === "operational"`
- `public/index.html`에 `id="maintenance-banner"` 없음
- `public/app.js`에 `renderMaintenance` 없음
- `public/styles.css`에 `.maintenance-banner*` 없음
- `docs/ops-notice.md` 와 `CHANGELOG.md`에 2026-05-20 관련 항목 없음
- `ops/maintenance-events.ndjson`는 없거나 비어 있음
- `reports/latest/index.html`은 "실행된 점검 배너 결과 없음" placeholder 상태

베이스라인 상태에서 `npm run harness`는 항상 6/6 통과해야 한다.

## 2. 하네스 검사는 config-driven 이어야 한다

`scripts/check-*.mjs`는 모두 **`status.config.json`을 먼저 읽고, 거기서 기대값을 derive** 해야 한다.

- 특정 날짜(`"2026-05-20"`), 특정 서비스명(`"API Gateway"`), 특정 타임스탬프를 검사 코드에 **하드코딩하지 않는다**.
- `if (config.maintenance?.enabled) { ... }` 가드를 사용해, 베이스라인에서는 maintenance 관련 검사가 자동으로 스킵되게 한다.
- 실패 메시지에는 **왜 실패했는지** + **어디서 기대값이 derive 되었는지**를 적는다 — 예: `ops notice must include "2026-05-20" (derived from config maintenance.start)`.

이렇게 하면 같은 하네스가 어떤 점검 일정에도 작동하고, 청중에게 "검사는 데이터에서 나온다"는 메시지를 그대로 보여준다.

## 3. 점검 배너 작업은 레이어별 checkpoint를 통과해야 한다

점검 배너 요청을 받으면 한 번에 구현을 끝내고 마지막에만 검사하지 않는다. 아래 순서로 checkpoint를 실행하고, 실패하면 해당 레이어를 고친 뒤 다시 실행한다.

1. `status.config.json` 수정 후 `npm run test:config`
2. API/status payload 영향이 있으면 `npm run test:contract`
3. UI DOM/render/style 수정 후 `npm run test:ui` 와 `npm run test:design`
4. 운영 공지, changelog, audit log 수정 후 `npm run test:docs` 와 `npm run test:ops-log`
5. 결과 리포트 작성 후 `npm run report:check`
6. 최종 완료 전 `npm run maintenance:complete`

`npm run maintenance:complete`가 통과하기 전에는 점검 배너 작업을 완료했다고 보고하지 않는다.

`test:design`은 전체 CSS를 새 디자인 시스템으로 강제하지 않는다. maintenance가 켜진 경우에만 배너 관련 CSS가 `design.md`의 토큰 기반 계약을 지키는지 검사한다.

`test:ops-log`는 config에서 derive한 점검 일정과 `ops/maintenance-events.ndjson`의 audit 이벤트가 일치하는지 검사한다.

`report:check`는 외부 브라우저 런타임에 의존하지 않고 HTML 결과 리포트, 하네스 로그, HTML snapshot 참조, 전후 이미지 참조가 존재하는지 검사한다.

## 4. `.target/`은 참고용이다

`.target/` 디렉토리는 AI가 도달해야 할 "완료된 상태"의 스냅샷이다.

- `npm run harness` 실행에 포함되지 않는다 (`package.json` 스크립트가 명시적 파일 목록만 검사).
- 라이브 시연 백업으로만 사용한다. `.target/` 내용을 코드에서 import하지 않는다.
- 베이스라인이나 하네스 로직이 변경되면 `.target/`도 함께 갱신해야 한다 — 그렇지 않으면 백업 시드가 더 이상 검사를 통과하지 못한다.

## 5. 단위 테스트 입력은 self-contained로 유지

`tests/unit/status.test.mjs`는 `status.config.json`을 읽지 않고 테스트 함수 내부에서 input을 만든다. 베이스라인이 바뀌어도 영향받지 않도록 이 구조를 유지한다.
