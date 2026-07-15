from dataclasses import dataclass

from sample_order_system.monitor import monitor_service


@dataclass
class SampleInventoryRow:
    sample_id: str
    name: str
    inventory: int
    valid_quantity: int
    status: str


def get_order_status_counts(repository):
    return monitor_service.count_orders_by_status(repository.list_orders())


def get_sample_inventory_report(repository):
    valid_quantities = monitor_service.valid_order_quantity_by_sample(repository.list_orders())
    rows = []
    for sample in repository.list_samples():
        valid_quantity = valid_quantities.get(sample.sample_id, 0)
        rows.append(
            SampleInventoryRow(
                sample_id=sample.sample_id,
                name=sample.name,
                inventory=sample.inventory,
                valid_quantity=valid_quantity,
                status=monitor_service.inventory_status(sample.inventory, valid_quantity),
            )
        )
    return rows
