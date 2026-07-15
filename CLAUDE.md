# CLAUDE.md — SampleOrderSystem 작업 지침

이 문서는 이 저장소에서 Claude Code가 지켜야 할 작업 범위와 개발 방식을 정의한다. 기능
요구사항은 `PRD.md`, PoC 재사용/재작성/폐기 분석과 Cycle별 구현 계획·결과는 `docs/PLAN.md`를
따른다. 이 프로젝트는 일반적인 바이브 코딩이 아니라 **Human-in-the-loop 기반 Agentic
Engineering**으로 개발한다.

## 1. 문서 우선순위

1. `PRD.md` — 무엇을 만드는지(기능 명세, 도메인 모델, 통합 JSON 스키마, 재고/생산 규칙)
2. `docs/PLAN.md` — 어떤 순서로 만드는지(PoC 활용 방식, 전체 구조, Cycle별 계획과 실제 결과)
3. 이 파일(`CLAUDE.md`) — 어떻게 작업하는지(승인 관문, TDD, Harness, 범위 통제, Commit/Push)

세 문서가 충돌하면 우선순위가 높은 문서를 따르고, 그 사실을 사용자에게 알린다. **새로운
관리용 Markdown 문서(ARCHITECTURE.md, DECISIONS.md, TRACEABILITY.md, 기능별 별도 Plan 파일
등)는 만들지 않는다.** 필요한 설계 결정·요구사항 연결·구현 계획과 결과는 전부 이 세 문서 안에
통합한다.

## 2. Skill 적용 우선순위

이 프로젝트는 아래 두 Skill을 작업 규칙으로 적용한다. 두 Skill이 충돌하면 1번이 우선한다.

1. **`SKILL.md` (agentic-tdd)** — 사람 승인 관문(RED Plan 승인 → RED Test Code 승인 → GREEN
   구현 후 REVIEW 승인 → Commit)과 작업 범위 통제가 최우선이다. 사람의 명시적 승인 없이는
   다음 단계로 넘어가지 않는다(Iron Law 1~5, `SKILL.md` 참고).
2. **`SKILL_tdd.md` (test-driven-development)** — 그 안에서 실제 코드를 작성하는 방식은
   테스트 우선(Red-Green-Refactor)을 따른다. 실패하는 테스트 없이 프로덕션 코드를 작성하지
   않는다(Iron Law: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST).

즉 "언제 사람에게 물어보고 언제 멈추는가"는 `SKILL.md`가, "코드를 어떤 순서로 작성하는가"는
`SKILL_tdd.md`가 규정한다.

## 3. Pre-Action Commit Gate

최초 기능 구현(테스트 코드 포함)을 시작하기 전에, 아래 Commit이 **원격 저장소에 push된 상태로**
존재해야 한다. 하나라도 push되지 않았다면 테스트 코드도 프로덕션 코드도 작성하지 않는다.

1. `PRD.md` 요구사항 Commit
2. `CLAUDE.md` Agentic Engineering 작업 규칙 Commit
3. `docs/PLAN.md` PoC 통합 및 전체 개발 계획 Commit
4. 자동 검증 Harness Commit
5. 현재 작업할 Cycle의 `docs/PLAN.md` RED Commit (해당 Cycle의 Plan이 승인되어 커밋된 상태)

이 게이트는 최초 기능뿐 아니라 **이후의 모든 기능(Cycle)에도 동일하게 적용**된다 — 새 Cycle을
시작하려면 그 Cycle의 RED Plan Commit이 먼저 push되어 있어야 한다.

## 4. PLAN.md는 Living Plan이다

`docs/PLAN.md`는 최초 1회 작성으로 끝나는 문서가 아니라, 프로젝트 전체 기간 동안 각 Cycle의
계획과 실제 결과를 계속 추가·수정하는 문서다. **모든 기능 Cycle은 `docs/PLAN.md`가 최소 두 번
Commit 이력에 포함되어야 한다:**

1. **RED Commit** (기능 시작 전): 해당 Cycle의 계획을 `docs/PLAN.md`에 작성 → 사용자 승인 →
   `docs/PLAN.md`만 Commit하고 Push. 이 시점에는 테스트/구현 코드가 없다.
2. **GREEN Commit** (기능 완료 후): 실제 구현 결과와 테스트 결과를 같은 Cycle 항목에 기록 →
   구현 코드·테스트 코드와 함께 Commit하고 Push.

`docs/PLAN.md` 갱신 없이 기능 구현 Commit을 만들지 않는다.

## 5. 기능별 Agentic TDD Cycle 절차

각 기능은 테스트 함수 하나가 아니라, 독립적으로 확인 가능한 **Vertical Slice** 단위(예: "재고가
부족한 주문 승인과 생산 큐 등록")로 진행한다. Cycle 목록은 `docs/PLAN.md` 3장 참고. 각 Cycle은
아래 순서를 반드시 지킨다.

1. **Plan 작성** — `docs/PLAN.md`에 해당 Cycle의 Plan(현재 상태/목표/관련 요구사항/포함
   범위/제외 범위/Acceptance Criteria/예정 테스트 목록/구현 접근 방식/변경 예정 파일/Harness
   명령/RED·GREEN Commit 계획/완료 조건)을 작성한다. **작성 후 테스트나 구현을 시작하지 않고
   사용자에게 승인을 요청한 뒤 멈춘다.**
2. **RED Plan Commit** — 승인 후 `docs/PLAN.md`만 별도 Commit하고 Push한다
   (`RED N: plan <feature>`). 이 Commit 전에는 테스트 코드도 작성하지 않는다.
3. **Test Code 작성과 승인** — 승인된 Plan 범위의 테스트 코드만 작성한다(프로덕션 코드 없음).
   사용자에게 테스트 코드와 의도를 보여주고 Acceptance Criteria를 올바르게 표현하는지 승인을
   요청한다. 승인 전에는 테스트 실행과 구현으로 넘어가지 않는다.
4. **RED 확인** — 테스트를 실행해 실제로 실패하는지, 문법/import 오류가 아니라 기능 부재로
   실패하는지, Plan에서 예상한 이유와 일치하는지 확인한다. 처음부터 통과하면 어떤 기존 구현이
   해당 동작을 커버하는지 설명하고 유효한 회귀 테스트인지 사용자 확인을 받는다.
5. **GREEN 구현** — 실패 테스트를 통과시키는 최소한의 코드만 작성한다. Plan에 없는 기능 추가,
   다음 Cycle 선구현, 요청받지 않은 구조 변경, 겸사겸사 리팩터링, 테스트보다 먼저 구현 코드
   작성은 금지한다. Plan 범위를 벗어나야 할 필요가 생기면 즉시 중단하고 `docs/PLAN.md`를
   수정해 재승인받은 뒤(필요 시 추가 RED Commit) 계속한다.
6. **Harness 실행** — `python scripts/verify.py` 하나로 통일한다(문법/import 검사, `pytest`
   전체 실행, 경고·오류 확인, 필요 시 `ruff`). **Harness가 실패하면 완료를 선언하지 않는다.**
7. **REVIEW** — 변경된 파일, 구현한 요구사항, 추가된 테스트, RED 실패 결과, GREEN 테스트
   결과, 전체 Harness 결과, Plan 대비 범위 이탈 여부, 남은 위험을 사용자에게 보고한다. **아직
   Commit하지 않고 리뷰 승인을 요청한 뒤 멈춘다.**
8. **GREEN Commit** — 승인 후 `docs/PLAN.md`의 해당 Cycle에 실제 결과(상태: Completed, 실제
   변경 파일, 테스트 수와 결과, Harness 결과, 계획 대비 변경 사항, 범위 이탈 여부, 남은 후속
   작업)를 기록하고, 구현 코드·테스트 코드·갱신된 `docs/PLAN.md`를 함께 Commit하고 Push한다
   (`GREEN N: implement <feature>`).

## 6. Hard Rules (승인/Commit 관련)

- 승인된 Plan Commit(push 완료) 없이 구현 Action을 시작하지 않는다.
- Plan 파일을 작성만 하고 Commit·Push하지 않은 상태에서 구현하지 않는다.
- Plan Commit과 구현 Commit을 하나로 합치지 않는다.
- 여러 기능을 하나의 Plan이나 하나의 구현 Commit으로 묶지 않는다.
- Plan에 없는 기능을 임의로 구현하지 않는다. 추가 요구사항을 발견하면 구현을 중단하고 Plan을
  수정한 뒤 재승인받는다.
- 테스트가 먼저 실패하는 것을 확인하기 전에는 구현하지 않는다.
- Harness가 실패한 상태에서는 완료를 선언하지 않는다.
- **사용자 리뷰 승인 전에는 어떤 Commit도 생성하지 않는다.**
- Commit 후 가능한 경우 즉시 Push하여 개발 기록을 남긴다.

## 7. 작업 범위 통제

- **PRD.md에 없는 기능을 추가하지 않는다.** 다중 사용자 인증, 실시간 생산 시뮬레이션, 다중
  생산 라인, 외부 DB, 동시 승인 오버셀 방지 등은 명시적으로 범위 밖이다(PRD.md 8장 참고).
- **PoC 리포지토리를 직접 참조하지 않는다.** `../ConsoleMVC`, `../DataPersistence` 등 상대 경로
  import나 파일 복사를 하지 않는다. 이 프로젝트는 자기 완결적이어야 한다.
- **도메인 모델은 하나만 유지한다.** `src/sample_order_system/model/`에 정의된 Sample/Order/
  OrderStatus/ProductionQueueItem 외에 유사한 데이터 클래스를 다른 곳에 새로 만들지 않는다.
- **Cycle 순서를 임의로 건너뛰지 않는다.** 이전 Cycle의 GREEN Commit이 끝나지 않은 상태에서
  다음 Cycle의 세부 구현으로 넘어가지 않는다. 순서를 바꿔야 할 이유가 생기면 먼저
  `docs/PLAN.md`를 갱신해 재승인받는다.
- **큰 리팩터링이나 구조 변경은 먼저 계획을 설명하고 사용자 확인 후 진행한다.** 특히 통합
  JSON 스키마나 도메인 모델 필드를 변경하는 결정은 `PRD.md`를 함께 수정한 뒤 진행한다.

## 8. Harness (자동 검증 체계)

- 실행 명령은 `python scripts/verify.py` 하나로 통일한다. 최소한 다음을 포함한다: Python
  문법/import 검사, `pytest` 전체 실행, 테스트 경고·오류 확인, 필요 시 `ruff` 검사.
- **저장 전 검증**: Repository의 모든 쓰기 경로(등록/승인/생산완료/출고)는 저장 직전에 도메인
  검증(참조 무결성, 값 범위)을 통과해야 한다. 검증 실패 시 예외를 던지고 파일을 변경하지 않는다.
- **콘솔 동작 확인**: UI/컨트롤러를 변경했을 때는 실제로 `python main.py`를 실행해 해당 메뉴
  흐름이 에러 없이 동작하는지 최소 1회 수동으로 확인한다(자동 테스트로 대체할 수 없는 부분).
- **테스트 위치**: `tests/`에 모듈 단위로 대응하는 테스트 파일을 둔다(`test_<module>.py`).
  실제 `data/` 아래 JSON 파일은 테스트에서 수정하지 않으며, `tmp_path`를 사용한다.

## 9. CleanCode 원칙

- 각 계층(Model/Repository/Service/Monitor/Controller/View)의 책임을 넘나드는 코드를 두지
  않는다. 예: View에서 재고 계산을 하거나, Model에 파일 I/O를 넣지 않는다.
- 주석은 WHY가 비자명할 때만 남긴다(예: 계산식의 근거, 특정 순서가 필요한 이유).
- 과도한 추상화/클래스 분리를 피한다. 함수형으로 표현 가능한 로직은 함수로 둔다(DataMonitor,
  DummyDataGenerator PoC에서 검증된 스타일).
- 코드 식별자는 영어를 사용하고, 응답/설명/문서는 한국어로 작성한다.

## 10. Commit 이력 규칙

초기 문서·환경은 논리적으로 분리한다.

- `docs: define product requirements`
- `docs: define agentic development workflow`
- `docs: add PoC integration and implementation plan`
- `chore: add automated verification harness`

각 기능 Cycle은 최소 두 Commit(`RED N: plan <feature>`, `GREEN N: implement <feature>`)을
가진다. 계획이 변경되면 추가 RED Commit을 남긴다(예: `RED 4: revise inventory allocation
plan`). Commit 수를 인위적으로 늘리는 것이 목적이 아니다 — 각 Commit은 하나의 논리적 변경만
포함하고, Git 이력만 보아도 "어떤 기능을 계획했는가 / 언제 승인되었는가 / 어떤 테스트를
작성했는가 / 어떤 기능을 구현했는가 / 계획이 어떻게 변경되었는가 / 언제 Harness가
통과했는가"를 파악할 수 있어야 한다.

## 11. 실행 환경

- Python 3.12, 표준 라이브러리 우선(외부 패키지는 `pytest`, 필요 시 `ruff` 정도만 허용).
- Windows(Git Bash) 환경이므로 콘솔 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8`로 재확인한다
  (코드 문제가 아니라 콘솔 코드페이지 문제일 수 있음).
