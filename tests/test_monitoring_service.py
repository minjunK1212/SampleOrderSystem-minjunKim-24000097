from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import monitoring_service, order_service


def test_get_order_status_counts_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=10)

    counts = monitoring_service.get_order_status_counts(repo)

    assert counts[OrderStatus.RESERVED] == 1


def test_get_sample_inventory_report_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=30)

    report = monitoring_service.get_sample_inventory_report(repo)

    assert len(report) == 1
    row = report[0]
    assert row.sample_id == "S-001"
    assert row.inventory == 100
    assert row.valid_quantity == 30
    assert row.status == "여유"
