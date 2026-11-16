"""Background pipeline orchestrator: chains tracking, analysis, and plot generation."""

import json
import logging
from pathlib import Path

from app.schemas.params import ProcessingParams
from app.services.analysis import run_analysis
from app.services.jobs_store import job_dir, read_status, write_status
from app.services.params_mapping import to_core
from app.services.plots import generate_plots
from app.services.results import save_legacy_txt
from app.services.tracking import run_tracking

logger = logging.getLogger(__name__)


def _load_job_params(data_dir: Path, job_id: str) -> ProcessingParams:
    """Load ProcessingParams from config.json, falling back to lab defaults if missing."""
    try:
        from app.services.job_config import load_config

        config = load_config(data_dir, job_id)
    except KeyError:
        return ProcessingParams()
    except ImportError:
        config_path = job_dir(data_dir, job_id) / "parameters" / "config.json"
        if not config_path.exists():
            return ProcessingParams()
        config = json.loads(config_path.read_text(encoding="utf-8"))
    return ProcessingParams.model_validate(config["params"])


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

        params = _load_job_params(data_dir, job_id)
        tracking_cfg, analysis_params, filter_params = to_core(params)

        video_path = input_dir / f"tAlgae{exp_id}.avi"
        if video_path.exists():
            write_status(data_dir, job_id, "tracking")
            traj_path = run_tracking(video_path, tracking_dir, tracking_cfg)
        else:
            traj_path = input_dir / f"tAlgae{exp_id}.txt"

        settings_txt = input_dir / "talgae_settings.txt"

        write_status(data_dir, job_id, "analysis")
        outputs = run_analysis(
            exp_id, settings_txt, traj_path, input_dir, analysis_params, filter_params
        )
        save_legacy_txt(outputs, results_dir, exp_id, analysis_params)

        write_status(data_dir, job_id, "plots")
        raw_plots = generate_plots(
            results_dir,
            settings_txt,
            input_dir,
            exp_id,
            plots_dir,
            disc_radius=analysis_params.disc_radius,
        )
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
