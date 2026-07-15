from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import order_service, shipment_service


def test_list_confirmed_orders_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=30)
    order_service.approve_order(repo, order.order_id)

    confirmed_orders = shipment_service.list_confirmed_orders(repo)

    assert [o.order_id for o in confirmed_orders] == [order.order_id]


def test_release_order_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.9, inventory=100))
    order = order_service.reserve_order(repo, sample_id="S-001", customer_name="A", quantity=30)
    order_service.approve_order(repo, order.order_id)

    released = shipment_service.release_order(repo, order.order_id)

    assert released.status == OrderStatus.RELEASE
