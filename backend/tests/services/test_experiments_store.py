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