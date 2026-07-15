from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import (
    monitoring_service,
    order_service,
    production_service,
    sample_service,
    shipment_service,
)


def test_full_acceptance_scenario_across_all_features(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    # 1. 시료 등록: S-001은 초기 재고 0(등록 규칙), S-002는 이미 재고를 보유한 상태로 준비.
    sample_service.register_sample(
        repo,
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.8,
    )
    repo.register_sample(Sample("S-002", "GaN Epitaxial Wafer", 0.3, 0.9, inventory=50))

    # 2. 주문 4건을 각각 다른 경로로 흘려보낸다.
    rejected = order_service.reserve_order(repo, sample_id="S-001", customer_name="RejectCo", quantity=10)
    order_service.reject_order(repo, rejected.order_id)

    confirmed_then_released = order_service.reserve_order(
        repo, sample_id="S-002", customer_name="QuickCo", quantity=20
    )
    order_service.approve_order(repo, confirmed_then_released.order_id)  # 재고 충분 -> CONFIRMED
    shipment_service.release_order(repo, confirmed_then_released.order_id)  # -> RELEASE

    produced_then_released = order_service.reserve_order(
        repo, sample_id="S-001", customer_name="ProduceCo", quantity=50
    )
    order_service.approve_order(repo, produced_then_released.order_id)  # 재고 부족 -> PRODUCING
    production_service.complete_current_production(repo)  # -> CONFIRMED, 재고 반영
    shipment_service.release_order(repo, produced_then_released.order_id)  # -> RELEASE

    still_reserved = order_service.reserve_order(repo, sample_id="S-002", customer_name="WaitCo", quantity=5)

    # 최종 주문 상태 검증
    assert repo.get_order(rejected.order_id).status == OrderStatus.REJECTED
    assert repo.get_order(confirmed_then_released.order_id).status == OrderStatus.RELEASE
    assert repo.get_order(produced_then_released.order_id).status == OrderStatus.RELEASE
    assert repo.get_order(still_reserved.order_id).status == OrderStatus.RESERVED

    # 최종 재고 검증: S-001 = 0 + 63(생산, ceil(50/0.8)) - 50(출고) = 13
    assert repo.get_sample("S-001").inventory == 13
    # S-002 = 50 - 20(출고) = 30
    assert repo.get_sample("S-002").inventory == 30

    # 3. 모니터링 집계가 최종 상태와 정확히 일치하는지 확인
    counts = monitoring_service.get_order_status_counts(repo)
    assert counts[OrderStatus.RESERVED] == 1
    assert counts[OrderStatus.PRODUCING] == 0
    assert counts[OrderStatus.CONFIRMED] == 0
    assert counts[OrderStatus.RELEASE] == 2

    report = {row.sample_id: row for row in monitoring_service.get_sample_inventory_report(repo)}
    # S-001: 유효 주문 없음(REJECTED/RELEASE만 참조) -> 여유
    assert report["S-001"].valid_quantity == 0
    assert report["S-001"].status == "여유"
    # S-002: RESERVED 5건만 유효 주문 -> 재고 30 >= 5 -> 여유
    assert report["S-002"].valid_quantity == 5
    assert report["S-002"].status == "여유"
