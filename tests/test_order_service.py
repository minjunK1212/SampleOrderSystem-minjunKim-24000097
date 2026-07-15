from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import order_service


def test_reserve_order_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))

    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=5)

    assert order.status == OrderStatus.RESERVED
    assert repo.get_order(order.order_id) is not None


def test_list_reserved_orders_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=5)

    reserved_orders = order_service.list_reserved_orders(repo)

    assert [o.order_id for o in reserved_orders] == [order.order_id]


def test_reject_order_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=5)

    rejected = order_service.reject_order(repo, order.order_id)

    assert rejected.status == OrderStatus.REJECTED
