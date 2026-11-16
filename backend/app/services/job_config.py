"""Job configuration (23.1): the experiment, parameters and input files used by a job.

Saved once when the job starts, in jobs/<job_id>/parameters/config.json, so the
results page and the history can show how a job was run.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.experiment import ExperimentSettings
from app.schemas.params import ProcessingParams
from app.services.jobs_store import job_dir

CONFIG_VERSION = 1


def _config_path(data_dir: Path, job_id: str) -> Path:
    return job_dir(data_dir, job_id) / "parameters" / "config.json"


def save_config(
    data_dir: Path,
    job_id: str,
    exp: ExperimentSettings,
    params: ProcessingParams,
    inputs: dict,
) -> None:
    """Write config.json for an existing job; unknown job IDs raise KeyError."""
    payload = {
        "version": CONFIG_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "experiment": exp.model_dump(mode="json"),
        "params": params.model_dump(mode="json"),
        "inputs": inputs,
    }
    path = _config_path(data_dir, job_id)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_config(data_dir: Path, job_id: str) -> dict:
    """Read config.json; unknown job or missing file raise KeyError.

    A file written with another version raises ValueError, so an old or newer
    format is never read as if it were the current one.
    """
    path = _config_path(data_dir, job_id)
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KeyError(job_id) from exc
    if config.get("version") != CONFIG_VERSION:
        raise ValueError(
            f"Unknown config version {config.get('version')!r} for job {job_id}; "
            f"expected {CONFIG_VERSION}"
        )
    return config
