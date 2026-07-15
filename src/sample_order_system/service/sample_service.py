from sample_order_system.model.sample import Sample


def register_sample(repository, sample_id, name, average_production_time, yield_rate):
    sample = Sample(sample_id, name, average_production_time, yield_rate, inventory=0)
    return repository.register_sample(sample)


def list_samples(repository):
    return repository.list_samples()


def search_samples(repository, keyword):
    return repository.search_samples_by_name(keyword)
