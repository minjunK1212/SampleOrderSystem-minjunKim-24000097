import math

import pytest

from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import (
    OrderSystemDataError,
    OrderSystemRepository,
)


def test_starts_empty_when_file_missing(tmp_path):
    data_path = tmp_path / "sample_management.json"

    repo = OrderSystemRepository(data_path)

    assert repo.list_samples() == []
    assert repo.list_orders() == []
    assert repo.list_production_queue() == []


def test_malformed_json_raises_clear_error(tmp_path):
    data_path = tmp_path / "sample_management.json"
    data_path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(OrderSystemDataError) as exc_info:
        OrderSystemRepository(data_path)

    assert str(data_path) in str(exc_info.value)


def test_full_lifecycle_survives_repository_restart(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=100))

    # REJECTED path
    rejected_order = repo.reserve_order(sample_id="S-001", customer_name="Rejected Co", quantity=10)
    repo.reject_order(rejected_order.order_id)

    # CONFIRMED (sufficient inventory) then RELEASE path: inventory 100 -> 80
    released_order = repo.reserve_order(sample_id="S-001", customer_name="Released Co", quantity=20)
    repo.approve_order(released_order.order_id)
    repo.release_order(released_order.order_id)

    # PRODUCING path (insufficient inventory), left incomplete: required=200-80=120
    producing_order = repo.reserve_order(sample_id="S-001", customer_name="Producing Co", quantity=200)
    repo.approve_order(producing_order.order_id)

    # untouched RESERVED order
    reserved_order = repo.reserve_order(sample_id="S-001", customer_name="Reserved Co", quantity=5)

    reloaded = OrderSystemRepository(data_path)

    assert reloaded.get_sample("S-001").inventory == 80
    assert reloaded.get_order(rejected_order.order_id).status == OrderStatus.REJECTED
    assert reloaded.get_order(released_order.order_id).status == OrderStatus.RELEASE
    assert reloaded.get_order(producing_order.order_id).status == OrderStatus.PRODUCING
    assert reloaded.get_order(reserved_order.order_id).status == OrderStatus.RESERVED

    queue = reloaded.list_production_queue()
    assert len(queue) == 1
    assert queue[0].order_id == producing_order.order_id
    assert queue[0].required_quantity == 120
    assert queue[0].production_quantity == math.ceil(120 / 0.8)


def test_recovered_repository_supports_further_operations(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(Sample("S-001", "Silicon Wafer 8-inch", 0.5, 0.8, inventory=10))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    repo.approve_order(order.order_id)  # PRODUCING

    reloaded = OrderSystemRepository(data_path)
    completed = reloaded.complete_current_production()

    assert completed.order_id == order.order_id
    assert completed.status == OrderStatus.CONFIRMED
    assert reloaded.get_sample("S-001").inventory > 10
