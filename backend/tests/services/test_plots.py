import gzip
import shutil
from pathlib import Path

import pytest

from app.services.plots import PLOT_NAMES, generate_plots
from core.analyses import plot_flux as flux_mod

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "exp49"
GZ_NEEDED = ["Flux_exp49_disc350.txt.gz", "N_dist_exp49_disc350.txt.gz"]


@pytest.fixture
def results_dir(tmp_path):
    out = tmp_path / "results"
    out.mkdir()

    for src in FIXTURES.glob("*_exp49*.txt"):
        shutil.copy(src, out / src.name)

    for name in GZ_NEEDED:
        src = FIXTURES / "reference" / name
        dst = out / name.removesuffix(".gz")
        with gzip.open(src, "rb") as f_in, open(dst, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return out


def test_generate_plots_generate_all_pngs(results_dir, tmp_path):
    settings_path = FIXTURES / "talgae_settings.txt"
    out_dir = tmp_path / "plots"
    generate_plots(results_dir, settings_path, FIXTURES, exp_id=49, out_dir=out_dir)
    for plt_name in PLOT_NAMES:
        assert (out_dir / f"{plt_name}.png").exists(), f"{plt_name}.png was not produced"


def test_one_failing_plot_does_not_stop_the_others(results_dir, tmp_path, monkeypatch):
    def broken_plot(**kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(flux_mod, "plot_flux", broken_plot)
    out_dir = tmp_path / "plots"

    result = generate_plots(
        results_dir, FIXTURES / "talgae_settings.txt", FIXTURES, exp_id=49, out_dir=out_dir
    )

    assert result["flux"] is None
    assert not (out_dir / "flux.png").exists()
    for name in PLOT_NAMES:
        if name != "flux":
            assert result[name] == str(out_dir / f"{name}.png")
            assert (out_dir / f"{name}.png").exists(), f"{name}.png was not produced"


def test_generate_plots_uses_custom_disc_radius(results_dir, tmp_path, monkeypatch):
    from core.analyses import plot_nt_stats as nt_mod
    from core.analyses import plot_theta_distribution as theta_mod

    seen = {}

    def spy_flux(**kwargs):
        seen["flux_disc"] = kwargs["disc_radius"]

    def spy_nt(**kwargs):
        seen["nt_disc"] = kwargs["disc_radius"]

    def spy_theta(**kwargs):
        seen["theta_inner"] = kwargs["inner_circle"]

    monkeypatch.setattr(flux_mod, "plot_flux", spy_flux)
    monkeypatch.setattr(nt_mod, "plot_nt_stats", spy_nt)
    monkeypatch.setattr(theta_mod, "plot_theta_distribution", spy_theta)
    monkeypatch.setattr(
        "app.services.plots.JOBS",
        {
            k: v
            for k, v in __import__("app.services.plots", fromlist=["JOBS"]).JOBS.items()
            if k in {"flux", "nt_stats", "theta_distribution"}
        },
    )

    out_dir = tmp_path / "plots"
    generate_plots(
        results_dir,
        FIXTURES / "talgae_settings.txt",
        FIXTURES,
        exp_id=49,
        out_dir=out_dir,
        disc_radius=150,
    )

    assert seen == {"flux_disc": 150, "nt_disc": 150, "theta_inner": 150}
