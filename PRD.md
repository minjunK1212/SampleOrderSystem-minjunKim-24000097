# PRD — 반도체 시료 생산주문관리 시스템 (SampleOrderSystem)

## 1. 배경

가상의 반도체 회사 "S-Semi"는 다양한 시료(Sample)를 생산해 연구소·팹리스·대학 연구실에 납품한다.
주문이 들어오면 웨이퍼 공정 설비로 제작 후 검수를 거쳐 출고된다. 최근 주문량 급증으로 처리
현황 추적이 어려워져, 엑셀·메모장 대신 체계적인 콘솔 기반 관리 시스템을 개발한다.

## 2. 역할

- **고객**: 필요한 시료를 이메일 등으로 요청(시스템 외부 행위, 구현 대상 아님).
- **주문 담당자**: 요청에 맞게 주문서를 작성(시료 등록, 주문 접수).
- **생산 담당자**: 개발 시료를 등록하고, 주문 수신 후 승인 또는 거절, 생산·출고를 처리.

이 시스템은 단일 콘솔 애플리케이션으로 위 역할들의 작업을 모두 수행할 수 있게 한다(역할별
로그인/권한 분리는 기능 범위에 없음).

## 3. 시스템 개요

- **생산 라인**: 공장에서 시료 하나를 생산하는 설비 흐름. 하나의 생산 라인은 시료를 하나씩
  생산하며, 주문이 들어온 시료에 대해서만 생산한다(단일 라인, FIFO 스케줄링).
- **실행 방식**: 콘솔 기반. 담당자가 메뉴 번호를 입력해 명령을 실행한다.

## 4. 도메인 모델 (단일 스키마)

`docs/PLAN.md`의 통일 결정에 따라 아래 하나의 스키마만 사용한다. DataPersistence/DataMonitor/
DummyDataGenerator PoC에서 검증된 필드 구성과 100% 동일하되, 주문 상태의 완료값은 `RELEASE`로
통일한다(ConsoleMVC PoC의 `RELEASED`는 폐기).

### Sample (시료)

| 필드 | 타입 | 규칙 |
|---|---|---|
| `sample_id` | str | 고유값, 빈 문자열 불가 |
| `name` | str | 고유값, 빈 문자열 불가 |
| `average_production_time` | float | 0보다 큼 |
| `yield_rate` | float | 0 초과 1 이하. `수율 = 정상 시료 수 / 총 생산 시료 수` |
| `inventory` | int | 0 이상. **현재 창고에 실제로 보유 중인, 즉시 출고 가능한 정상품 수량**을 의미한다. 승인 시점에는 차감되지 않으며, 정확히 출고(RELEASE) 시점 한 곳에서만 차감된다(6.7 참고) |

### Order (주문)

| 필드 | 타입 | 규칙 |
|---|---|---|
| `order_id` | str | 고유값 |
| `sample_id` | str | 등록된 Sample을 참조해야 함 |
| `customer_name` | str | 빈 문자열 불가 |
| `quantity` | int | 1 이상 |
| `status` | str(Enum) | `RESERVED` / `PRODUCING` / `CONFIRMED` / `RELEASE` / `REJECTED` 중 하나 |

### ProductionQueueItem (생산 큐 항목)

| 필드 | 타입 | 규칙 |
|---|---|---|
| `order_id` | str | PRODUCING 상태 Order를 참조해야 함 |
| `sample_id` | str | 참조 Order의 sample_id와 동일 |
| `required_quantity` | int | `max(order.quantity - sample.inventory, 1)` |
| `production_quantity` | int | `ceil(required_quantity / sample.yield_rate)` |
| `queue_position` | int | 1부터 시작하는 FIFO 순번, 중복 불가 |

### 통합 JSON 스키마

```json
{
  "samples": [ { "sample_id": "S-001", "name": "...", "average_production_time": 0.5, "yield_rate": 0.9, "inventory": 100 } ],
  "orders": [ { "order_id": "ORD-0001", "sample_id": "S-001", "customer_name": "...", "quantity": 50, "status": "RESERVED" } ],
  "production_queue": [ { "order_id": "ORD-0001", "sample_id": "S-001", "required_quantity": 10, "production_quantity": 12, "queue_position": 1 } ]
}
```

## 5. 주문 상태 흐름

| 상태 | 의미 |
|---|---|
| `RESERVED` | 주문 접수 |
| `REJECTED` | 주문 거절 (정상 흐름 밖, 모니터링 집계에서 제외) |
| `PRODUCING` | 승인 완료 + 재고 부족으로 생산 중 |
| `CONFIRMED` | 승인 완료 + 출고 대기 중 |
| `RELEASE` | 출고 완료 |

```
RESERVED --승인(재고 충분)--> CONFIRMED --출고--> RELEASE
RESERVED --승인(재고 부족)--> PRODUCING --생산 완료--> CONFIRMED --출고--> RELEASE
RESERVED --거절--> REJECTED
```

## 6. 기능 명세

### 6.1 메인 메뉴

기능별 선택 화면과 전체 시료 요약(등록 시료 수, 총 재고, 전체 주문 수, 생산라인 대기 건수)을
표시한다.

| 메뉴 | 설명 |
|---|---|
| 시료 관리 | 신규 시료 등록, 목록 조회, 이름 검색 |
| 시료 주문 | 고객 주문 접수 |
| 주문 승인/거절 | 접수된 주문 승인 또는 거절 |
| 모니터링 | 상태별 주문 수 및 시료별 재고 현황 |
| 생산 라인 | 현재 생산 중 시료 및 대기 큐 확인 |
| 출고 처리 | CONFIRMED 주문 출고 실행 |

### 6.2 시료 관리

- **시료 등록**: `sample_id`, `name`, `average_production_time`, `yield_rate` 입력(초기 `inventory`는
  0). `sample_id`/`name` 중복 시 등록 거부.
- **시료 조회**: 등록된 모든 시료를 현재 재고와 함께 목록으로 표시.
- **시료 검색**: 이름 등 속성으로 특정 시료 검색.

### 6.3 시료 주문

- 고객이 시료를 요청하면 주문 담당자가 주문을 생성한다.
- 입력값: `sample_id`(등록된 시료여야 함), `customer_name`, `quantity`(1 이상).
- 생성 직후 상태는 `RESERVED`.

### 6.4 주문 승인/거절

- **접수된 주문 목록**: `RESERVED` 상태 주문만 표시.
- **승인**: 재고 상황에 따라 자동 분기. **승인 시점에는 `inventory`를 차감하지 않는다** — 재고
  충분 여부를 확인하는 조회일 뿐이며, 실제 차감은 6.7 출고 시점에 단 한 번만 일어난다.
  - 재고 충분(`inventory >= quantity`) → 즉시 `CONFIRMED`. (생산 큐 미등록)
  - 재고 부족(`inventory < quantity`) → 생산 라인 큐에 등록하고 `PRODUCING`으로 전환.
    이때 부족분 `required_quantity = max(quantity - inventory, 1)`(주문 수량에서 현재 재고를
    뺀 값. 재고가 0이어도 최소 1개는 생산),
    `production_quantity = ceil(required_quantity / yield_rate)`(수율 손실을 감안해 실제로
    생산해야 할 수량, 올림 처리)를 계산해 큐 항목을 만든다.
- **거절**: 즉시 `REJECTED`로 전환. 재고에는 어떤 영향도 주지 않는다.

### 6.5 모니터링

- **주문량 확인**: `RESERVED`/`PRODUCING`/`CONFIRMED`/`RELEASE` 상태별 건수 표시. `REJECTED`는
  유효한 주문이 아니므로 집계에서 제외(별도로 표시하는 것은 무방하나 정상 집계에는 포함하지 않음).
- **재고량 확인**: 시료별 현재 재고와 상태(여유/부족/고갈) 표시.
  - **유효 주문 수량**: 해당 시료를 참조하는 주문 중 `REJECTED`, `RELEASE`를 제외한(`RESERVED`
    + `PRODUCING` + `CONFIRMED`) 주문의 `quantity` 합. `CONFIRMED`/`PRODUCING`도 아직 출고
    전이라 재고에서 실제로 차감되지 않은 상태이므로(6.4/6.7 참고) 계속 "재고를 필요로 하는
    수요"로 집계한다.
  - `고갈`: 재고 0
  - `부족`: 재고 < 유효 주문 수량 합
  - `여유`: 재고 >= 유효 주문 수량 합

### 6.6 생산 라인

- **현재 생산 작업 해석 규칙**: `production_queue`는 `queue_position` 오름차순으로 정렬된
  FIFO 대기열이다. **이 중 `queue_position`이 가장 작은(첫 번째) 항목이 "현재 생산 중인
  작업"**이며, 나머지는 대기 중인 작업이다. 별도의 "진행 중" 플래그나 자료구조를 두지 않고,
  큐의 첫 항목이라는 사실 자체로 현재 작업을 판별한다.
- **총 생산 시간(표시용)**: `total_production_time = sample.average_production_time *
  production_quantity`. 실시간 진행률 계산에 쓰이지 않는 참고용 값이다(8장 범위 제외 참고 —
  실시간 시뮬레이션 없음).
- **생산 완료 처리**(메뉴 조작으로 명시적으로 트리거): 큐의 첫 항목(현재 작업)에 대해서만
  실행할 수 있다.
  1. 해당 시료의 `inventory`에 `production_quantity`를 더한다(생산된 전량이 창고 재고로 들어옴).
  2. 대응 주문을 `PRODUCING → CONFIRMED`로 전환한다. **이 시점에 `inventory`를 다시 차감하지
     않는다** — 차감은 오직 6.7 출고 시점에만 일어난다(재고 중복 차감 방지).
  3. 완료된 항목을 큐에서 제거한다. 다음으로 `queue_position`이 작은 항목이 새로운 "현재
     생산 작업"이 된다(큐 앞으로 당길 뿐, `queue_position` 값 자체를 재부여하지는 않는다).
- 표시 정보 수준은 자유(주문 정보, 진행률 등)이나 최소한 대기 순서·주문ID·시료ID·부족수량·
  실생산량은 포함한다.

### 6.7 출고 처리

- `CONFIRMED` 상태 주문 목록을 표시하고, 선택한 주문을 출고 처리한다.
- **이 시점에만 `inventory -= order.quantity`를 수행한다.** 승인(6.4)과 생산 완료(6.6)는
  재고를 차감하지 않으므로, 동일 주문에 대해 재고가 두 번 차감되는 일은 구조적으로 발생하지
  않는다. 차감 후 주문 상태를 `RELEASE`로 전환한다.

## 7. 비기능 요구사항

- **데이터 영속성**: 통합 JSON 파일(`data/sample_management.json` 등)에 저장하며, 재시작해도
  데이터가 유지되어야 한다. 저장은 임시 파일 → 원자적 교체(atomic replace) 방식으로 손상을 방지한다.
- **검증**: 모든 쓰기 작업 전에 참조 무결성(Order의 sample_id 존재 여부, Queue의 order_id/상태
  일치 등)과 값 검증을 통과해야 한다. 검증 실패 시 기존 파일을 변경하지 않는다.
- **테스트**: 도메인 규칙(재고 분기, 생산 계산식, 상태 전이)과 리포지토리(영속성, 무결성)는
  pytest로 자동 검증한다.
- **아키텍처**: Model / Repository / Service / Controller / View로 책임을 분리한다(자세한 계층
  구조는 `docs/PLAN.md` 참고).

## 8. 범위 제외

- 다중 사용자 인증/권한 분리
- 실시간(멀티스레드) 생산 시뮬레이션 — 생산 완료는 메뉴 조작을 통한 명시적 트리거로 처리
- 다중 생산 라인 병렬 처리(PDF 기준 단일 라인)
- 외부 DB/ORM 연동
- **동시 승인으로 인한 재고 초과 예약(오버셀) 방지** — 승인 시점에는 재고를 차감(예약)하지
  않으므로(6.4 참고), 여러 주문을 연달아 승인한 뒤 그 합이 실제 재고보다 많은 상태에서 각각
  출고를 시도하면 이론상 재고가 음수가 될 수 있다. 이 시스템은 단일 담당자가 콘솔에서 순차적으로
  조작하는 것을 전제로 하므로 이 경쟁 상태(race condition)에 대한 잠금(lock)이나 예약 처리는
  구현하지 않는다.
