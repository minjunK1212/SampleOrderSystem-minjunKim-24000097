from sample_order_system.model.order import OrderStatus

KNOWN_ORDER_STATUSES = (
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
)

EXCLUDED_FROM_VALID_QUANTITY = (OrderStatus.REJECTED, OrderStatus.RELEASE)

STATUS_DEPLETED = "고갈"
STATUS_SHORTAGE = "부족"
STATUS_SUFFICIENT = "여유"


def count_orders_by_status(orders):
    counts = {status: 0 for status in KNOWN_ORDER_STATUSES}
    for order in orders:
        if order.status in counts:
            counts[order.status] += 1
    return counts


def valid_order_quantity_by_sample(orders):
    """REJECTED, RELEASE 상태의 주문을 제외한 시료별 유효 주문 수량 합계."""
    totals = {}
    for order in orders:
        if order.status in EXCLUDED_FROM_VALID_QUANTITY:
            continue
        totals[order.sample_id] = totals.get(order.sample_id, 0) + order.quantity
    return totals


def inventory_status(inventory, valid_quantity):
    if inventory == 0:
        return STATUS_DEPLETED
    if inventory < valid_quantity:
        return STATUS_SHORTAGE
    return STATUS_SUFFICIENT
