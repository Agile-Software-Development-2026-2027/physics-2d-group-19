from pathlib import Path

import pandas as pd

from app.schemas.experiment import ExperimentSettings
from app.services.experiment_settings import to_setting_row, to_settings_line
from core.clam_pipeline.io import load_settings

FIXTURE_FILES = Path(__file__).parent / "fixtures" / "exp49" / "talgae_settings.txt"

EXP_49 = ExperimentSettings(exps=49, exp_type=1, ill=14, intensity=180, pix_arr=1.041667)


def test_line():
    lab_line = ""
    for line in FIXTURE_FILES.read_text().splitlines():
        if line.startswith("49 "):
            lab_line = line.strip()
    assert to_settings_line(EXP_49) == lab_line


def test_row():
    expected = load_settings(FIXTURE_FILES).query("exps == 49").iloc[0]

    pd.testing.assert_series_equal(to_setting_row(EXP_49), expected, check_names=False)


def test_pixarr_six_decimals():
    settings = ExperimentSettings(exps=49, ill=14, intensity=180, pix_arr=1 / 0.96)
    parts = to_settings_line(settings).split()
    assert parts[4] == "1.041667"
