import pytest

from sample_order_system.model.production_queue import ProductionQueueItem


def make_queue_item(**overrides):
    defaults = dict(
        order_id="ORD-0001",
        sample_id="S-001",
        required_quantity=10,
        production_quantity=12,
        queue_position=1,
    )
    defaults.update(overrides)
    return ProductionQueueItem(**defaults)


def test_creates_valid_queue_item():
    item = make_queue_item()
    assert item.queue_position == 1


def test_rejects_required_quantity_below_one():
    with pytest.raises(ValueError):
        make_queue_item(required_quantity=0)


def test_rejects_production_quantity_below_one():
    with pytest.raises(ValueError):
        make_queue_item(production_quantity=0)


def test_rejects_queue_position_below_one():
    with pytest.raises(ValueError):
        make_queue_item(queue_position=0)
