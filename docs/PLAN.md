# SampleOrderSystem 구현 계획 — PoC 자산 분석

이 문서는 코드를 옮기기 전에, 앞서 완성한 4개 PoC(ConsoleMVC, DataPersistence, DataMonitor,
DummyDataGenerator)에서 무엇을 재사용/재작성/폐기할지, 그리고 최종 구현 순서를 정리한다.
**PoC 리포지토리를 그대로 import하거나 상대경로로 의존하지 않는다.** 이 문서에서 "재사용"은
검증된 로직·규칙·인터페이스 설계를 참고해 SampleOrderSystem 안에 새로 작성한다는 뜻이며,
파일을 복사해 오는 것을 의미하지 않는다.

## 0. 가장 먼저 해결해야 할 불일치: 도메인 모델 통일

4개 PoC를 독립적으로 만들다 보니 같은 개념에 대해 서로 다른 필드명을 썼다. SampleOrderSystem은
**하나의 Domain Model, 하나의 통합 JSON 스키마**만 가지므로 아래 불일치를 먼저 확정해야 한다.

| 개념 | ConsoleMVC | DataPersistence | DataMonitor / DummyDataGenerator | 최종 채택 |
|---|---|---|---|---|
| 시료 필드 | `Sample(sample_id, name, average_production_time, yield_rate, inventory)` | 동일 | 동일 | **변경 없음** — 3개 PoC가 이미 일치 |
| 주문 완료 상태명 | `RELEASED` (OrderStatus Enum) | (해당 없음) | `RELEASE` (문자열) | **`RELEASE`** — PDF 8p 표와 DataMonitor/DummyDataGenerator 표기를 따름 |
| 주문 상태 표현 | `Enum` (OrderStatus) | (해당 없음) | 허용값 목록을 가진 `str` | **`Enum`으로 재도입하되 값은 문자열과 동일하게 유지**(`Enum(str)` 형태) — 타입 안정성 + JSON 직렬화 호환 둘 다 확보 |
| 생산 큐 항목 필드 | `ProductionJob(order_id, sample_id, shortage_quantity, actual_quantity, total_process_time)` — 값 계산은 전부 TODO | (해당 없음) | `ProductionQueueItem(order_id, sample_id, required_quantity, production_quantity, queue_position)` — 계산식 확정, 실제 사용 중 | **DataMonitor/DummyDataGenerator 필드명 채택**, ConsoleMVC 필드명은 폐기 |
| 생산 큐 자료구조 | `deque` + `current_job`(진행 중 1건) | (해당 없음) | 단순 리스트(대기열 전체를 한 번에 나열, "진행 중" 개념 없음) | **`deque` 기반 유지** — PDF의 "현재 처리 중 1건 + 대기 목록" UI(21p 예시)를 충족하려면 진행 중 개념이 필요 |

## 1. PoC별 재사용 / 재작성 / 폐기

### ConsoleMVC (`model/`, `view/`, `controller/`)

- **재사용(설계 그대로 따름)**
  - Model / View / Controller 3계층 분리 구조 자체. PDF 미션1이 요구한 구조이자, SampleOrderSystem도
    콘솔 기반 대화형 시스템이므로 그대로 이어간다.
  - `MainController`가 메뉴별 서브컨트롤러+뷰를 조립하고 라우팅하는 패턴(`controller/main_controller.py`).
  - 각 `*_view.py`의 메뉴 문구·입력 프롬프트 구조(예: `[1] 시료 등록  [2] 시료 목록 ...`) — PDF의
    예시 UI 화면과 맞닿아 있어 그대로 이어받는다.
- **재작성(뼈대만 있고 실제 로직이 없어 새로 채워야 함)**
  - `OrderController.approve_order`: 현재 `shortage_quantity=0`, `actual_quantity=0`,
    `total_process_time=0`으로 TODO 처리되어 있음 → `required_quantity = max(quantity - inventory, 1)`,
    `production_quantity = ceil(required_quantity / yield_rate)`, `total_process_time =
    average_production_time * production_quantity` 실제 계산으로 교체.
  - `ProductionController.complete_current_job`: 현재 큐를 그냥 다음 항목으로 넘기기만 하고 재고
    반영·주문 상태 전환이 없음 → 생산 완료 시 `sample.inventory`에 `production_quantity`를 더하고
    해당 주문을 `PRODUCING → CONFIRMED`로 전환하는 로직 추가.
  - `OrderStatus`: `RELEASED` → `RELEASE`로 값 변경.
  - `ProductionJob` → `ProductionQueueItem`으로 필드명 교체(위 표 참고).
- **폐기**
  - 없음 — 구조 자체는 전부 유효하고, 값 계산 로직만 채우면 되는 수준.

### DataPersistence (`model/sample.py`, `repository/sample_repository.py`)

- **재사용**
  - `Sample` dataclass 필드 정의(변경 없이 그대로).
  - `validate_sample_fields` 검증 규칙(빈 문자열 금지, `average_production_time > 0`,
    `0 < yield_rate <= 1`, `inventory >= 0`).
  - `SampleRepository`의 원자적 저장 방식(임시 파일 → `os.replace`)과 sample_id/name 중복 검증 로직 —
    다만 대상 범위를 Sample 전용에서 Sample+Order+ProductionQueue 통합 리포지토리로 확장 재작성.
- **재작성**
  - 리포지토리 범위: `SampleRepository` 하나만 있던 것을, `samples`/`orders`/`production_queue`를
    함께 다루는 단일 `OrderSystemRepository`(가칭)로 확장.
- **폐기**
  - 없음 — `samples`만 다루던 스코프가 좁을 뿐, 로직 자체는 전부 재사용 가치가 있음.

### DataMonitor (`src/data_monitor/*.py`)

- **재사용**
  - `monitor_service.py`의 집계 함수들(`count_orders_by_status`, `valid_order_quantity_by_sample`,
    `inventory_status`의 여유/부족/고갈 기준, `sorted_production_queue`) — PDF의 "모니터링" 메뉴
    요구사항(18~19p)과 정확히 일치. 필드명만 통일된 도메인 모델에 맞게 조정해 그대로 가져온다.
  - `json_loader.py`의 구조적 오류 처리 방식(파일 없음/빈 파일/JSON 문법 오류/최상위 타입 오류를
    구분해 명확한 한국어 메시지로 예외 발생) — 통합 리포지토리의 로딩 계층에 반영.
- **재작성**
  - 이 PoC는 "읽기 전용"이 전제였으므로, 최종 시스템에서는 동일한 집계 로직을 CRUD 가능한
    리포지토리 위에서 다시 호출하도록 감싸야 한다(집계 함수 자체는 순수 함수라 그대로 재사용 가능,
    감싸는 방식만 재작성).
- **폐기**
  - `--watch` 반복 조회, OS 비종속 화면 갱신 등 "모니터링 전용 콘솔 앱"으로서의 실행 진입점
    설계는 폐기 — 최종 시스템은 메인 메뉴의 `[4] 모니터링` 안에서 1회성으로 같은 정보를 보여주면
    충분하다(PDF 예시 UI 기준).

### DummyDataGenerator (`src/dummy_data_generator/*.py`)

- **재사용**
  - `validator.py`의 참조 무결성 검증 로직(Sample/Order 중복 검사, Order의 sample_id 참조 검사,
    ProductionQueue의 `required_quantity`/`production_quantity` 계산식 일치 검사, PRODUCING 주문과
    큐 항목의 1:1 매칭 검사) — 통합 리포지토리가 저장 전에 수행할 검증 로직의 기반으로 그대로 채택.
  - `json_storage.py`의 `tempfile.mkstemp` 기반 원자적 저장 + 로딩 시 항목 단위 타입 검증 패턴 —
    통합 리포지토리의 저장/로딩 계층 설계 기준으로 채택.
  - 생성 규칙(시료 재고 4구간 분포, 주문 5개 상태 커버리지, PRODUCING 주문만 큐에 매핑) — 이번
    프로젝트에서도 "Dummy 데이터 시딩" 스크립트로 그대로 필요하다.
- **재작성**
  - CLI(`cli.py`)는 SampleOrderSystem의 대화형 메인 메뉴와는 별개로, "초기 데이터 시딩용
    독립 스크립트"로 유지하되 통합 리포지토리의 스키마/검증 함수를 그대로 호출하도록 재작성
    (로직 중복 제거).
- **폐기**
  - `--mode append`처럼 생성 도구 자체의 CLI 옵션 체계는 시딩 스크립트에만 남기고, 대화형
    메인 메뉴에는 노출하지 않는다(PDF 기능 명세에 없는 메뉴이므로).

## 2. 최종 아키텍처 (재사용 요소를 반영한 결론)

```
SampleOrderSystem/
├── CLAUDE.md
├── PRD.md
├── docs/
│   └── PLAN.md              (이 문서)
├── main.py                   # 대화형 콘솔 진입점 (ConsoleMVC 패턴 계승)
├── scripts/
│   └── seed_dummy_data.py    # DummyDataGenerator 로직을 재작성한 시딩 스크립트
├── src/sample_order_system/
│   ├── model/                 # 통일된 Sample/Order/ProductionQueueItem/OrderStatus
│   ├── repository/            # DataPersistence+DummyDataGenerator 저장 로직을 확장 재작성
│   ├── service/               # 주문 승인/생산 완료/출고 등 실제 비즈니스 규칙 (ConsoleMVC의 TODO를 채움)
│   ├── monitor/                # DataMonitor 집계 로직 재사용
│   ├── controller/             # ConsoleMVC 패턴 계승, service/repository 호출
│   └── view/                   # ConsoleMVC 패턴 계승
└── tests/
```

## 3. 구현 순서 — Vertical Slice Cycle (Living Plan)

이 프로젝트는 계층 전체(Model 전체 → Repository 전체 → Service 전체 → ...)를 한 번에 구현하지
않는다. 대신 **하나의 기능을 처음부터 끝까지(Model~View, 필요한 만큼) 관통하는 얇은 조각(Vertical
Slice) 단위**로 나눠, `SKILL.md`(agentic-tdd)의 RED(Plan 승인 → Test 승인) → GREEN → REVIEW
사이클을 각 Cycle마다 반복한다.

이 섹션은 **최초에 한 번 쓰고 끝나는 문서가 아니라, 프로젝트 전체 기간 동안 계속 갱신되는 Living
Plan**이다. 각 Cycle을 시작하기 전 "Plan" 항목을 채워 RED Commit을 만들고, 완료 후 "Result"
항목을 채워 GREEN Commit에 포함시킨다. 규칙과 문서 형식은 `CLAUDE.md`를 따른다.

### 예상 Cycle 목록

| Cycle | 기능 | 상태 |
|---|---|---|
| 0 | 프로젝트 구조와 Harness | 완료 |
| 1 | 시료 등록, 조회, 검색 | 완료 |
| 2 | 주문 접수와 RESERVED 상태 생성 | 완료 |
| 3 | RESERVED 주문 거절 | 완료 |
| 4 | 재고가 충분한 주문 승인 | 대기 |
| 5 | 재고가 부족한 주문 승인과 생산 큐 등록 | 대기 |
| 6 | FIFO 생산라인 조회와 생산 완료 | 대기 |
| 7 | CONFIRMED 주문 출고 | 대기 |
| 8 | 주문 및 재고 모니터링 | 대기 |
| 9 | JSON 영속성과 재실행 복구 | 대기 |
| 10 | 전체 Acceptance Scenario | 대기 |

이 순서는 확정이 아니라 초안이다. Cycle을 진행하다 필요성이 확인되면 이 표와 아래 Cycle
Log를 갱신하고 재승인을 받는다(예: Cycle 분할/병합, 순서 변경).

각 Cycle에서 필요한 만큼의 Model, Repository, Service, Controller, View, Test를 함께
조금씩 구현한다(계층 전체를 미리 만들어두지 않는다). PoC 재사용/재작성/폐기 방침(1장)은 각
Cycle에서 해당 계층을 처음 건드릴 때 적용한다 — 예: Cycle 1에서 Model의 Sample과 Repository의
저장 로직 일부, Cycle 4~5에서 Service의 승인 로직과 그때 필요한 Repository 확장이 이뤄진다.

### Cycle Log

각 Cycle의 상세 Plan과 실제 구현 결과는 아래에 Cycle별로 추가한다. Plan 승인 시 RED Commit,
구현 완료 승인 시 GREEN Commit에 포함된다(형식은 `CLAUDE.md`의 "Agentic TDD Cycle" 절 참고).

<!--
Cycle N: <기능명> 를 시작할 때 아래 형식으로 이 아래에 추가한다.

#### Cycle N: <기능명> — Plan (RED)

- 현재 상태 / 목표 / 관련 요구사항(PRD.md 절 번호) / 포함 범위 / 제외 범위
- Acceptance Criteria
- 예정 테스트 목록
- 구현 접근 방식
- 변경 예정 파일
- Harness 명령
- RED/GREEN Commit 계획
- 완료 조건

#### Cycle N: <기능명> — Result (GREEN)

- 상태: Completed
- 실제 변경 파일
- 실제 테스트 수와 결과
- Harness 결과
- 계획 대비 변경 사항
- 범위 이탈 여부
- 남은 위험 또는 후속 작업
-->

#### Cycle 0: 프로젝트 구조와 Harness — Plan (RED)

- **현재 상태**: 문서(PRD.md/CLAUDE.md/docs/PLAN.md)만 존재. `src/`, `tests/`, 실행 가능한
  코드, 자동 검증 수단이 전혀 없다.
- **목표**: 이후 모든 Cycle이 TDD로 진행될 수 있도록 최소 프로젝트 골격과 단일 Harness 명령
  (`python scripts/verify.py`)을 갖춘다. 이 Cycle은 도메인 로직을 전혀 포함하지 않는다.
- **관련 요구사항**: PRD.md 7장(테스트·아키텍처), CLAUDE.md 8장(Harness)
- **포함 범위**
  - `pyproject.toml` (pytest 설정, `testpaths = ["tests"]`)
  - `conftest.py` (`src/`를 `sys.path`에 추가 — DataMonitor/DummyDataGenerator PoC와 동일한 src-layout 패턴)
  - `src/sample_order_system/` 빈 패키지와 6개 하위 패키지(`model/repository/service/monitor/controller/view`)의 `__init__.py` (전부 비어 있음 — 로직 없음)
  - `scripts/verify.py`: (1) `py_compile`로 `src/`, `tests/` 전체 문법 검사, (2) `pytest -v`
    전체 실행, (3) 둘 중 하나라도 실패하면 0이 아닌 종료 코드 반환. `ruff`는 설치되어 있으면
    실행하고, 없으면 건너뛴다는 메시지만 남긴다(필수 의존성으로 강제하지 않음).
  - `tests/test_harness_smoke.py`: `sample_order_system` 패키지가 정상적으로 import되는지
    확인하는 스모크 테스트 1개. 이번 Cycle의 유일한 테스트이자, "Harness 자체가 작동하는가"를
    검증하는 용도.
- **제외 범위**: 실제 도메인 모델(Sample/Order 등), 비즈니스 로직, `main.py` 콘솔 메뉴 —
  전부 Cycle 1부터 시작.
- **Acceptance Criteria**
  1. `python scripts/verify.py`가 성공적으로 종료(exit code 0)한다.
  2. `pytest -v` 실행 시 `test_harness_smoke.py`의 테스트가 수집되고 통과한다.
  3. `import sample_order_system`이 `src/`를 `sys.path`에 추가한 상태에서 오류 없이 동작한다.
- **예정 테스트 목록**
  - `tests/test_harness_smoke.py::test_package_is_importable` — `sample_order_system` 패키지를
    import할 수 있는지 확인(패키지가 아직 없으므로 최초엔 `ModuleNotFoundError`로 실패해야 정상).
- **구현 접근 방식**: DataMonitor/DummyDataGenerator PoC에서 검증한 src-layout(+conftest.py로
  sys.path 등록) 패턴을 그대로 따른다. `scripts/verify.py`는 외부 의존성 없이 표준 라이브러리
  (`subprocess`, `py_compile`, `sys`)만 사용해 pytest를 하위 프로세스로 실행한다.
- **변경 예정 파일**: `pyproject.toml`, `conftest.py`, `scripts/verify.py`,
  `src/sample_order_system/__init__.py`(+ model/repository/service/monitor/controller/view
  6개 하위 `__init__.py`), `tests/test_harness_smoke.py`
- **Harness 명령**: `python scripts/verify.py`
- **RED/GREEN Commit 계획**: `RED 0: plan project structure and harness` (이 Plan, PLAN.md만) →
  승인 → `GREEN 0: implement project structure and harness` (골격 + harness + 스모크 테스트 +
  결과가 반영된 PLAN.md)
- **완료 조건**: 위 Acceptance Criteria 3개를 모두 만족하고, `python scripts/verify.py`가 로컬에서
  실제로 성공하는 것을 확인한 뒤 GREEN Commit.

#### Cycle 0: 프로젝트 구조와 Harness — Result (GREEN)

- **상태**: Completed
- **실제 변경 파일**: `conftest.py`, `pyproject.toml`, `tests/test_harness_smoke.py`,
  `scripts/verify.py`, `src/sample_order_system/__init__.py` +
  `model/repository/service/monitor/controller/view` 6개 하위 패키지의 빈 `__init__.py`
- **실제 테스트 수와 결과**: 1개(`test_package_is_importable`) — RED 단계에서
  `ModuleNotFoundError`로 예상대로 실패 확인 → GREEN 단계에서 PASSED
- **Harness 결과**: `python scripts/verify.py` → 문법 검사 OK, `pytest -v` 1 passed, `ruff`는
  미설치로 건너뜀(경고만, 실패 아님) → **Harness PASSED**
- **계획 대비 변경 사항**: 없음. Plan에 명시한 파일만 생성.
- **범위 이탈 여부**: 없음.
- **남은 위험/후속 작업**: 없음. `ruff` 설치 시 harness가 자동으로 포함해 실행한다.

#### Cycle 1: 시료 등록, 조회, 검색 — Plan (RED)

- **현재 상태**: Cycle 0에서 만든 빈 패키지 골격과 harness만 존재. 도메인 로직 없음, `main.py` 없음.
- **목표**: 시료(Sample) 등록/조회/이름 검색 기능을 Model~Repository~Service~Controller~View까지
  관통하는 첫 Vertical Slice로 구현하고, `python main.py`로 실제 콘솔 조작이 가능하게 한다.
- **관련 요구사항**: PRD.md 4장(Sample 도메인 모델), 6.1(메인 메뉴 최소 골격), 6.2(시료 관리),
  7장(영속성·검증)
- **포함 범위**
  - `model/sample.py`: `Sample` dataclass(`sample_id, name, average_production_time, yield_rate,
    inventory`) + 검증 함수(빈 문자열 금지, `average_production_time > 0`, `0 < yield_rate <= 1`,
    `inventory`는 0 이상 정수). DataPersistence PoC의 `Sample`/`validate_sample_fields`를 참고해
    새로 작성.
  - `repository/order_system_repository.py`: `OrderSystemRepository` — 통합 스키마
    `{"samples": [...], "orders": [...], "production_queue": [...]}` 전체를 읽고 쓰되, 이번
    Cycle에서는 `samples` 관련 메서드(`register_sample`, `list_samples`, `search_samples_by_name`,
    `get_sample`)만 구현한다. `orders`/`production_queue`는 로드 시 그대로 보존하고 빈 리스트로
    시작만 하며, 이번 Cycle에서 값을 채우거나 조작하지 않는다. 저장은 임시 파일 → `os.replace`
    원자적 교체(DataPersistence/DummyDataGenerator PoC 패턴).
  - `service/sample_service.py`: 등록/조회/검색을 위한 얇은 서비스 함수. Repository 호출과 최소
    조합만 하고 새로운 비즈니스 규칙을 추가하지 않는다.
  - `controller/main_controller.py`, `controller/sample_controller.py`,
    `view/main_menu_view.py`, `view/sample_view.py`: 메인 메뉴는 **이번 Cycle 범위인 "시료 관리"
    진입점과 종료만** 노출한다(주문/승인/모니터링/생산라인/출고 메뉴 항목은 아직 추가하지 않는다
    — Cycle 2부터 하나씩 추가).
  - `main.py`(프로젝트 루트): 콘솔 진입점. `MainController().run()` 호출.
- **제외 범위**: 주문 접수/승인/거절/생산/출고/모니터링 전부(Cycle 2 이후), 동시 승인 오버셀
  방지, 메인 메뉴의 시료 관리 이외 항목.
- **Acceptance Criteria**
  1. 시료 등록 시 `sample_id`/`name` 중복이면 거부하고, 유효성 위반(빈 문자열, 잘못된 범위 값)
     시 거부한다.
  2. 정상 등록된 시료는 JSON 파일에 저장되고, `OrderSystemRepository`를 새로 생성해도(재시작
     시뮬레이션) 그대로 조회된다.
  3. 시료 조회 시 등록된 모든 시료가 현재 재고와 함께 표시된다.
  4. 이름 검색 시 부분 일치하는 시료만 반환된다.
  5. 저장된 JSON은 `{"samples": [...], "orders": [], "production_queue": []}` 구조를 유지한다
     (아직 없는 orders/production_queue 키도 빈 리스트로 명시적으로 저장).
  6. `python main.py` 실행 시 시료 등록 → 조회 → 검색 메뉴 흐름이 에러 없이 동작한다(수동 확인).
- **예정 테스트 목록** (모두 `tmp_path` 사용, 실제 `data/` 파일 미수정)
  - `tests/test_model_sample.py`: 정상 생성, 빈 `sample_id`/`name` 거부, `average_production_time
    <= 0` 거부, `yield_rate` 범위 밖 거부, `inventory` 음수/비정수 거부
  - `tests/test_repository_sample.py`: 등록 후 JSON 저장 확인, 리포지토리 재생성 후 조회(영속성),
    `sample_id` 중복 거부, `name` 중복 거부, 이름 검색 부분 일치, 저장 구조에 `orders`/
    `production_queue` 빈 리스트 포함 확인
  - `tests/test_sample_service.py`: 서비스 함수가 Repository를 올바르게 호출/조합하는지
    (등록·조회·검색 각각)
- **구현 접근 방식**: DataPersistence PoC의 `Sample`/`validate_sample_fields`/원자적 저장 로직을
  참고해 새로 작성(코드 복사 없음). ConsoleMVC PoC의 `MainController` 라우팅 패턴을 참고해
  Controller/View를 얇게 구성.
- **변경 예정 파일**: `src/sample_order_system/model/sample.py`,
  `src/sample_order_system/repository/order_system_repository.py`,
  `src/sample_order_system/service/sample_service.py`,
  `src/sample_order_system/controller/main_controller.py`,
  `src/sample_order_system/controller/sample_controller.py`,
  `src/sample_order_system/view/main_menu_view.py`,
  `src/sample_order_system/view/sample_view.py`, `main.py`,
  `tests/test_model_sample.py`, `tests/test_repository_sample.py`, `tests/test_sample_service.py`
- **Harness 명령**: `python scripts/verify.py`
- **RED/GREEN Commit 계획**: `RED 1: plan sample management` (이 Plan, PLAN.md만) → 승인 →
  `GREEN 1: implement sample management` (구현 코드 + 테스트 + 결과가 반영된 PLAN.md)
- **완료 조건**: Acceptance Criteria 6개 모두 충족, `pytest` 전체 통과, `python scripts/verify.py`
  성공, `python main.py` 수동 실행으로 시료 등록/조회/검색 흐름 확인 후 GREEN Commit.

#### Cycle 1: 시료 등록, 조회, 검색 — Result (GREEN)

- **상태**: Completed
- **실제 변경 파일**: `src/sample_order_system/model/sample.py`,
  `src/sample_order_system/repository/order_system_repository.py`,
  `src/sample_order_system/service/sample_service.py`,
  `src/sample_order_system/controller/main_controller.py`,
  `src/sample_order_system/controller/sample_controller.py`,
  `src/sample_order_system/view/main_menu_view.py`,
  `src/sample_order_system/view/sample_view.py`, `main.py`,
  `tests/test_model_sample.py`, `tests/test_repository_sample.py`, `tests/test_sample_service.py`
- **실제 테스트 수와 결과**: 신규 16개(모델 7 + 리포지토리 6 + 서비스 3) — RED 단계에서 3개 파일
  모두 `ModuleNotFoundError`로 예상대로 실패 확인 → GREEN 단계에서 스모크 테스트 포함 17개 전부 PASSED
- **Harness 결과**: `python scripts/verify.py` → 문법 검사 OK, `pytest -v` 17 passed, `ruff`는
  미설치로 건너뜀 → **Harness PASSED**
- **계획 대비 변경 사항**: 없음. Plan에 명시한 파일만 생성.
- **범위 이탈 여부**: 없음. 주문/승인/생산/모니터링/출고는 손대지 않음.
- **수동 확인**: `python main.py`로 시료 등록 → 목록 조회 → 이름 검색(부분 일치 2건) → 재시작 후
  데이터 유지까지 실제 실행으로 확인. 저장된 JSON이
  `{"samples": [...], "orders": [], "production_queue": []}` 구조를 유지함을 확인.
- **남은 위험/후속 작업**: 없음. Cycle 2부터 `orders`에 실제 데이터가 채워지기 시작한다.

#### Cycle 2: 주문 접수와 RESERVED 상태 생성 — Plan (RED)

- **현재 상태**: 시료 관리(Cycle 1)만 존재. `Order`/`OrderStatus` 모델과 주문 관련 리포지토리
  메서드가 전혀 없음. `orders`는 항상 빈 리스트로만 저장되고 있음.
- **목표**: 고객 주문을 접수해 `RESERVED` 상태의 `Order`를 생성하고 통합 JSON의 `orders`에
  저장한다. 콘솔 메인 메뉴에 `[2] 시료 주문`이 추가되어 실제로 조작 가능해야 한다.
- **관련 요구사항**: PRD.md 4장(Order/OrderStatus 도메인 모델), 5장(RESERVED 상태), 6.3(시료 주문)
- **포함 범위**
  - `model/order.py`: `OrderStatus(str, Enum)`(`RESERVED/PRODUCING/CONFIRMED/RELEASE/REJECTED`)와
    `Order` dataclass(`order_id, sample_id, customer_name, quantity, status`) + 검증
    (`customer_name` 비어있지 않음, `quantity`는 1 이상 정수). 생성 시 `status` 기본값은
    `OrderStatus.RESERVED`.
  - `repository/order_system_repository.py` 확장: `orders`를 이제 원본 dict가 아니라 `Order`
    객체로 파싱해 관리한다(로드/저장 시 `Order.to_dict()`/`from_dict()` 사용). 추가 메서드:
    `reserve_order(sample_id, customer_name, quantity)` — 등록된 `sample_id`인지 확인(없으면
    거부), `order_id`를 `ORD-0001` 형식으로 기존 최대 번호+1로 자동 부여, `RESERVED` 상태로
    저장. `get_order(order_id)`, `list_orders()` 추가.
  - `service/order_service.py`: `reserve_order(repo, sample_id, customer_name, quantity)` —
    Repository에 위임만 한다.
  - `controller/order_controller.py`, `view/order_view.py` 신설: 시료 ID/고객명/수량 입력받아
    주문 접수, 결과(주문번호·상태)를 표시.
  - `controller/main_controller.py`: 메인 메뉴에 `[2] 시료 주문` 항목을 추가(PRD 6.1 메뉴 순서상
    두 번째). 주문 승인/거절·모니터링·생산라인·출고 메뉴는 아직 추가하지 않는다.
- **제외 범위**: 주문 승인/거절(Cycle 3~5), 생산/출고/모니터링, 재고 차감/분기 로직(아직 승인
  단계가 없으므로).
- **Acceptance Criteria**
  1. 등록된 `sample_id`로 주문을 접수하면 `ORD-0001` 형식의 `order_id`가 자동 부여되고 상태는
     `RESERVED`이다.
  2. 등록되지 않은 `sample_id`로 주문을 시도하면 거부된다.
  3. `quantity`가 1 미만이면 거부된다.
  4. `customer_name`이 빈 문자열이면 거부된다.
  5. 생성된 주문은 통합 JSON의 `orders`에 저장되고, 리포지토리를 재생성해도
     `get_order`/`list_orders`로 조회된다.
  6. `order_id`는 중복 없이 순차 부여되며, 재시작(리포지토리 재생성) 후에도 마지막 번호 다음부터
     이어진다.
  7. `python main.py` 실행 시 메인 메뉴에 `[2] 시료 주문`이 나타나고, 주문 접수 흐름이 에러 없이
     동작한다(수동 확인).
- **예정 테스트 목록** (모두 `tmp_path` 사용)
  - `tests/test_model_order.py`: 정상 생성(기본 상태 `RESERVED`), `quantity < 1` 거부,
    `customer_name` 빈 문자열 거부
  - `tests/test_repository_order.py`: `reserve_order` 저장 확인(JSON `orders`에 반영),
    존재하지 않는 `sample_id` 거부, `order_id` 자동 증가(`ORD-0001`, `ORD-0002`, ...), 재로드 후
    다음 번호부터 이어서 부여됨, `get_order`/`list_orders` 동작
  - `tests/test_order_service.py`: 서비스가 Repository에 올바르게 위임하는지
- **구현 접근 방식**: DummyDataGenerator PoC의 `order_id` 포맷팅/다음 번호 계산 로직과
  ConsoleMVC PoC의 `OrderStatus` Enum 설계를 참고해 새로 작성.
- **변경 예정 파일**: `src/sample_order_system/model/order.py`,
  `src/sample_order_system/repository/order_system_repository.py`(확장),
  `src/sample_order_system/service/order_service.py`,
  `src/sample_order_system/controller/order_controller.py`,
  `src/sample_order_system/view/order_view.py`,
  `src/sample_order_system/controller/main_controller.py`(메뉴 추가),
  `tests/test_model_order.py`, `tests/test_repository_order.py`, `tests/test_order_service.py`
- **Harness 명령**: `python scripts/verify.py`
- **RED/GREEN Commit 계획**: `RED 2: plan order reservation` (PLAN.md만) → 승인 →
  `GREEN 2: implement order reservation` (구현 + 테스트 + 결과 반영된 PLAN.md)
- **완료 조건**: Acceptance Criteria 7개 모두 충족, `pytest` 전체 통과, `python scripts/verify.py`
  성공, `python main.py` 수동 실행으로 주문 접수 흐름 확인 후 GREEN Commit.

#### Cycle 2: 주문 접수와 RESERVED 상태 생성 — Result (GREEN)

- **상태**: Completed
- **실제 변경 파일**: `src/sample_order_system/model/order.py`,
  `src/sample_order_system/repository/order_system_repository.py`(확장),
  `src/sample_order_system/service/order_service.py`,
  `src/sample_order_system/controller/order_controller.py`,
  `src/sample_order_system/view/order_view.py`,
  `src/sample_order_system/controller/main_controller.py`(메뉴 추가),
  `src/sample_order_system/view/main_menu_view.py`(메뉴 추가),
  `tests/test_model_order.py`, `tests/test_repository_order.py`, `tests/test_order_service.py`
- **실제 테스트 수와 결과**: 신규 9개(모델 3 + 리포지토리 5 + 서비스 1) — RED 단계에서 3개 파일
  모두 `ModuleNotFoundError`로 예상대로 실패 확인 → GREEN 단계에서 기존 17개 포함 26개 전부 PASSED
- **Harness 결과**: `python scripts/verify.py` → 문법 검사 OK, `pytest -v` 26 passed, `ruff`는
  미설치로 건너뜀 → **Harness PASSED**
- **계획 대비 변경 사항**: 없음. Plan에 명시한 파일만 생성.
- **범위 이탈 여부**: 없음. 승인/거절/생산/출고/모니터링은 손대지 않음.
- **수동 확인**: `python main.py`로 시료 등록 → 주문 접수(`ORD-0001`, `RESERVED` 확인) → 미등록
  `sample_id`로 주문 시 거부 메시지까지 실제 실행으로 확인. 저장된 JSON의 `orders`에 정확히
  반영되고 `production_queue`는 여전히 빈 리스트임을 확인.
- **남은 위험/후속 작업**: 없음. Cycle 3부터 이 주문들을 조회/거절하는 기능이 추가된다.

#### Cycle 3: RESERVED 주문 거절 — Plan (RED)

- **현재 상태**: 시료 관리(Cycle 1) + 주문 접수(Cycle 2)만 존재. 접수된 주문을 조회/거절하는
  기능이 없다. 메인 메뉴에 `[3] 주문 승인/거절`이 없다.
- **목표**: `RESERVED` 상태 주문 목록을 조회하고, 특정 주문을 거절해 즉시 `REJECTED`로 전환한다.
  승인(재고 분기)은 이번 Cycle 범위가 아니며 Cycle 4~5에서 같은 메뉴에 추가된다.
- **관련 요구사항**: PRD.md 5장(REJECTED 상태), 6.4(주문 승인/거절 — 접수된 주문 목록, 거절)
- **포함 범위**
  - `repository/order_system_repository.py` 확장: `list_orders_by_status(status)` — 주어진
    `OrderStatus`인 주문만 반환(우선 `RESERVED` 조회에 사용). `reject_order(order_id)` — 주문이
    존재하고 `RESERVED` 상태일 때만 `REJECTED`로 전환(불변 `Order`이므로
    `dataclasses.replace`로 새 객체를 만들어 교체) 후 저장. 존재하지 않거나 `RESERVED`가 아니면
    거부.
  - `service/order_service.py` 확장: `list_reserved_orders(repo)`, `reject_order(repo, order_id)`
    — Repository에 위임만 한다.
  - `controller/order_approval_controller.py`, `view/order_approval_view.py` 신설: `RESERVED`
    주문 목록을 보여주고, 거절할 주문번호를 입력받아 거절 처리 후 결과를 표시.
  - `controller/main_controller.py`, `view/main_menu_view.py`: 메인 메뉴에 `[3] 주문 승인/거절`
    추가.
- **제외 범위**: 주문 승인(재고 충분/부족 분기, 생산 큐 등록)은 다루지 않는다(Cycle 4~5). 이번
  Cycle의 승인/거절 메뉴는 거절만 지원한다. 생산/출고/모니터링도 범위 밖.
- **Acceptance Criteria**
  1. `RESERVED` 상태 주문만 목록에 표시된다.
  2. 유효한 `order_id`를 거절하면 해당 주문이 `REJECTED`로 전환되고 JSON에 저장된다.
  3. 존재하지 않는 `order_id`를 거절하려 하면 거부되고 오류 메시지가 표시된다.
  4. 이미 `RESERVED`가 아닌 주문(예: 이미 `REJECTED`)을 다시 거절하려 하면 거부된다.
  5. 거절해도 어떤 시료의 `inventory`도 변하지 않는다(PRD 6.4).
  6. `python main.py` 실행 시 메인 메뉴에 `[3] 주문 승인/거절`이 나타나고, `RESERVED` 목록 조회 →
     거절 흐름이 에러 없이 동작한다(수동 확인).
- **예정 테스트 목록** (모두 `tmp_path` 사용)
  - `tests/test_repository_order.py`에 추가: `list_orders_by_status`가 `RESERVED`만 필터링하는지,
    `reject_order` 성공 시 상태 전환·저장 확인, 존재하지 않는 `order_id` 거부, `RESERVED`가
    아닌 주문 재거절 거부, 거절 후 관련 시료의 `inventory`가 변하지 않는지
  - `tests/test_order_service.py`에 추가: `list_reserved_orders`/`reject_order`가 Repository에
    올바르게 위임되는지
- **구현 접근 방식**: `Order`가 불변(frozen dataclass)이므로 `dataclasses.replace`로 상태만
  바꾼 새 인스턴스를 만들어 교체한다(ConsoleMVC PoC의 `OrderController.reject_order`가 상태만
  바꾸던 방식과 동일한 결과, 새로 작성).
- **변경 예정 파일**: `src/sample_order_system/repository/order_system_repository.py`(확장),
  `src/sample_order_system/service/order_service.py`(확장),
  `src/sample_order_system/controller/order_approval_controller.py`,
  `src/sample_order_system/view/order_approval_view.py`,
  `src/sample_order_system/controller/main_controller.py`(메뉴 추가),
  `src/sample_order_system/view/main_menu_view.py`(메뉴 추가),
  `tests/test_repository_order.py`(추가), `tests/test_order_service.py`(추가)
- **Harness 명령**: `python scripts/verify.py`
- **RED/GREEN Commit 계획**: `RED 3: plan order rejection` (PLAN.md만) → 승인 →
  `GREEN 3: implement order rejection` (구현 + 테스트 + 결과 반영된 PLAN.md)
- **완료 조건**: Acceptance Criteria 6개 모두 충족, `pytest` 전체 통과, `python scripts/verify.py`
  성공, `python main.py` 수동 실행으로 거절 흐름 확인 후 GREEN Commit.

#### Cycle 3: RESERVED 주문 거절 — Result (GREEN)

- **상태**: Completed
- **실제 변경 파일**: `src/sample_order_system/repository/order_system_repository.py`(확장 —
  `list_orders_by_status`, `reject_order`),
  `src/sample_order_system/service/order_service.py`(확장 — `list_reserved_orders`,
  `reject_order`), `src/sample_order_system/controller/order_approval_controller.py`,
  `src/sample_order_system/view/order_approval_view.py`,
  `src/sample_order_system/controller/main_controller.py`(메뉴 추가),
  `src/sample_order_system/view/main_menu_view.py`(메뉴 추가),
  `tests/test_repository_order.py`(추가), `tests/test_order_service.py`(추가)
- **실제 테스트 수와 결과**: 신규 7개(리포지토리 5 + 서비스 2) — RED 단계에서 모두
  `AttributeError`로 예상대로 실패 확인 → GREEN 단계에서 기존 26개 포함 33개 전부 PASSED
- **Harness 결과**: `python scripts/verify.py` → 문법 검사 OK, `pytest -v` 33 passed, `ruff`는
  미설치로 건너뜀 → **Harness PASSED**
- **계획 대비 변경 사항**: 없음. Plan에 명시한 파일만 생성.
- **범위 이탈 여부**: 없음. 승인(재고 분기)/생산/출고/모니터링은 손대지 않음.
- **수동 확인**: `python main.py`로 시료 등록 → 주문 접수 → 주문 승인/거절 메뉴에서 RESERVED
  목록 확인 → 거절(`REJECTED` 전환, 목록에서 사라짐) → 존재하지 않는 주문번호 거절 시 오류
  메시지까지 실제 실행으로 확인. 거절 후에도 `inventory`가 변하지 않음을 JSON으로 확인.
- **남은 위험/후속 작업**: 없음. Cycle 4부터 같은 메뉴에 승인(재고 충분) 로직이 추가된다.

(Cycle 4 Plan은 다음 승인 요청 시 이 아래에 추가된다.)

각 Cycle의 RED/GREEN 커밋은 별도로 남기고, 원격 저장소에 즉시 push한다(`CLAUDE.md` 참고).
