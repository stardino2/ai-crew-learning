# Cline Usage — Live Demo Prompts

이 파일은 VSCode + Cline을 사용한 라이브 시연에서 청중 화면에 띄울 **붙여넣기용 프롬프트**를 담는다. Cline은 시작 시 `AGENTS.md`를 읽고 Work Principles에 따라 아래 프롬프트 한 줄만으로 Step 1–5를 자동 수행한다.

---

## Prompt A — 기능 요청 (단일 프롬프트, Step 1–5 자동)

청중에게 Cline 입력창에 붙여넣는 모습을 보여준다.

```
[예시 feature 요청 프롬프트]
```

Cline은 `AGENTS.md`를 읽고 다음을 순서대로 실행한다:

| Step | 화면에 보이는 것 |
|---|---|
| 0 | `sh scripts/demo-trace.sh reset` — 로그 파일 초기화 배너 |
| 1 | `git worktree add ../lecture0419-wt/<feature-branch> -b <feature-branch>` + `cd` |
| 2 | `plans/active/<feature>.md` 작성 (Cline이 즉석 생성) |
| 3 | `demo/src/engine/<feature>.js` 작성 (pure functions) |
| 4 | `demo/index.html` + `demo/src/ui/input.js` 업데이트 |
| 5 | `demo/tests/<feature>.test.js` 작성 + `npx vitest run` green |

각 step 앞에 터미널에 `═══ Step N — 제목 ═══` 배너가 찍힌다. 동시에 `logs/demo-trace.md`에 시간 스탬프 기록이 남는다.

### 발표자 보조 설명 (각 step 사이 10–15초)

- Step 1 찍힐 때: "메인 브랜치를 건드리지 않는 격리된 작업 공간을 만듭니다."
- Step 2 찍힐 때: "Cline이 코드보다 **계획**을 먼저 씁니다 — Context engineering."
- Step 3 찍힐 때: "`engine/` 폴더는 순수 함수만. DOM 호출 금지가 **architectural constraint**입니다."
- Step 5 vitest green: "실패 가능한 검증 루프 — computational feedback."

### 만약 Cline이 멈추거나 잘못된 경로로 가면

- 가장 흔한 실패: Step 1 후 Cline이 워크트리로 `cd` 안 하고 원래 폴더에 파일을 씀 → `.husky/pre-commit` Step 1에서 차단됨 ("main branch direct commit")
- 복구: *"이어서 Step 2부터 `D:/workspace/lecture0419-wt/<feature-branch>/` 기준으로 진행해줘"* 추가 프롬프트

---

## Prompt B — Hook 차단 시연 (Step 6, 별도 트리거)

Prompt A가 끝나고 Step 5의 `vitest green`까지 확인한 뒤, **두 번째 프롬프트**를 붙여넣는다.

```
이제 harness 훅이 실제로 나쁜 커밋을 막는지 3종으로 보여줘.
1) main 직접 커밋
2) plan 없는 커밋
3) 깨진 테스트 커밋
모두 실패한 뒤, 정상 상태로 복구해서 성공 커밋까지 보여줘.
```

Cline은 다음을 순서대로 수행한다:

### 빨강 ① — main 직접 commit

```bash
sh scripts/demo-trace.sh "Red ① — main 직접 commit"
git checkout main
git add -A && git commit -m "test: direct to main"
# → ❌ Direct commits to main branch are not allowed.
git checkout <feature-branch>
```

### 빨강 ② — plan 없는 commit

```bash
sh scripts/demo-trace.sh "Red ② — plan 없는 commit"
mv plans/active/<feature>.md /tmp/
git add -A && git commit -m "test: no plan"
# → ❌ No plan file found in plans/active/
mv /tmp/<feature>.md plans/active/
```

### 빨강 ③ — 깨진 테스트 commit

```bash
sh scripts/demo-trace.sh "Red ③ — 깨진 테스트 commit"
# <feature>.test.js에 expect(1).toBe(2) 임시 추가
git add -A && git commit -m "test: failing assertion"
# → ❌ verify-tasks 실패
# 테스트 복구
```

### 초록 — 정상 커밋

```bash
sh scripts/demo-trace.sh "Green — 정상 커밋"
git add -A && git commit -m "feat: add <feature>

Plan: plans/active/<feature>.md"
# → ✅ pre-commit checks passed
```

발표자 멘트:
> "Prompt에 '하지 마' 쓰는 것과 급이 다릅니다. Architectural constraints는 말이 아니라 **실패로** 막는 장치입니다."

---

## Fallback (Cline 전체 실패 시)

Cline이 응답하지 않거나 계속 잘못된 경로를 쓰면 즉시 전환:

```bash
git checkout after-complete
# 브라우저 새로고침: demo/index.html?after
```

그리고 슬라이드로 복귀해서 `presentation/slides/index.html` Step 6 슬라이드를 말로 내레이션한다.
