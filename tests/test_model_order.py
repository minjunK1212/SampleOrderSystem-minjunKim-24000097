import pytest

from sample_order_system.model.order import Order, OrderStatus


def make_order(**overrides):
    defaults = dict(
        order_id="ORD-0001",
        sample_id="S-001",
        customer_name="S-Semi Research",
        quantity=10,
    )
    defaults.update(overrides)
    return Order(**defaults)


def test_creates_order_with_reserved_status_by_default():
    order = make_order()
    assert order.status == OrderStatus.RESERVED


def test_rejects_quantity_below_one():
    with pytest.raises(ValueError):
        make_order(quantity=0)


def test_rejects_empty_customer_name():
    with pytest.raises(ValueError):
        make_order(customer_name="")
