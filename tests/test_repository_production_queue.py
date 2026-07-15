import json
import math

import pytest

from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository


def make_sample(**overrides):
    defaults = dict(
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.8,
        inventory=10,
    )
    defaults.update(overrides)
    return Sample(**defaults)


def test_approve_order_with_insufficient_inventory_transitions_to_producing(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)

    approved = repo.approve_order(order.order_id)

    assert approved.status == OrderStatus.PRODUCING
    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["orders"][0]["status"] == "PRODUCING"
    assert len(saved["production_queue"]) == 1


def test_approve_order_with_insufficient_inventory_creates_correct_queue_item(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10, yield_rate=0.8))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)

    repo.approve_order(order.order_id)

    queue_item = repo.list_production_queue()[0]
    assert queue_item.order_id == order.order_id
    assert queue_item.sample_id == "S-001"
    assert queue_item.required_quantity == 40  # 50 - 10
    assert queue_item.production_quantity == math.ceil(40 / 0.8)


def test_approve_order_with_insufficient_inventory_does_not_change_inventory(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)

    repo.approve_order(order.order_id)

    assert repo.get_sample("S-001").inventory == 10


def test_queue_positions_are_sequential_across_multiple_approvals(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    first_order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    second_order = repo.reserve_order(sample_id="S-001", customer_name="B", quantity=60)

    repo.approve_order(first_order.order_id)
    repo.approve_order(second_order.order_id)

    positions = [item.queue_position for item in repo.list_production_queue()]
    assert positions == [1, 2]


def test_required_quantity_is_at_least_one(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=9))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=10)

    repo.approve_order(order.order_id)

    queue_item = repo.list_production_queue()[0]
    assert queue_item.required_quantity == 1


def test_get_current_production_job_returns_first_by_queue_position(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    first_order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    second_order = repo.reserve_order(sample_id="S-001", customer_name="B", quantity=60)
    repo.approve_order(first_order.order_id)
    repo.approve_order(second_order.order_id)

    current = repo.get_current_production_job()

    assert current.order_id == first_order.order_id
    assert current.queue_position == 1


def test_get_current_production_job_returns_none_when_queue_empty(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    assert repo.get_current_production_job() is None


def test_complete_current_production_increases_sample_inventory(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10, yield_rate=0.8))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    repo.approve_order(order.order_id)
    production_quantity = repo.get_current_production_job().production_quantity

    repo.complete_current_production()

    assert repo.get_sample("S-001").inventory == 10 + production_quantity


def test_complete_current_production_transitions_order_to_confirmed(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    repo.approve_order(order.order_id)

    completed_order = repo.complete_current_production()

    assert completed_order.order_id == order.order_id
    assert completed_order.status == OrderStatus.CONFIRMED
    assert repo.get_order(order.order_id).status == OrderStatus.CONFIRMED


def test_complete_current_production_removes_item_and_advances_to_next(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10))
    first_order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    second_order = repo.reserve_order(sample_id="S-001", customer_name="B", quantity=60)
    repo.approve_order(first_order.order_id)
    repo.approve_order(second_order.order_id)

    repo.complete_current_production()

    assert len(repo.list_production_queue()) == 1
    assert repo.get_current_production_job().order_id == second_order.order_id


def test_complete_current_production_raises_when_queue_empty(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    with pytest.raises(ValueError):
        repo.complete_current_production()
