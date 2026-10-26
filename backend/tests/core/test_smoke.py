import importlib
from dataclasses import fields

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from core.clam_pipeline.analyze import AnalysisParams, FilterParams, analyze_experiment
from core.tracking_core import (
    TrackingConfig,
    load_linked_df,
    run_link_in_h5,
    run_locate_to_h5,
    save_outputs,
)

CORE_MODULES = [
    "core.clamutils_exp",
    "core.tracking_core",
    "core.clam_pipeline.analyze",
    "core.clam_pipeline.io",
    "core.analyses.common",
    "core.analyses.load_results",
    "core.analyses.plot_angle_distribution",
    "core.analyses.plot_density_vs_distance",
    "core.analyses.plot_flux",
    "core.analyses.plot_nt_stats",
    "core.analyses.plot_omega_distribution",
    "core.analyses.plot_theta_distribution",
    "core.analyses.plot_theta_y_distribution",
    "core.analyses.plot_tumbling",
]

N_FRAMES, SIZE = 10, 64
START_POSITIONS = [(15, 10), (32, 20), (48, 30)]  # (y, x) of each synthetic cell

# Values of legacy config_tracking-49-65.json, except minmass and search_range,
# lowered for the small synthetic cells.
TRACKING_CONFIG = TrackingConfig(
    channel=2,
    background_subtraction=True,
    background_method="mean",
    diameter=5,
    minmass=50,
    invert=False,
    search_range=5,
    adaptive_stop=5,
    adaptive_step=0.98,
    memory=None,
    filter_stubs=0,
)

EXPECTED_ANALYSIS_COLUMNS = {
    "theta": ["theta", "dist"],
    "theta_y": ["theta_y", "dist"],
    "theta_y_axis0": ["theta_y", "dist"],
    "theta_y_axis1": ["theta_y", "dist"],
    "flux": ["time", "flux"],
    "angle": ["angle", "dist", "v"],
    "omega": ["omega", "dist", "time"],
    "tumbling_orientation": ["theta", "dist", "duration", "time"],
    "tumbling_duration": ["dist", "duration", "time"],
    "nt_stats": ["N_raw", "n_disc_raw", "dists_raw", "N", "n_disc", "dists"],
}


@pytest.mark.parametrize("name", CORE_MODULES)
def test_core_module_imports(name):
    importlib.import_module(name)


@pytest.fixture
def frames():
    yy, xx = np.mgrid[:SIZE, :SIZE]
    out = np.zeros((N_FRAMES, SIZE, SIZE), dtype=np.float32)
    for t in range(N_FRAMES):
        for y0, x0 in START_POSITIONS:
            out[t] += 200 * np.exp(-((yy - y0) ** 2 + (xx - x0 - t) ** 2) / (2 * 1.5**2))
    return out


def test_tracking_finds_and_links_every_cell(frames, tmp_path):
    h5_path = tmp_path / "tracking.h5"

    run_locate_to_h5(frames, h5_path, TRACKING_CONFIG)
    run_link_in_h5(h5_path, TRACKING_CONFIG, N_FRAMES)
    df = load_linked_df(h5_path)

    assert {"frame", "x", "y", "particle"} <= set(df.columns)
    assert df["particle"].nunique() == len(START_POSITIONS)
    assert len(df) == N_FRAMES * len(START_POSITIONS)

    save_outputs(df, tmp_path / "out", TRACKING_CONFIG.filter_stubs)
    assert (tmp_path / "out.pkl").exists()
    with open(tmp_path / "out.txt") as f:
        assert f.readline().strip() == "frame,y,x,particle"


def test_analyze_experiment_returns_every_table(tmp_path):
    # With ill=0 the core loads illumination1.tiff from the illumination folder.
    Image.fromarray(np.full((256, 256), 128, dtype=np.uint8)).save(tmp_path / "illumination1.tiff")
    settings = pd.Series({"pix_arr": 1.0, "ill": 0, "ctr": 1, "intensity": 180})
    trajectories = pd.DataFrame(
        [
            {"snap": t, "y_px": y0, "x_px": x0 + t, "tag": tag}
            for tag, (y0, x0) in enumerate(START_POSITIONS)
            for t in range(N_FRAMES)
        ]
    )

    out = analyze_experiment(
        exp_id=49,
        settings_row=settings,
        traj_df=trajectories,
        illum_dir=tmp_path,
        radial_dir=tmp_path,
        params=AnalysisParams(radial_map=False),
        fparams=FilterParams(),
    )

    assert [f.name for f in fields(out)] == list(EXPECTED_ANALYSIS_COLUMNS)
    for name, columns in EXPECTED_ANALYSIS_COLUMNS.items():
        assert list(getattr(out, name).columns) == columns, name
