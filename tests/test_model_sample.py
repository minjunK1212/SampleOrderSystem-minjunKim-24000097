import pytest

from sample_order_system.model.sample import Sample


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


def test_creates_valid_sample():
    sample = make_sample()
    assert sample.sample_id == "S-001"
    assert sample.inventory == 100


def test_rejects_empty_sample_id():
    with pytest.raises(ValueError):
        make_sample(sample_id="")


def test_rejects_empty_name():
    with pytest.raises(ValueError):
        make_sample(name="")


def test_rejects_non_positive_average_production_time():
    with pytest.raises(ValueError):
        make_sample(average_production_time=0)


def test_rejects_yield_rate_out_of_range():
    with pytest.raises(ValueError):
        make_sample(yield_rate=0)
    with pytest.raises(ValueError):
        make_sample(yield_rate=1.5)


def test_rejects_negative_inventory():
    with pytest.raises(ValueError):
        make_sample(inventory=-1)


def test_rejects_non_integer_inventory():
    with pytest.raises(ValueError):
        make_sample(inventory=1.5)
