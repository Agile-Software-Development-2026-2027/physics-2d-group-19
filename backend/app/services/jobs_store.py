"""Disk-backed job storage. Each job has one writer and may have multiple readers."""

import json
import os
import re
import uuid
from pathlib import Path


def _save_status(directory: Path, payload: dict) -> None:
    serialized = json.dumps(payload)
    temporary = directory / "status.json.tmp"
    temporary.write_text(serialized, encoding="utf-8")
    os.replace(temporary, directory / "status.json")


def create_job(data_dir: Path, exp_id: int) -> str:
    """Create an isolated job with queued status, retrying ID collisions."""
    jobs = data_dir / "jobs"
    jobs.mkdir(parents=True, exist_ok=True)
    while True:
        job_id = uuid.uuid4().hex[:12]
        directory = jobs / job_id
        try:
            directory.mkdir()
        except FileExistsError:
            continue
        break
    for name in ("input", "tracking", "results", "plots"):
        (directory / name).mkdir()
    _save_status(directory, {"job_id": job_id, "exp_id": exp_id, "status": "queued", "error": None})
    return job_id


def job_dir(data_dir: Path, job_id: str) -> Path:
    """Resolve an existing job; invalid or unknown IDs raise KeyError."""
    if not isinstance(job_id, str) or re.fullmatch(r"[0-9a-f]{12}", job_id) is None:
        raise KeyError(job_id)
    directory = data_dir / "jobs" / job_id
    if not directory.is_dir():
        raise KeyError(job_id)
    return directory


def read_status(data_dir: Path, job_id: str) -> dict:
    """Read persisted status; missing jobs/status raise KeyError, corrupt JSON propagates."""
    directory = job_dir(data_dir, job_id)
    try:
        return json.loads((directory / "status.json").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KeyError(job_id) from exc


def write_status(
    data_dir: Path, job_id: str, status: str, error: str | None = None, **extra
) -> None:
    """Replace status atomically, preserving metadata and clearing error by default.

    State transitions are the orchestrator's responsibility. Atomic replacement
    protects readers from partial JSON, but does not coordinate concurrent writers.
    """
    if {"job_id", "exp_id"} & extra.keys():
        raise ValueError("Job identity cannot be changed")
    payload = read_status(data_dir, job_id)
    payload.update(extra)
    payload.update(status=status, error=error)
    _save_status(job_dir(data_dir, job_id), payload)
