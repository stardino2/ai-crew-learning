# mini-status-harness

Harness Engineering 시연용 소형 상태 페이지 프로젝트. 외부 런타임 의존이 없도록 의도적으로 단순하게 만들어졌다.

## Baseline

저장소 커밋 상태는 **"점검 일정 없음" 베이스라인**이다.

- `status.config.json`의 `maintenance.enabled`가 `false`
- 모든 서비스 `operational`
- `public/index.html`/`app.js`/`styles.css`에 점검 배너 요소/렌더러/스타일 없음
- `docs/ops-notice.md` / `CHANGELOG.md`는 빈 템플릿
- `ops/maintenance-events.ndjson`는 없거나 비어 있음
- `reports/latest/index.html`은 실행 전 placeholder

이 상태에서 `npm run harness`는 통과한다. 모든 레이어가 "점검 없음"으로 일관되기 때문이다.

## Demo Request

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

이 요청을 만족하면 다음 레이어가 변경된다:

| 레이어 | 변경 |
| --- | --- |
| `status.config.json` | `maintenance.enabled: true` + 일정/서비스/메시지 |
| `public/index.html` | `#maintenance-banner` section 추가 |
| `public/app.js` | `renderMaintenance` 함수 + 호출 |
| `public/styles.css` | design token 기반 `.maintenance-banner*` 규칙 |
| `docs/ops-notice.md` | 2026-05-20 공지 |
| `CHANGELOG.md` | 변경 이력 |
| `ops/maintenance-events.ndjson` | `maintenance.scheduled` audit 이벤트 |
| `reports/latest/` | HTML 결과 리포트, 하네스 로그, HTML snapshot, 이미지 참조 |

## Run

```powershell
npm start
```

`http://localhost:4173` 접속. 베이스라인에서는 서비스 카드 3개만 표시된다.

## Harness

```powershell
npm run harness
```

기본 6단계 검사:

1. **lint** — Node 구문 검사
2. **test:unit** — `summarizeStatus` / `publicStatusPayload` 단위 테스트
3. **test:config** — `status.config.json` schema
4. **test:contract** — `/api/status` payload shape
5. **test:ui** — UI에 필요한 요소 존재 여부
6. **test:docs** — config의 점검 일정과 문서 내용의 일관성

검사 3~6은 모두 `status.config.json`에서 기대값을 derive 한다. 즉 **config에 점검을 등록하면 UI/docs가 따라와야 하고, 등록하지 않으면 아무것도 요구하지 않는다.** 이것이 cross-layer 일관성 검사이다.

점검 배너 작업은 추가 checkpoint까지 통과해야 완료된다:

```powershell
npm run test:design
npm run test:ops-log
npm run report:check
npm run maintenance:complete
```

`maintenance:complete`는 `harness + design + ops-log + report`를 묶은 최종 완료 게이트다.

## Layer Checkpoints

점검 배너를 구현할 때는 아래 순서로 실행한다.

1. config 수정 후 `npm run test:config`
2. API payload 확인 후 `npm run test:contract`
3. UI 수정 후 `npm run test:ui` 와 `npm run test:design`
4. docs/log 수정 후 `npm run test:docs` 와 `npm run test:ops-log`
5. 리포트 작성 후 `npm run report:check`
6. 마지막에 `npm run maintenance:complete`

이 흐름은 watch hook은 아니지만, 구현 중간에 하네스가 어느 레이어의 누락을 잡는지 발표 화면에 그대로 남긴다.

## Suggested Recording Beats

1. 베이스라인에서 `npm run maintenance:complete` 실행 → maintenance off 경로까지 모두 통과.
2. AI에게 위의 **Demo Request** 를 입력.
3. AI가 `AGENTS.md`의 checkpoint 규칙에 따라 구현과 검사를 진행하는 과정을 보여준다.
4. `npm run maintenance:complete` 통과 로그를 보여준다.
5. `npm start`로 페이지 새로고침 → 점검 배너가 노출됨.
6. `reports/latest/index.html`을 열어 하네스 결과, 로그, snapshot, ops-log 요약을 확인한다.

실패 장면은 필수 시연 요소가 아니다. 실패 없이 끝나면 HTML 결과 리포트를 최종 증거로 보여준다.
