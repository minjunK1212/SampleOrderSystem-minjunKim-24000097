import json

import pytest

from sample_order_system.model.order import OrderStatus
from sample_order_system.model.sample import Sample
from sample_order_system.repository.order_system_repository import OrderSystemRepository


def make_sample(**overrides):
    defaults = dict(
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.9,
        inventory=100,
    )
    defaults.update(overrides)
    return Sample(**defaults)


def test_release_order_transitions_to_release_and_persists(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=100))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=30)
    repo.approve_order(order.order_id)  # sufficient inventory -> CONFIRMED

    released = repo.release_order(order.order_id)

    assert released.status == OrderStatus.RELEASE
    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["orders"][0]["status"] == "RELEASE"


def test_release_order_deducts_sample_inventory(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=100))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=30)
    repo.approve_order(order.order_id)

    repo.release_order(order.order_id)

    assert repo.get_sample("S-001").inventory == 70


def test_release_order_rejects_reserved_order(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=100))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=30)

    with pytest.raises(ValueError):
        repo.release_order(order.order_id)


def test_release_order_rejects_producing_order(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=10, yield_rate=0.8))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=50)
    repo.approve_order(order.order_id)  # insufficient inventory -> PRODUCING

    with pytest.raises(ValueError):
        repo.release_order(order.order_id)


def test_release_order_rejects_already_released_order(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=100))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=30)
    repo.approve_order(order.order_id)
    repo.release_order(order.order_id)

    with pytest.raises(ValueError):
        repo.release_order(order.order_id)


def test_release_order_rejects_unknown_order_id(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    with pytest.raises(ValueError):
        repo.release_order("ORD-9999")
