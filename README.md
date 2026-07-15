# SampleOrderSystem

반도체 시료 생산주문관리 시스템 — 콘솔 기반 MVC 애플리케이션.

시료(Sample) 등록, 고객 주문 접수, 주문 승인/거절, 생산 라인 운영, 출고 처리, 모니터링을
하나의 콘솔 앱에서 처리한다. Human-in-the-loop Agentic TDD(`SKILL.md`, `SKILL_tdd.md`)
방식으로 개발되었으며, 전체 개발 과정과 근거는 `docs/PLAN.md`에 Cycle 단위로 기록되어 있다.

## 실행 방법

```bash
python main.py
```

실행하면 `data/sample_management.json`에 상태가 저장되며, 앱을 다시 실행해도 데이터가
유지된다(데이터 영속성).

## 주요 기능 (메인 메뉴)

| 메뉴 | 기능 |
|---|---|
| [1] 시료 관리 | 시료 등록, 목록 조회(재고 포함), 이름 검색 |
| [2] 시료 주문 | 시료 ID / 고객명 / 수량으로 주문 접수 (`RESERVED`) |
| [3] 주문 승인/거절 | 재고 충분 시 즉시 `CONFIRMED`, 부족 시 생산 라인 등록 후 `PRODUCING`, 거절 시 `REJECTED` |
| [4] 생산 라인 | 현재 생산 작업 및 FIFO 대기열 조회, 생산 완료 처리(`PRODUCING` → `CONFIRMED`) |
| [5] 출고 처리 | `CONFIRMED` 상태 주문 출고(`RELEASE`), 이 시점에만 재고 차감 |
| [6] 모니터링 | 상태별 주문 건수(`REJECTED` 제외), 시료별 재고 여유/부족/고갈 현황 |

메인 메뉴 진입 시마다 등록 시료 수 / 총 재고 / 전체 주문 수 / 생산라인 대기 건수 요약이
표시된다.

## 주문 상태 흐름

`RESERVED` → (승인) → 재고 충분: `CONFIRMED` / 재고 부족: `PRODUCING` → `CONFIRMED` → `RELEASE`
`RESERVED` → (거절) → `REJECTED`

## 프로젝트 구조

```
main.py                      진입점
src/sample_order_system/
  model/                     Sample, Order, ProductionQueueItem (frozen dataclass)
  repository/                JSON 파일 기반 영속성 (atomic write)
  service/                   유스케이스별 얇은 서비스 계층
  monitor/                   모니터링 순수 로직
  controller/                메뉴별 컨트롤러
  view/                      콘솔 입출력
tests/                       pytest 테스트 (81개)
scripts/verify.py            Harness (문법 검사 + pytest + 선택적 ruff)
docs/PLAN.md                 Living Plan — Cycle별 RED/GREEN 기록
PRD.md / CLAUDE.md           요구사항 정의서 / 개발 규칙
SKILL.md / SKILL_tdd.md       Agentic TDD 절차 정의
```

## 개발/검증

```bash
python scripts/verify.py   # 문법 검사 + 전체 테스트 + (설치 시) ruff
```

이 프로젝트는 Vertical Slice 단위의 Cycle(0~11)로 개발되었으며, 각 Cycle은 RED(실패하는
테스트 작성) → GREEN(최소 구현) 커밋 쌍으로 기록된다. 자세한 설계 근거와 각 Cycle의 계획·결과는
`docs/PLAN.md`를 참고한다.
