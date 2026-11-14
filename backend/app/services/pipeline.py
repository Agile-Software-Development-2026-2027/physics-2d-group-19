"""Background pipeline orchestrator: chains tracking, analysis, and plot generation."""

import json
import logging
from pathlib import Path

from app.resources import ANALYSIS_PARAMS, TRACKING_CONFIG_JSON
from app.services.analysis import run_analysis
from app.services.gif import make_gif
from app.services.jobs_store import job_dir, read_status, write_status
from app.services.plots import generate_plots
from app.services.results import save_legacy_txt
from app.services.tracking import run_tracking
from core.clam_pipeline.io import load_settings
from core.tracking_core import load_config_json

logger = logging.getLogger(__name__)


# Helper function to check if the user enabled `make_gif` in the job configuration.
# If enabled, it extracts physical analysis parameters (disc_radius, dt) and experiment
# metadata (illumination ID, pixel scale, light power), falling back to talgae_settings.txt.
def _read_gif_options(base_dir: Path, settings_txt: Path, exp_id: int) -> dict | None:
    config_path = base_dir / "parameters" / "config.json"
    if not config_path.exists():
        return None
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    # If make_gif is false or omitted, GIF rendering is skipped
    if not cfg.get("make_gif", False):
        return None

    # Retrieve parameters supplied by the user/API in config.json
    params = cfg.get("params", {})
    analysis = params.get("analysis", {})
    exp = cfg.get("experiment", {})

    # Load experimental settings table as fallback if specific fields were omitted
    settings = load_settings(settings_txt) if settings_txt.exists() else None
    row = settings.loc[settings["exps"] == exp_id] if settings is not None else None
    has_row = row is not None and not row.empty

    ill_id = int(exp.get("ill") or (int(row["ill"].iloc[0]) if has_row else 14))
    pix = float(exp.get("pix_arr") or (float(row["pix_arr"].iloc[0]) if has_row else 1 / 0.96))
    power_uw = (
        float(exp["intensity"])
        if exp.get("intensity") is not None
        else (float(row["intensity"].iloc[0]) if has_row else None)
    )
    ctrp = int(
        exp.get("ctr")
        if exp.get("ctr") is not None
        else (int(row["ctr"].iloc[0]) if has_row else 0)
    )

    return {
        "ill_id": ill_id,
        "disc_radius": float(analysis.get("disc_radius", 130.0)),
        "dt": float(analysis.get("dt", 0.1)),
        "pix": pix,
        "power_uw": power_uw,
        "ctrp": ctrp,
    }


def run_job(data_dir: Path, job_id: str) -> None:
    """Never raises: any error ends in status 'error' with its message."""
    try:
        status_data = read_status(data_dir, job_id)
        exp_id = status_data["exp_id"]
        base_dir = job_dir(data_dir, job_id)
        input_dir = base_dir / "input"
        tracking_dir = base_dir / "tracking"
        results_dir = base_dir / "results"
        plots_dir = base_dir / "plots"

        video_path = input_dir / f"tAlgae{exp_id}.avi"
        if video_path.exists():
            write_status(data_dir, job_id, "tracking")
            cfg = load_config_json(TRACKING_CONFIG_JSON)
            traj_path = run_tracking(video_path, tracking_dir, cfg)
        else:
            traj_path = input_dir / f"tAlgae{exp_id}.txt"

        settings_txt = input_dir / "talgae_settings.txt"

        write_status(data_dir, job_id, "analysis")
        outputs = run_analysis(exp_id, settings_txt, traj_path, input_dir)
        save_legacy_txt(outputs, results_dir, exp_id, ANALYSIS_PARAMS)

        write_status(data_dir, job_id, "plots")
        raw_plots = generate_plots(results_dir, settings_txt, input_dir, exp_id, plots_dir)
        plot_errors = {
            name: "Plot generation failed; see server logs" if val is None else None
            for name, val in raw_plots.items()
        }

        # Optional GIF generation: executed only if requested in `config.json` (make_gif=True).
        # In accordance with Sprint 2 specifications (Task 24.1), GIF generation runs after plots,
        # and any rendering failure is isolated: it logs the error and records `gif_error` in
        # `status.json` without failing the overall job (status remains 'done').
        gif_requested = False
        gif_error: str | None = None
        try:
            gif_opts = _read_gif_options(base_dir, settings_txt, exp_id)
            if gif_opts is not None:
                gif_requested = True
                ill_path = input_dir / f"illumination{gif_opts['ill_id']}.tiff"
                make_gif(
                    video_path=video_path,
                    trajectories_txt=traj_path,
                    illumination=ill_path,
                    out_dir=base_dir / "gif",
                    disc_radius=gif_opts["disc_radius"],
                    pix=gif_opts["pix"],
                    dt=gif_opts["dt"],
                    power_uw=gif_opts["power_uw"],
                    ctrp=gif_opts["ctrp"],
                )
        except Exception as exc:
            logger.exception("GIF generation failed for job %s", job_id)
            gif_requested = True
            gif_error = str(exc)

        # Finalize job status as 'done', saving per-plot errors and optional GIF error metadata
        extra_status: dict = {"plots": plot_errors}
        if gif_requested:
            extra_status["gif_error"] = gif_error
        write_status(data_dir, job_id, "done", **extra_status)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        try:
            write_status(data_dir, job_id, "error", error=str(exc))
        except Exception:
            logger.exception("Could not write error status for job %s", job_id)
