"""Background pipeline orchestrator: chains tracking, analysis, and plot generation."""

import logging
from pathlib import Path

from app.resources import ANALYSIS_PARAMS, TRACKING_CONFIG_JSON
from app.services.analysis import run_analysis
from app.services.jobs_store import job_dir, read_status, write_status
from app.services.plots import generate_plots
from app.services.results import save_legacy_txt
from app.services.tracking import run_tracking
from core.tracking_core import load_config_json

logger = logging.getLogger(__name__)


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

        write_status(data_dir, job_id, "done", plots=plot_errors)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        try:
            write_status(data_dir, job_id, "error", error=str(exc))
        except Exception:
            logger.exception("Could not write error status for job %s", job_id)
