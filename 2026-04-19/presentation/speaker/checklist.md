# Live Demo Checklist — 발표자용

> 이 파일을 강의 직전에 한 번 훑으세요.
> 각 단계를 수행하면서 체크하세요.

---

## 사전 준비 (강의 시작 전)

- [ ] VSCode에서 `D:/workspace/lecture0419` 열기
- [ ] Cline 확장 활성화 확인
- [ ] `npx vitest run` 한 번 돌려서 11개 green 확인
- [ ] `demo/index.html` 브라우저에서 열어두기 (Before 상태)
- [ ] GitHub origin 연결 확인: `git remote -v` → `https://github.com/stardino2/lecture0419-harness.git`
- [ ] `plans/active/` 비어 있는지 확인
- [ ] 터미널 폰트 크기 키우기 (청중이 보기 쉽게)

---

## 슬라이드 1–5 진행 중 (발표자 직접 설명)

코드 건드리지 않음. 슬라이드만 진행.

---

## 라이브 시연 (슬라이드 6 구간 / 5:00–9:00)

### Step 1–5 — 단일 프롬프트 (Cline 자동)

Cline 입력창에 **이 한 문장만** 붙여넣는다 (`presentation/cline-usage.md` Prompt A):

```
[예시 feature 요청 프롬프트]
```

Cline은 `AGENTS.md`에 따라 자동으로 다음을 실행한다:

- Step 0 — `sh scripts/demo-trace.sh reset` (로그 초기화)
- Step 1 — `git worktree add ../lecture0419-wt/<feature-branch> -b <feature-branch>` + `cd`
- Step 2 — `plans/active/<feature>.md` 생성
- Step 3 — `demo/src/engine/<feature>.js` 구현 (pure)
- Step 4 — `demo/index.html` + `demo/src/ui/input.js` 연동
- Step 5 — `demo/tests/<feature>.test.js` 작성 + `npx vitest run` green

터미널에 `═══ Step N — 제목 ═══` 배너가 각 단계마다 찍히고, `logs/demo-trace.md`에 시간 스탬프로 기록된다.

- [ ] Cline 프롬프트 입력
- [ ] 터미널에 Step 1–5 배너 순차 출력 확인
- [ ] 최종 vitest green 확인 (11+ tests)
- [ ] 각 배너 찍힐 때 10–15초 청중 설명 (Step 1: worktree / Step 2: plan / Step 3: pure engine / Step 5 green: feedback loop)

### Step 5b — Screenshot 저장 (수동)
- [ ] 터미널 green 화면 스크린샷 → `logs/<date>-after-test.png`
- [ ] `demo/index.html?after` 브라우저에서 생년월일 입력 → UI 스크린샷 → `logs/<date>-after-ui.png`

### Step 6 — Hook 차단 시연 (두 번째 Cline 프롬프트)

`presentation/cline-usage.md` Prompt B를 붙여넣는다:

```
이제 harness 훅이 실제로 나쁜 커밋을 막는지 3종으로 보여줘.
1) main 직접 커밋  2) plan 없는 커밋  3) 깨진 테스트 커밋
모두 실패한 뒤, 정상 상태로 복구해서 성공 커밋까지 보여줘.
```

Cline이 자동으로 빨강 3종을 실행 → 각 차단 메시지 확인 → 복구 → 정상 커밋 green까지 수행한다.

- [ ] 빨강 ① main 직접 — `❌ Direct commits to main branch are not allowed` 확인
- [ ] 빨강 ② plan 없음 — `❌ No plan file found in plans/active/` 확인
- [ ] 빨강 ③ 깨진 테스트 — `❌ verify-tasks` 실패 확인
- [ ] 초록 — `✅ pre-commit checks passed` 확인
- [ ] 청중에게 설명: "Architectural constraints — 말이 아니라 실패로 막습니다"

### Step 7 — Push & Merge
```bash
git push origin <feature-branch>
git checkout main
git merge <feature-branch>
git push origin main
```
- [ ] GitHub에서 main 반영 확인 (선택: 화면 공유)

### Step 8 — Plan 이동 (Garbage collection 시연)
```bash
mv plans/active/<feature>.md plans/completed/
# main 직접 commit이므로 hook bypass (housekeeping 예외)
git add -A && git commit --no-verify -m "chore: complete <feature> plan"
git push origin main
```
- [ ] `plans/completed/<feature>.md` 이동 확인
- [ ] 청중에게 설명: "Garbage collection — 완료된 context를 정리합니다"

---

## 폴백 계층

| 상황 | 대응 |
|---|---|
| Cline 안 됨 | 미리 작성한 feature 구현 diff 보여주고 코드 설명 |
| 시연 3분 초과 | `git checkout after-complete && open demo/index.html?after` |
| 전체 시연 불가 | `presentation/slides/index.html` 슬라이드만 넘기며 내레이션 |

---

## 리허설 체크리스트

- [ ] 통째 타이머 리허설 2회 (10분 초과 시 Slide 5 대본 30초 단축)
- [ ] 시연 성공 케이스 (3분 내 완료)
- [ ] Cline 폴백 케이스 (미리 작성 코드 설명, 3분 내)
- [ ] `after-complete` 긴급 점프 (10초 내)
- [ ] 동료에게 "3 pillar가 뭐예요?" 질문 → 즉답 나오면 성공

---

## 마무리 발언 (Closing)

> "Harness engineering도 하나의 흐름입니다.
> 오늘 본 3 pillar와 8단계를 무조건 따르기보다,
> 여러분의 repo, 팀, 정책에 맞추어 조정해서 쓰시는 것이 가장 좋습니다."
