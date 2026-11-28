import gzip
from pathlib import Path

import pytest

from app.resources import ANALYSIS_PARAMS
from app.services.results import RESULT_NAMES, save_csv, save_legacy_txt

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "exp49"

LAB_FILES = [
    "tumb_exp49_tthres5.0.txt",
    "tumb_dur_exp49_tthres5.0.txt",
    "Theta_exp49_FluoRadialised.txt",
    "angle_exp49.txt",
    "omega_exp49.txt",
]


@pytest.fixture(scope="module")
def exp49_results_dir(tmp_path_factory, exp49_outputs):
    """Legacy .txt and CSV files of experiment 49, written from the shared analysis."""
    d = tmp_path_factory.mktemp("results")
    outputs = exp49_outputs
    save_legacy_txt(outputs, d, 49, ANALYSIS_PARAMS)
    save_csv(outputs, d)
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


def test_save_csv_writes_one_file_per_result(exp49_results_dir):
    for name in RESULT_NAMES:
        assert (exp49_results_dir / f"{name}.csv").is_file()


def test_omega_csv_has_same_rows_as_lab(exp49_results_dir):
    # both files have one header line, then one line per row
    csv_lines = (exp49_results_dir / "omega.csv").read_text().splitlines()
    lab_lines = (FIXTURES_DIR / "omega_exp49.txt").read_text().splitlines()
    assert len(csv_lines) == len(lab_lines)
