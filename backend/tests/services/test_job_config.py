import json

import pytest

from app.schemas.experiment import ExperimentSettings
from app.schemas.params import ProcessingParams
from app.services.job_config import load_config, save_config
from app.services.jobs_store import create_job, job_dir

EXP_49 = ExperimentSettings(exps=49, exp_type=1, ill=14, intensity=180, pix_arr=1.041667)
INPUTS = {"video": "tAlgae49.avi", "illumination": "illumination14.tiff"}


def test_save_and_load_give_the_same_values(tmp_path):
    job_id = create_job(tmp_path, 49)
    params = ProcessingParams()

    save_config(tmp_path, job_id, EXP_49, params, INPUTS)
    config = load_config(tmp_path, job_id)

    assert config["version"] == 1
    assert "created_at" in config
    assert ExperimentSettings(**config["experiment"]) == EXP_49
    assert ProcessingParams(**config["params"]) == params
    assert config["inputs"] == INPUTS


def test_unknown_version_raises_a_clear_error(tmp_path):
    job_id = create_job(tmp_path, 49)
    save_config(tmp_path, job_id, EXP_49, ProcessingParams(), INPUTS)
    path = job_dir(tmp_path, job_id) / "parameters" / "config.json"
    config = json.loads(path.read_text())
    path.write_text(json.dumps({**config, "version": 99}))

    with pytest.raises(ValueError, match="Unknown config version 99"):
        load_config(tmp_path, job_id)


def test_missing_config_raises_key_error(tmp_path):
    job_id = create_job(tmp_path, 49)

    with pytest.raises(KeyError):
        load_config(tmp_path, job_id)
