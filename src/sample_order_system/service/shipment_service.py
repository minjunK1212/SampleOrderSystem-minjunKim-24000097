from sample_order_system.model.order import OrderStatus


def list_confirmed_orders(repository):
    return repository.list_orders_by_status(OrderStatus.CONFIRMED)


def release_order(repository, order_id):
    return repository.release_order(order_id)
