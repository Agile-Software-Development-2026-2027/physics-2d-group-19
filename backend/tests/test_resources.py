# Tests for the resources of experiment 49

from pathlib import Path

from app.resources import SETTINGS_TXT, TRACKING_CONFIG_JSON
from core.clam_pipeline.io import load_settings
from core.tracking_core import load_config_json

# Folder with the lab files used as reference
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "exp49"


def test_settings_row_49():
    # The row of experiment 49 can be read and has the right values
    row = load_settings(SETTINGS_TXT).query("exps == 49").iloc[0]
    assert row["ill"] == 14
    assert row["pix_arr"] == 1.041667


def test_same_files_as_lab():
    # The copied file is identical to the one of the lab
    mine = SETTINGS_TXT.read_bytes()
    lab = (FIXTURES_DIR / "talgae_settings.txt").read_bytes()
    assert mine == lab


def test_tracking_config_loads():
    # The tracking config can be loaded and minmass is 180
    config = load_config_json(TRACKING_CONFIG_JSON)
    assert config.minmass == 180
