import json

import pytest

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


def test_register_sample_persists_to_json_file(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)

    repo.register_sample(make_sample())

    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["samples"][0]["sample_id"] == "S-001"
    assert saved["orders"] == []
    assert saved["production_queue"] == []


def test_reload_repository_sees_existing_sample(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())

    reloaded = OrderSystemRepository(data_path)

    assert reloaded.get_sample("S-001") is not None
    assert reloaded.get_sample("S-001").name == "Silicon Wafer 8-inch"


def test_duplicate_sample_id_is_rejected(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())

    with pytest.raises(ValueError):
        repo.register_sample(make_sample(name="Different Name"))


def test_duplicate_name_is_rejected(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample())

    with pytest.raises(ValueError):
        repo.register_sample(make_sample(sample_id="S-002"))


def test_search_samples_by_name_matches_partial_name(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(sample_id="S-001", name="Silicon Wafer 8-inch"))
    repo.register_sample(make_sample(sample_id="S-002", name="GaN Epitaxial Wafer"))

    results = repo.search_samples_by_name("Wafer")

    assert {s.sample_id for s in results} == {"S-001", "S-002"}
    assert [s.sample_id for s in repo.search_samples_by_name("Silicon")] == ["S-001"]


def test_list_samples_returns_all_registered_samples(tmp_path):
    data_path = tmp_path / "sample_management.json"
    repo = OrderSystemRepository(data_path)
    repo.register_sample(make_sample(sample_id="S-001"))
    repo.register_sample(make_sample(sample_id="S-002", name="GaN Epitaxial Wafer"))

    assert len(repo.list_samples()) == 2
