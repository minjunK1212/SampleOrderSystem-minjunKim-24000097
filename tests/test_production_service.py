from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import order_service, production_service


def test_get_current_job_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=10))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=50)
    order_service.approve_order(repo, order.order_id)

    current = production_service.get_current_job(repo)

    assert current.order_id == order.order_id


def test_list_production_queue_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=10))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=50)
    order_service.approve_order(repo, order.order_id)

    queue = production_service.list_production_queue(repo)

    assert len(queue) == 1


def test_complete_current_production_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=10))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=50)
    order_service.approve_order(repo, order.order_id)

    completed = production_service.complete_current_production(repo)

    assert completed.status == OrderStatus.CONFIRMED
