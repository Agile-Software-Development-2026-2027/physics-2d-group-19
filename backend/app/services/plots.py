from pathlib import Path
import logging
import matplotlib
import matplotlib.pyplot as plt


# ruff: noqa: I001 Because ruff does not like this import style but i do :P
from core.analyses import (
    plot_angle_distribution as angle_mod,
    plot_density_vs_distance as density_mod,
    plot_flux as flux_mod,
    plot_nt_stats as nt_mod,
    plot_omega_distribution as omega_mod,
    plot_theta_distribution as theta_mod,
    plot_tumbling as tumbling_mod,
)

logger = logging.getLogger(__name__)

JOBS = {
    "theta_distribution": lambda r, s, i, e: theta_mod.plot_theta_distribution(
        results_dir=r, settings_path=s, exp_ids=e, inner_circle=INNER_CIRCLE
    ),
    "flux": lambda r, s, i, e: flux_mod.plot_flux(
        results_dir=r, settings_path=s, exp_ids=e, disc_radius=DISC_RADIUS
    ),
    "density_vs_distance": lambda r, s, i, e: density_mod.plot_density_vs_distance(
        results_dir=r, settings_path=s, illum_dir=i, exp_ids=e
    ),
    "angle_distribution": lambda r, s, i, e: angle_mod.plot_angle_distribution(
        results_dir=r, exp_ids=e
    ),
    "omega_distribution": lambda r, s, i, e: omega_mod.plot_omega_distribution(
        results_dir=r, exp_ids=e
    ),
    "nt_stats": lambda r, s, i, e: nt_mod.plot_nt_stats(
        results_dir=r, exp_ids=e, disc_radius=DISC_RADIUS
    ),
    "tumbling_vs_gradient": lambda r, s, i, e: tumbling_mod.plot_tumbling_vs_gradient(
        results_dir=r, exp_ids=e
    ),
    "tumbling_duration_vs_distance": lambda r, s, i, e: (
        tumbling_mod.plot_tumbling_duration_vs_distance(results_dir=r, exp_ids=e)
    ),
}
matplotlib.use("Agg")
INNER_CIRCLE = 300
DISC_RADIUS = 350
PLOT_NAMES = list(JOBS)


def generate_plots(
    results_dir: Path, settings_txt: Path, illum_dir: Path, exp_id: int, out_dir: Path
) -> dict[str, str | None]:

    if not results_dir.exists():
        raise FileNotFoundError(f"results_dir not found: {results_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str | None] = {}
    for name in JOBS.keys():
        try:
            JOBS[name](results_dir, settings_txt, illum_dir, [exp_id])
            file_path = out_dir / f"{name}.png"

            plt.savefig(file_path, bbox_inches="tight", dpi=300)
            logger.info("Saved plot in %s", file_path)
            results[name] = str(file_path)
        except Exception:
            logger.exception("plot %s failed", name)
            results[name] = None
        finally:
            plt.close()

    return results
