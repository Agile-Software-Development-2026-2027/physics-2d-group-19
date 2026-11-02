from pathlib import Path

import pandas as pd
import pytest

from app.services.analysis import run_analysis
from tests.core.test_regression_analysis import (
    ATOL_LEGACY,
    RTOL_LEGACY,
    _load_fixture_table,
)
from tests.helpers.compare import assert_tables_close

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "exp49"


def test_same_angle_as_lab():
    out = run_analysis(
        49,
        FIXTURES_DIR / "talgae_settings.txt",
        FIXTURES_DIR / "tAlgae49.txt",
        FIXTURES_DIR,
    )
    expected = _load_fixture_table(FIXTURES_DIR / "angle_exp49", ["angle", "dist", "v"])
    assert_tables_close(out.angle, expected, rtol=RTOL_LEGACY, atol=ATOL_LEGACY)


def test_unknown_experiment_raise_value_error():
    with pytest.raises(ValueError, match="not found"):
        run_analysis(
            999,
            FIXTURES_DIR / "talgae_settings.txt",
            FIXTURES_DIR / "tAlgae49.txt",
            FIXTURES_DIR,
        )


def test_empty_trajectories_raise_value_error(tmp_path):
    empty_traj = tmp_path / "empty_trajectories.txt"
    empty_traj.write_text("frame,y,x,particle\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No trajectories to analyse"):
        run_analysis(
            49,
            FIXTURES_DIR / "talgae_settings.txt",
            empty_traj,
            FIXTURES_DIR,
        )


def test_empty_dataframe_raise_value_error(monkeypatch):
    # Mock trajectory loader to return an empty DataFrame without raising exceptions
    monkeypatch.setattr(
        "app.services.analysis.load_trajectories_txt",
        lambda _: pd.DataFrame(),
    )

    with pytest.raises(ValueError, match="No trajectories to analyse"):
        run_analysis(
            49,
            FIXTURES_DIR / "talgae_settings.txt",
            FIXTURES_DIR / "tAlgae49.txt",
            FIXTURES_DIR,
        )
