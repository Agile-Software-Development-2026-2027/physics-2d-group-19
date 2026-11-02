import gzip
from pathlib import Path

import pytest

from app.services.results import save_legacy_txt
from core.clam_pipeline.analyze import AnalysisParams, FilterParams, analyze_experiment
from core.clam_pipeline.io import load_settings, load_trajectories_txt

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "exp49"

LAB_FILES = [
    "tumb_exp49_tthres5.0.txt",
    "tumb_dur_exp49_tthres5.0.txt",
    "Theta_exp49_FluoRadialised.txt",
    "angle_exp49.txt",
    "omega_exp49.txt",
]

# Analysis_param copied from the script make_reference.py
ANALYSIS_PARAMS = AnalysisParams(
    diam=10,
    dt=0.1,
    particle_show=5,
    disc_radius=350,
    flux_cg_in=1,
    flux_cg_out=150,
    tumbling_threshold=5.0,
    radial_map=False,
    nskip=1,
)

# Filter copied from the script make_reference.py
FILTER_PARAMS = FilterParams(
    lifetime_min=0,
    threshold_dist=0,
    threshold_dist_tot=0,
    dist_step=1,
    strict=True,
    only_inside=True,
    blinking_ratio=0,
    blinking_tolerance=0,
    long_track_min_snaps=0,
)


@pytest.fixture(scope="module")
def exp49_results_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("results")

    settings = load_settings(FIXTURES_DIR / "talgae_settings.txt")
    row = settings.loc[settings["exps"] == 49].iloc[0]
    traj_df = load_trajectories_txt(FIXTURES_DIR / "tAlgae49.txt")

    outputs = analyze_experiment(
        exp_id=49,
        settings_row=row,
        traj_df=traj_df,
        illum_dir=FIXTURES_DIR,
        radial_dir=FIXTURES_DIR / "_unused_radial_map",
        params=ANALYSIS_PARAMS,
        fparams=FILTER_PARAMS,
    )

    save_legacy_txt(outputs, d, 49, ANALYSIS_PARAMS)
    return d


@pytest.mark.parametrize("name", LAB_FILES)
def test_same_bytes_as_lab(exp49_results_dir, name):
    generated = (exp49_results_dir / name).read_bytes().replace(b"\r\n", b"\n")
    lab = (FIXTURES_DIR / name).read_bytes().replace(b"\r\n", b"\n")
    assert generated == lab


def test_flux_same_as_reference(exp49_results_dir):
    ref = FIXTURES_DIR / "reference" / "Flux_exp49_disc350.txt.gz"
    generated_flux = (
        (exp49_results_dir / "Flux_exp49_disc350.txt").read_bytes().replace(b"\r\n", b"\n")
    )
    expected_flux = gzip.decompress(ref.read_bytes()).replace(b"\r\n", b"\n")
    assert generated_flux == expected_flux
