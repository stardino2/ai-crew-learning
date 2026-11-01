# 근거 자료와 재현 안내

보고서의 메일 34/100, 라우팅 90/100은 아래 집계와 실행 기록으로 확인할 수 있다. 공개 자료를 추가하는 과정에서 모델 추론을 다시 실행하지 않았다.

| 자료 | 확인할 내용 |
|---|---|
| [메일 집계](eval_results/baseline-20261030/summary.json) | 성공·오류 수, 일치율, 언어·분할·클래스별 지표 |
| [메일 실행 설정](eval_results/baseline-20261030/run-manifest.json) | 모델·스냅샷·장치·온도, 튜닝 미실시 |
| [라우팅 집계](eval_results/routing-baseline-20261030/summary.json) | 일치율, Macro-F1, 혼동 행렬, 지연시간 |
| [라우팅 문항별 결과](eval_results/routing-baseline-20261030/results.json) | 합성 100문항의 예측과 잠정 정답 비교 |
| [라우팅 실행 설정](eval_results/routing-baseline-20261030/run-manifest.json) | 지시문, 분류 기준, 동결 데이터·코드 해시 |
| [합성 라우팅 100문항](data/routing_eval.json) | 입력, 잠정 정답, 근거, 언어와 분할 |
| [라우팅 프로토콜](tasks/routing-protocol.json) | 과업 정의와 데이터 제약 |
| [파일 출처·수정 이력](provenance.json) | 로컬 원본 및 공개본 SHA-256, 수정 내역 |

## 재현

이 폴더를 작업 디렉터리로 사용한다. 평가 코드는 Python 표준 라이브러리만 사용한다. 모델 서버 설치는 별도로 필요하며 모델 가중치를 내려받는다.

```powershell
python routing_test.py --validate-only
python -m unittest discover -p "test_*test.py"

git clone https://github.com/jaredpalmer/kev.git vendor/kev
uv sync --project vendor/kev --extra serve --no-dev
uv run --project vendor/kev --no-dev python -m kev.serve --run jaredpalmer/kev-0.8b@v1.0 --port 8009 --device cpu
```

서버가 준비되면 다른 터미널에서 같은 작업 디렉터리로 이동해 실행한다.

```powershell
python routing_test.py --output-dir eval_results/routing-new-run
python mail_demo.py
```

`mail_demo.py`는 함께 제공한 합성 더미 15건의 예비 실행이다. 실제 메일 100건을 재현하는 입력 데이터는 공개하지 않았다. `kev_test.py`와 `test_kev_test.py`는 평가 구현을 확인하기 위한 자료이며, 공개된 메일 집계만으로 원본 메일 평가를 독립 재현할 수는 없다. 실행 환경·캐시 등에 따라 지연시간은 달라질 수 있다.

## 해석과 공개본 변경

- 정답은 잠정 AI 라벨이다. 사람 검수 정확도나 실사용 성능 보증으로 해석하지 않는다.
- 합성 라우팅은 실제 도구 실행이 아니며 공식 지원 범위 밖의 진단이다.
- 메일 집계의 모델·장치가 `unknown`인 원래 메타데이터는 보존했다. 별도 실행 설정에 검증된 식별 정보가 있다.
- 라우팅 집계의 확률 설명은 릴리스 온도 보정 적용 사실에 맞게 수정했다. 해당 라우팅 분포에서의 보정 품질은 미검증이다. 지표 수치는 바꾸지 않았다.
- 실행 설정의 로컬 절대 경로 접두사는 제거했다. 공개본은 UTF-8/LF로 저장해 원본과 바이트 해시가 다를 수 있다.
- 실제 메일 문항·주소·본문·ID, 원본 메일 요청·응답, 인증 정보, 작업자 로그 및 모델 가중치는 제외했다. 합성 라우팅 문항 속 인물·주소·도구는 시나리오 데이터다.

## 이번 공개 패키지 검증

합성 라우팅 100건 스키마·클래스 균형·언어·분할 검증 통과. 단위 테스트 35건 중 34건 통과. 나머지 로컬 HTTP 모의 서버 테스트 1건은 현재 실행 환경의 소켓 접근 제한(`WinError 10013`)으로 실패했다. 이는 과거 모델 평가 결과를 재실행한 검증이 아니며, 이번에 전체 테스트 통과로 보고하지 않는다.
