from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.service import sample_service


def test_register_sample_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")

    sample = sample_service.register_sample(
        repo,
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.9,
    )

    assert sample.inventory == 0
    assert repo.get_sample("S-001") is not None


def test_list_samples_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    sample_service.register_sample(
        repo,
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.9,
    )

    samples = sample_service.list_samples(repo)

    assert len(samples) == 1


def test_search_samples_via_service(tmp_path):
    repo = OrderSystemRepository(tmp_path / "sample_management.json")
    sample_service.register_sample(
        repo,
        sample_id="S-001",
        name="Silicon Wafer 8-inch",
        average_production_time=0.5,
        yield_rate=0.9,
    )

    results = sample_service.search_samples(repo, "Wafer")

    assert len(results) == 1
