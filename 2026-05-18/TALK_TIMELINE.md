# 05/20 Harness Engineering Talk Timeline

Target duration: 9:30 presentation + 0:30 Q&A/source buffer.

| Time | Section | Speaker intent |
| --- | --- | --- |
| 0:00-0:55 | 하네스 비유 | Open with Harness Engineering and explain the dog/robot harness as a metaphor, not a quiz. |
| 0:55-1:50 | 병목 퀴즈 | Ask one quiz: where the AI-workflow bottleneck is. Land on human repeated verification. |
| 1:50-2:50 | 수동 확인을 자동 검증으로 | Explain that repeated manual checks should become automated verification. Use the table headers `사람이 매번 확인` / `자동 검증으로 대체`. |
| 2:50-3:35 | 영역별 적용 예시 | Help operations/docs, FE, BE, and System Engineers map the concept to their own work before the demo. |
| 3:35-4:10 | Industry pattern | Use OpenAI, Claude Code, GitHub Copilot, and DORA as evidence cards for the shared pattern. |
| 4:10-7:05 | 예제 실습 흐름 | Show `요청 → 영향 범위 → 영역별 검증 → 최종 검증 → 결과 리포트` without relying on internet, server, or terminal execution. |
| 7:05-7:55 | 모델이 좋아지면 하네스는? | Explain that better models make harnesses thinner and more precise, not irrelevant. Add the SE point about AI-facing CI feedback. |
| 7:55-9:30 | One-page close + CTA | Close with the summary and ask everyone to find one repeated review/ops question this week as an automation candidate. |
| 9:30-10:00 | Sources + Q&A | Keep source references available and start questions. |

## Closing Line

AI에게 더 많이 맡기고 싶다면, 먼저 검증 흐름을 만드세요.

## CTA Line

이번 주에는 PR 리뷰나 운영 점검에서 같은 질문을 3번 이상 반복한 항목 하나를 자동화 후보로 적어보세요.

## Backup Line for Q&A

Harness Engineering이라는 이름은 아직 정착 중이지만, 자동 테스트, 빠른 피드백, 배포 자동화, 에이전트용 저장소 규칙과 hooks가 가리키는 방향은 일관적입니다.

## Offline Practice Note

발표장 인터넷이 없어도 4:10-7:05 구간은 `slides/standalone.html`과 `slides/assets/`의 캡처만으로 진행한다. 외부 링크, 현장 Codex 입력, `npm start`, 현장 `maintenance:complete` 실행은 말하지 않는다.
