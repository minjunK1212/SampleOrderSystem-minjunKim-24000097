from dataclasses import dataclass


@dataclass(frozen=True)
class MainMenuSummary:
    sample_count: int
    total_inventory: int
    order_count: int
    production_queue_count: int


def get_main_menu_summary(repository) -> MainMenuSummary:
    samples = repository.list_samples()
    return MainMenuSummary(
        sample_count=len(samples),
        total_inventory=sum(sample.inventory for sample in samples),
        order_count=len(repository.list_orders()),
        production_queue_count=len(repository.list_production_queue()),
    )
