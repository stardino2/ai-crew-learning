# 2-3 Minute Demo Script

## 0:00-0:20 - Request

Show the prompt:

```text
현재 상태 페이지에 예정 점검 배너를 추가해줘.
- 점검 시간은 2026-05-20 19:00-20:00 KST
- 영향 서비스는 API Gateway
- 사용자가 첫 화면에서 바로 볼 수 있어야 함
- 운영 공지 문구도 함께 업데이트해줘
```

Narration: "AI에게 단순 코드 변경이 아니라 운영 가능한 변경을 요청합니다."

## 0:20-0:55 - AI Change

Show changed files:

- `status.config.json`
- `public/app.js`
- `public/styles.css`
- `docs/ops-notice.md`

Narration: "변경은 UI, 설정, 문서에 걸쳐 생깁니다."

## 0:55-1:25 - Harness Failure

Show `npm run test:docs` failing because the operations notice is incomplete.

Narration: "하네스는 AI를 막는 장치가 아니라, 빠진 운영 조건을 즉시 드러내는 장치입니다."

## 1:25-2:05 - Fix and Pass

Show the notice fixed and `npm run harness` passing.

Narration: "사람이 매번 같은 체크리스트를 들고 보는 대신, 합의된 기준이 자동으로 실행됩니다."

## 2:05-2:30 - Final Result

Show the status page with the maintenance banner and the operations notice.

Narration: "결과는 코드 변경이 아니라, 검증된 운영 가능한 변경입니다."

