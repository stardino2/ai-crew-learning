# .target — 시연 목표 상태 스냅샷

이 디렉토리는 **AI(또는 시연자)가 베이스라인에서 도달해야 할 "완료된 상태"의 참고 스냅샷**이다.

## 이 디렉토리는

- `npm run harness` 실행에 **포함되지 않는다** (`package.json`의 lint/test 스크립트가 명시적인 파일 목록만 검사하므로 자동 제외).
- 시연용 요청("2026-05-20 API Gateway 점검 배너 추가")이 완료된 모습의 6개 파일 사본을 담는다.
- 라이브 시연이 실패하거나 시간이 부족할 때 사용할 **백업 시드**이다.
- 하네스 조건이 실제로 만족 가능한지 검증하는 **레퍼런스**이다.

## 사용법

라이브 시연에서 AI 작업이 막혔을 때, `.target/`의 일부 또는 전체를 상위 디렉토리로 복사해 원하는 단계의 상태를 만든다.

```powershell
# 완전 통과 상태로 점프
Copy-Item -Recurse -Force .target\* .

# "AI가 docs를 빠뜨린" 실패 상태 재현 (docs/ops-notice.md만 제외하고 복사)
Copy-Item -Force .target\status.config.json .
Copy-Item -Force .target\public\* public\
Copy-Item -Force .target\CHANGELOG.md .
# docs/ops-notice.md는 베이스라인 그대로 둠
npm run harness  # docs check 실패가 발생
```

## 주의

`.target/` 자체는 베이스라인 저장소의 "정답" 사본일 뿐이다. 하네스 검사의 **기대값은 `.target/`이 아니라 `status.config.json`에서 derive된다.** `.target/`을 바꿔도 검사 동작은 바뀌지 않는다.
