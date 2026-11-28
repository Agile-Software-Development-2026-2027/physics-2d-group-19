from app.services import experiments_store as store


def test_settings_copies_file(tmp_path):

    path = store.settings_path(tmp_path)
    assert path.exists()
    assert path.read_bytes() == store.RESOURCE_SETTINGS.read_bytes()


def test_get_experiment_49(tmp_path):
    experiment = store.get_experiment(tmp_path, 49)
    assert experiment.exps == 49


def test_get_experiment_missing(tmp_path):
    import pytest

    with pytest.raises(KeyError):
        store.get_experiment(tmp_path, 9999)


def test_save_new_experiment(tmp_path):
    experiment = store.get_experiment(tmp_path, 49)
    new = experiment.model_copy(update={"exps": 400})
    store.save_experiment(tmp_path, new)

    assert store.get_experiment(tmp_path, 400).exps == 400
    assert store.get_experiment(tmp_path, 49).exps == 49


def first_numbers(tmp_path):
    numbers = []
    for line in store.settings_path(tmp_path).read_text().splitlines():
        numbers.append(int(line.split()[0]))
    return numbers


def test_save_experiments_keeps_the_order(tmp_path):
    experiment = store.get_experiment(tmp_path, 49)
    new = []
    for exp_id in [470, 400, 466]:
        new.append(experiment.model_copy(update={"exps": exp_id}))

    store.save_experiments(tmp_path, new)

    numbers = first_numbers(tmp_path)
    assert numbers == sorted(numbers)
    assert numbers[-3:] == [400, 466, 470]


def test_save_experiments_replaces_a_row_of_zeros(tmp_path):
    experiment = store.get_experiment(tmp_path, 49)
    lines_before = len(first_numbers(tmp_path))

    store.save_experiments(tmp_path, [experiment.model_copy(update={"exps": 48})])

    assert store.get_experiment(tmp_path, 48).ill == 14
    assert first_numbers(tmp_path).count(48) == 1
    assert len(first_numbers(tmp_path)) == lines_before
