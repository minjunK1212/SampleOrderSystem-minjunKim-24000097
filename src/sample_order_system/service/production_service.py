def get_current_job(repository):
    return repository.get_current_production_job()


def list_production_queue(repository):
    return repository.list_production_queue()


def complete_current_production(repository):
    return repository.complete_current_production()
