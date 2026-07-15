from sample_order_system.model.order import OrderStatus


def reserve_order(repository, sample_id, customer_name, quantity):
    return repository.reserve_order(sample_id, customer_name, quantity)


def list_reserved_orders(repository):
    return repository.list_orders_by_status(OrderStatus.RESERVED)


def reject_order(repository, order_id):
    return repository.reject_order(order_id)
