import pytest
from pydantic import ValidationError

from app.schemas.experiment import ExperimentSettings
from core.clam_pipeline.io import SETTINGS_COLUMNS

EXP_49 = dict(exps=49, exp_type=1, ill=14, intensity=180, pix_arr=1.041667)


def test_exp49_is_valid():
    settings = ExperimentSettings(**EXP_49)
    assert settings.no_skip is True
    assert settings.ctr == 0
    assert settings.fluo == 0
    assert settings.lin == 0
    assert settings.axis == 0


def test_pix_arr_zero():
    with pytest.raises(ValueError):
        ExperimentSettings(**{**EXP_49, "pix_arr": 0})


def test_negative_experiment():
    with pytest.raises(ValueError):
        ExperimentSettings(**{**EXP_49, "exps": -1})


def test_ctr_not_allowed():
    with pytest.raises(ValueError):
        ExperimentSettings(**{**EXP_49, "ctr": 2})


def test_missing_fields():
    with pytest.raises(ValueError):
        ExperimentSettings(exps=49)


def test_unknown_field():
    with pytest.raises(ValidationError):
        ExperimentSettings(**EXP_49, intesity=180)


def test_every_field_has_description():
    for name, field in ExperimentSettings.model_fields.items():
        assert field.description, f"{name} has no description"


def test_fields_have_the_same_order_as_the_core():
    assert list(ExperimentSettings.model_fields) == SETTINGS_COLUMNS
