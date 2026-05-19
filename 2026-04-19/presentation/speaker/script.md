# 강의 대본 — Harness Engineering 10분 강의

> 슬라이드별 발표자 내레이션. `slides/index.html`과 나란히 사용.
> 데모 단계 체크리스트는 `speaker/checklist.md` 참조.

## 발표 운영 메모

- **Slide 5·7·9**에 3 pillar 아이콘(Context/Constraints/Collection) 항상 노출 → 마무리에서 자동 기억
- **시연 페이지**: Slide 8 진입 직전 새 창에서 `presentation/slides/demo.html` 열어 Cline IDE 옆(좌·우 반반)에 배치.
- **다크/라이트 토글**: 회의실 조명에 따라 좌측 상단 🌗 버튼으로 전환. 상태는 창별 localStorage에 저장 (키: `harness-theme`).
- **시간 리스크**: 라이브 시연이 가장 위험. 5분 지나면 `after-complete` tag 체크아웃으로 즉시 점프
- **마무리 1분 절대 포기 금지** — "agent가 사는 집" 한 줄이 안 가면 강의 목적 무너짐
- **Cline 차단 시**: 미리 작성된 feature 구현 diff를 화면에 띄우고 코드 설명으로 대체
- **유머 2개**(권투·뷔페)는 분위기 보고 뺄 수 있음 — 반응 없으면 바로 다음 포인트로 진행 (강아지 비유는 Slide 2·3에 내장되어 생략 불가)
- Q&A는 10분 **밖**으로 분리 안내

---

## Slide 1 — Opening (0:00–0:30)

**제목:** "Harness Engineering — 어려워 하지 마세요"

> 안녕하세요 여러분! 소중한 시간 내어 참석해 주셔서 감사합니다.
> 하네스 엔지니어링에 대해 소개해드리려고 합니다.

> 오늘 저는 클로드나 Codex 대신 VSCode의 Cline이라는 확장을 씁니다.
> 사내 환경에서 클로드나 Codex CLI 접근이 안 되는 분들이 많으실 텐데 — 도구는 달라도 오늘 배울 원리는 완전히 동일합니다.

> Prompt engineering, Context engineering, 이젠 Harness engineering.
> 오늘 10분 동안 이게 뭔지, 왜 나왔는지, 어떻게 적용하는지 간략히 정리해드립니다.
> 마지막 4분은 하네스 사용법을 라이브로 보여드립니다.

> (브릿지) 그런데 '하네스'가 뭘까요? 구글에 검색해 보면 제일 먼저 이런 이미지가 뜹니다 —

---

## Slide 2 — 비유: 강아지와 하네스 (0:30–0:55)

**화면 지시:** 강아지 사진 두 장을 손짓으로 가리킴

> 그렇습니다. 강아지 가슴줄이죠. (웃음)
> 그런데 이 하네스가 왜 필요한지 잠깐 생각해 보시면 — 똑똑하고 활발한 강아지일수록 방향 없이 달리면 보호자도 힘들고, 강아지도 위험합니다.
>
> 하네스는 강아지를 **묶는** 장치가 아니라, 보호자와 강아지가 **같은 방향으로 멀리 갈 수 있게** 해주는 장치입니다.
> 잘 채워야 원하는 곳까지 같이 도달할 수 있습니다.

---

## Slide 3 — 비유: AI Agent = 로봇 강아지 (0:55–1:20)

**화면 지시:** 로봇 강아지 이미지로 전환 — 손짓 강조

> 이제 이 강아지가 CPU와 토큰으로 달린다고 상상해 보세요.
> 그게 오늘의 AI 코딩 에이전트입니다.
>
> 많은 분이 오해하시는 게 — "AI가 똑똑해지면 통제할 필요 없어지지 않나요?" 인데,
> 오히려 반대입니다. 똑똑해지고 힘이 세질수록, 엉뚱한 방향으로 달렸을 때의 파급이 커집니다.
> 그래서 하네스는 **여전히, 오히려 더** 필요합니다.
>
> 오늘 얘기할 하네스 엔지니어링은 이 로봇 강아지에게 채우는 목줄이자 안전장치입니다.

---

## Slide 4 — AI로 결국 하고 싶은 것 + 역사 맥락 (1:20–1:50)

**화면 지시:** 중앙의 AI 환경 설계 개념도(`ai_env01.png`) 가리키며

> AI가 내 대신 결과물을 만들어 주려면 — 우리가 AI가 움직이는 **환경**을 잘 설계해야 합니다.
> 이 그림처럼, 에이전트 혼자 일을 하는 게 아니라 에이전트가 일할 **환경**이 함께 설계되어야 한다는 거죠.

**역사 맥락:**
> Harness라는 단어 자체는 새로운 개념이 아닙니다.
> 제어 시스템, DevOps, 테스트 인프라에서 "harness"는 오래전부터 쓰인 용어입니다.
> 2026년 초 OpenAI가 Codex 기반 5개월 실험을 공개 문서로 정리하면서,
> AI coding agent 맥락에서 다시 대중적 관심을 얻게 된 흐름입니다.

---

## Slide 5 — 진화 3단 (1:50–2:20)

```
Prompt engineering   →  말 잘하기 (무엇을 원하는지 설명)
Context engineering  →  히스토리·맥락 주기 (어떤 상황인지 알려주기)
Harness engineering  →  agent가 사는 환경 설계
```

> Prompt engineering은 말을 잘하는 기술입니다.
> Context engineering은 일의 히스토리와 맥락을 주는 겁니다.
> 이제 agent의 역량이 커지면서 — 환경 없이는 엉뚱한 방향으로 달릴 수 있습니다.

**화면 지시:** 하단 말(馬) 이미지 가리키며

> 말(馬) 이미지를 하나 띄워 놨는데요, 아까는 강아지를 보여드렸지만 Harness라는 단어의 **원래 뜻**이 바로 이 마구(馬具)입니다.
> 말의 에너지를 원하는 방향으로 채널링하는 장치 — 조금 전 강아지 하네스와 정확히 같은 개념이죠.
> AI agent에게도 바로 이런 장치가 필요한 겁니다.

---

## Slide 6 — OpenAI 5-Month Experiment (2:20–3:00)

**화면 지시:** 상단 OpenAI 공식 문서 캡처(`openai1.jpeg`) 가리키며

> OpenAI에서 최근 문서가 하나 나왔습니다 — 이 캡처가 그 원문입니다.
> 아마 많은 분이 사내 보안망에 막혀 openai.com 원문 접속이 안 되셨을 겁니다. 제가 요약해드리면 —
> 'AI에게 맨땅에 코드 짜라고 던지지 말고, 실수할 수밖에 없는 AI를 위해 엄격히 통제된 작업 환경, 즉 harness를 씌우자'는 겁니다.
>
> 실제로 어떤 성과가 나왔냐 하면: 5개월 동안, 소규모 팀이, 사람이 직접 쓴 코드 0줄로, 약 100만 줄 규모의 베타 제품을 만들었다는 겁니다.
>
> 어떻게?
> Agent 자체를 바꾼 게 아닙니다.
> Agent가 사는 집 — Harness — 을 바꿨습니다.
>
> OpenAI가 직접 남긴 문장:
> "Most difficult challenges center on designing environments, feedback loops, and control systems."
>
> 오늘은 그 환경을 제 repo 한 개에 옮겨 봅니다.

---

## Slide 7 — 3 Pillar × 2 Axis (3:00–5:00)

> OpenAI는 Harness를 세 가지 pillar로 정리했습니다.

**Pillar ① Context engineering**
> Agent가 "무엇을, 어디서, 왜" 읽을지 구조화하는 것입니다.
> 일반적으로 `AGENTS.md` 와, `각종 plans.md` 작업 계획서가 여기 해당합니다.

**Pillar ② Architectural constraints**
> Agent가 벗어나면 안 되는 경계를 설정하는 것입니다.
> 현재 repo 기준으로 husky 로 작성한 hook 들에 해당합니다.
> `.husky/pre-commit`은 룰 어기면 실제로 commit을 막습니다.
> Prompt에 "하지 마"라고 쓰는 것과 급이 다릅니다.

**Pillar ③ Garbage collection**
> 누적된 context 노이즈를 주기적으로 걸러내는 것입니다.
> `plans/active → completed` 이동, `logs/` 정리, size 제한이 여기 해당합니다.

**(추가) Martin Fowler 2 axis — 20초 체크리스트:**
> 추가로 Martin Fowler의 2 axis 를 소개해드립니다. repo의 harness를 점검할 때 두 축을 씁니다.
> Feedforward vs Feedback — 사전 제약(lint rule, hook)이냐, 사후 검증(test, review)이냐.
> Computational vs Inferential — 결정적 검증(test·type check)이냐, 의미적 검증(LLM review)이냐.
> 이 네 칸 중 어디가 비어 있는지 확인하세요.
> AI가 환각증세나 에러를 일으켜도, 테스트 코드로 해결 가능합니다.

---

## Slide 8 — 라이브 시연 (5:00–9:00)

**요청 — Prompt A (청중 앞에서 Cline에 붙여넣는 **한 문장**):**
> ```
> [예시 feature 요청 프롬프트]
> ```

Cline은 `AGENTS.md`를 읽고 Step 1–5를 자동 수행.
터미널에 `sh scripts/demo-trace.sh "<step>"` 배너가 각 단계마다 찍혀 청중이 진행 상황을 볼 수 있다.
화면 위쪽 파이프라인 다이어그램을 가리키며: "색이 같은 단계는 같은 pillar입니다 — 따라가 보시죠."

**시연 8단계** (세부는 `speaker/checklist.md`):

1. `git worktree add` → **Pillar ①** Context: 메인 건드리지 않고 작업 공간 분리 *(Prompt A 자동)*
2. Cline → `plans/active/<feature>.md` 생성 → **Pillar ①** Agent가 계획부터 씀 *(자동)*
3. Cline → `demo/src/engine/<feature>.js` 구현 → **Pillar ②** engine(pure) 유지 *(자동)*
4. `npx vitest run` → 11 + α tests green → Computational check *(자동)*
5. 스크린샷 → `logs/` → **Pillar ③** 증거 남기기 *(수동 — Win+Shift+S)*

> **Hook(훅)이란?** — 권투의 훅처럼, 어떤 행동 직전(예: 커밋 직전)에 낚아채서 실행되는 검문소 프로그램입니다. `.husky/pre-commit`이 바로 이 역할을 합니다.

6. Hook 차단 시연 — **Prompt B** 붙여넣기 → Cline이 빨강 3종(main 직접 / plan 없음 / 깨진 테스트) 실행 → 모두 ❌ → 복구 → `git commit` → ✅

   **Prompt B 원문** (복붙용 — `presentation/cline-usage.md` §Prompt B 동일):
   ```
   이제 harness 훅이 실제로 나쁜 커밋을 막는지 3종으로 보여줘.
   1) main 직접 커밋
   2) plan 없는 커밋
   3) 깨진 테스트 커밋
   모두 실패한 뒤, 정상 상태로 복구해서 성공 커밋까지 보여줘.
   ```

   > "보셨죠? Architectural constraints — 말이 아니라 실패로 막는 장치입니다."

7. `git push origin <feature-branch>` + merge to main
8. `mv plans/active/... plans/completed/` + commit → **Pillar ③** Garbage collection 시각화

> 계획을 안 써도 막히고, 테스트가 통과 안 되어도 막힙니다. 이게 harness engineering의 진가입니다.

---

## Slide 9 — Closing (9:00–10:00)

**오늘 한 줄:**
> "Agent를 바꾸지 말고, agent가 사는 집을 바꾸세요."

**화면 지시:** 큰 문장 바로 아래 집(`harness-house1.png`) 이미지를 손짓

> 오늘 10분 내내 계속 나온 비유죠 — **agent가 사는 집**.
> 이 집이 바로 harness입니다. 강아지 하네스, 말 마구, 그리고 agent의 집 — 다 같은 얘기입니다.

3 Pillar: **Context engineering / Architectural constraints / Garbage collection**

**다음 걸음:**
1. 이번 주 딱 하나: `AGENTS.md` 목차 한 장 → 반복 설명 반으로 줄기
2. 그 다음: `.husky/pre-commit` 훅 하나 → 말이 아닌 장치로
3. 사내 가이드 추천 순서: week3 → week5 → week8 → week7

**마무리 메시지:**
> Harness engineering도 하나의 흐름입니다.
> 특정 구조에 종속되실 필요 없습니다. 팀 문화와 프로젝트 성격에 맞게 — 뷔페처럼 필요한 파트만 골라 도입하세요.
>
> 기술 트렌드가 자고 일어나면 바뀌는 시대, 기업 AX(AI Transformation) 도입엔 끊임없는 공부가 필요합니다.
> 저도 매일 쏟아지는 기술 보면서 머리 싸매고 공부 중입니다.
> 도입하면서 트러블이 생기면 같이 고민하고 뚫어봤으면 좋겠습니다.
> 끝까지 경청해 주셔서 감사합니다!

Q&A는 10분 **밖**으로 분리.
