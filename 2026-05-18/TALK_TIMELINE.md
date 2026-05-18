# 05/20 Harness Engineering Talk Timeline

Target duration: 9:30 presentation + 0:30 buffer.

| Time | Section | Speaker intent |
| --- | --- | --- |
| 0:00-1:10 | Icebreaker quizzes | Ask "what is this?" with a dog harness, then ask where the AI-workflow bottleneck is. Land on "harness" and "human verification bottleneck." |
| 1:10-2:00 | Why it matters | Explain that repeated human verification must move into team-owned automated criteria. |
| 2:00-2:55 | Definition | Define Harness Engineering as a runtime environment where AI output passes build, test, review, and ops criteria. |
| 2:55-3:50 | Industry pattern | Use OpenAI, Claude Code, GitHub Copilot, and DORA as evidence cards for the shared pattern. |
| 3:50-7:10 | 예제 실습 흐름 | Show the AI request, AI 수정 범위, Harness 진행 과정, `maintenance:complete` result, final screen, and HTML result report without relying on internet, server, or terminal execution. |
| 7:10-7:55 | 영역별 적용 예시 | Help FE, BE, System Engineer, and operations/documentation owners map the concept to their own work. |
| 7:55-9:25 | Agentic Engineering close | Explain that better models make harnesses thinner and more dynamic, not irrelevant. |
| 9:25-10:00 | Sources + Q&A | Keep source references available and start questions. |

## Closing Line

Agentic Engineering은 AI에게 일을 맡기는 것이 아니라, AI가 한 일을 조직의 검증 흐름에 넣는 것입니다.

## Backup Line for Q&A

Harness Engineering이라는 이름은 아직 정착 중이지만, 자동 테스트, 빠른 피드백, 배포 자동화, 에이전트용 저장소 규칙과 hooks가 가리키는 방향은 일관적입니다.

## Offline Practice Note

발표장 인터넷이 없어도 3:50-7:10 구간은 `slides/standalone.html`과 `slides/assets/`의 캡처만으로 진행한다. 외부 링크, 현장 Codex 입력, `npm start`, 현장 `maintenance:complete` 실행은 말하지 않는다.
