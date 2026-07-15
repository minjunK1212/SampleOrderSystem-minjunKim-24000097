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


def test_reserve_order_persists_to_json_file(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())

    order = repo.reserve_order(sample_id="S-001", customer_name="S-Semi Research", quantity=10)

    assert order.order_id == "ORD-0001"
    assert order.status == OrderStatus.RESERVED
    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["orders"][0]["order_id"] == "ORD-0001"
    assert saved["orders"][0]["status"] == "RESERVED"


def test_reserve_order_rejects_unknown_sample_id(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    with pytest.raises(ValueError):
        repo.reserve_order(sample_id="S-999", customer_name="S-Semi Research", quantity=10)


def test_order_ids_increment_sequentially(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())

    first = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)
    second = repo.reserve_order(sample_id="S-001", customer_name="B", quantity=2)

    assert first.order_id == "ORD-0001"
    assert second.order_id == "ORD-0002"


def test_order_id_continues_after_reload(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())
    repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)

    reloaded = OrderSystemRepository(data_path)
    next_order = reloaded.reserve_order(sample_id="S-001", customer_name="B", quantity=2)

    assert next_order.order_id == "ORD-0002"


def test_get_order_and_list_orders(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)

    assert repo.get_order(order.order_id).customer_name == "A"
    assert len(repo.list_orders()) == 1


def test_list_orders_by_status_filters_reserved(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())
    reserved = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)
    to_reject = repo.reserve_order(sample_id="S-001", customer_name="B", quantity=2)
    repo.reject_order(to_reject.order_id)

    reserved_orders = repo.list_orders_by_status(OrderStatus.RESERVED)

    assert [o.order_id for o in reserved_orders] == [reserved.order_id]


def test_reject_order_transitions_to_rejected_and_persists(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)

    rejected = repo.reject_order(order.order_id)

    assert rejected.status == OrderStatus.REJECTED
    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["orders"][0]["status"] == "REJECTED"


def test_reject_order_rejects_unknown_order_id(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    with pytest.raises(ValueError):
        repo.reject_order("ORD-9999")


def test_reject_order_rejects_non_reserved_order(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)
    repo.reject_order(order.order_id)

    with pytest.raises(ValueError):
        repo.reject_order(order.order_id)


def test_reject_order_does_not_change_sample_inventory(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(inventory=100))
    order = repo.reserve_order(sample_id="S-001", customer_name="A", quantity=1)

    repo.reject_order(order.order_id)

    assert repo.get_sample("S-001").inventory == 100
