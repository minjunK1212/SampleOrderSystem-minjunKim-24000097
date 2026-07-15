from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import main_menu_summary_service, order_service


def test_get_main_menu_summary_computes_totals(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=10))
    repo.register_sample(Sample("S-002", "GaN Epitaxial Wafer", 0.3, 0.9, inventory=20))

    order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=5)
    order_service.reserve_order(repo, sample_id="S-001", customer_name="B", quantity=5)
    insufficient_order = order_service.reserve_order(repo, sample_id="S-002", customer_name="C", quantity=100)
    order_service.approve_order(repo, insufficient_order.order_id)  # 재고 부족 -> 생산큐 등록

    summary = main_menu_summary_service.get_main_menu_summary(repo)

    assert summary.sample_count == 2
    assert summary.total_inventory == 30
    assert summary.order_count == 3
    assert summary.production_queue_count == 1


def test_get_main_menu_summary_when_empty(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")

    summary = main_menu_summary_service.get_main_menu_summary(repo)

    assert summary.sample_count == 0
    assert summary.total_inventory == 0
    assert summary.order_count == 0
    assert summary.production_queue_count == 0
