from sample_order_system.model.order import Order, OrderStatus
from sample_order_system.monitor.monitor_service import (
    count_orders_by_status,
    inventory_status,
    valid_order_quantity_by_sample,
)


def make_order(**overrides):
    defaults = dict(
        order_id="ORD-0001",
        sample_id="S-001",
        customer_name="A",
        quantity=10,
        status=OrderStatus.RESERVED,
    )
    defaults.update(overrides)
    return Order(**defaults)


def test_count_orders_by_status_counts_each_known_status():
    orders = [
        make_order(order_id="ORD-0001", status=OrderStatus.RESERVED),
        make_order(order_id="ORD-0002", status=OrderStatus.PRODUCING),
        make_order(order_id="ORD-0003", status=OrderStatus.PRODUCING),
        make_order(order_id="ORD-0004", status=OrderStatus.CONFIRMED),
        make_order(order_id="ORD-0005", status=OrderStatus.RELEASE),
    ]

    counts = count_orders_by_status(orders)

    assert counts == {
        OrderStatus.RESERVED: 1,
        OrderStatus.PRODUCING: 2,
        OrderStatus.CONFIRMED: 1,
        OrderStatus.RELEASE: 1,
    }


def test_count_orders_by_status_excludes_rejected():
    orders = [
        make_order(order_id="ORD-0001", status=OrderStatus.RESERVED),
        make_order(order_id="ORD-0002", status=OrderStatus.REJECTED),
    ]

    counts = count_orders_by_status(orders)

    assert sum(counts.values()) == 1
    assert OrderStatus.REJECTED not in counts


def test_valid_order_quantity_excludes_rejected_and_release():
    orders = [
        make_order(order_id="ORD-0001", sample_id="S-001", quantity=100, status=OrderStatus.RESERVED),
        make_order(order_id="ORD-0002", sample_id="S-001", quantity=50, status=OrderStatus.REJECTED),
        make_order(order_id="ORD-0003", sample_id="S-001", quantity=30, status=OrderStatus.RELEASE),
        make_order(order_id="ORD-0004", sample_id="S-001", quantity=20, status=OrderStatus.CONFIRMED),
    ]

    totals = valid_order_quantity_by_sample(orders)

    assert totals["S-001"] == 120  # 100(RESERVED) + 20(CONFIRMED)


def test_inventory_status_depleted_when_zero():
    assert inventory_status(inventory=0, valid_quantity=0) == "고갈"
    assert inventory_status(inventory=0, valid_quantity=50) == "고갈"


def test_inventory_status_shortage_when_below_valid_quantity():
    assert inventory_status(inventory=30, valid_quantity=31) == "부족"


def test_inventory_status_sufficient_when_at_or_above_valid_quantity():
    assert inventory_status(inventory=30, valid_quantity=30) == "여유"
    assert inventory_status(inventory=30, valid_quantity=0) == "여유"
