from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.history import HistoryItem
from app.schemas.jobs import JobCreateResponse, JobStatus, JobStatusResponse
from app.schemas.preview import PreviewResponse
from app.schemas.results import ResultFileItem
from app.schemas.videos import VideoUploadResponse


def test_job_status_enum_values():
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.TRACKING.value == "tracking"
    assert JobStatus.ANALYSIS.value == "analysis"
    assert JobStatus.PLOTS.value == "plots"
    assert JobStatus.DONE.value == "done"
    assert JobStatus.ERROR.value == "error"


def test_job_create_response():
    resp = JobCreateResponse(job_id="0123456789ab")
    assert resp.job_id == "0123456789ab"
    assert resp.status == JobStatus.QUEUED
    assert resp.model_dump() == {"job_id": "0123456789ab", "status": "queued"}


def test_job_status_response_success():
    now = datetime.now(UTC)
    resp = JobStatusResponse(
        job_id="0123456789ab",
        exp_id=49,
        status=JobStatus.DONE,
        created_at=now,
        plots={"flux": None, "theta": None},
        error=None,
    )
    assert resp.status == JobStatus.DONE
    assert resp.error is None
    assert resp.plots["flux"] is None


def test_job_status_response_error_state():
    resp = JobStatusResponse(
        job_id="0123456789ab",
        exp_id=49,
        status=JobStatus.ERROR,
        error="Cannot read video",
    )
    assert resp.status == JobStatus.ERROR
    assert resp.error == "Cannot read video"


def test_job_status_response_invalid_status():
    with pytest.raises(ValidationError):
        JobStatusResponse(
            job_id="0123456789ab",
            exp_id=49,
            status="non_existing_status",
        )


def test_video_upload_response():
    resp = VideoUploadResponse(
        video_id="0123456789ab",
        filename="tAlgae49.avi",
        size_bytes=1048576,
        frames=100,
        fps=25.0,
    )
    assert resp.video_id == "0123456789ab"
    assert resp.frames == 100
    assert resp.fps == 25.0


def test_preview_response():
    resp = PreviewResponse(
        frame=5,
        cell_count=42,
        image="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==",
    )
    assert resp.frame == 5
    assert resp.cell_count == 42
    assert resp.image.startswith("data:image/png")


def test_result_file_item():
    item = ResultFileItem(name="theta", url="/api/jobs/0123456789ab/results/theta.csv")
    assert item.name == "theta"
    assert item.url.endswith(".csv")


def test_history_item():
    now = datetime.now(UTC)
    item = HistoryItem(
        job_id="0123456789ab",
        exp_id=49,
        status=JobStatus.DONE,
        created_at=now,
        video="tAlgae49.avi",
    )
    assert item.job_id == "0123456789ab"
    assert item.exp_id == 49
    assert item.status == JobStatus.DONE
    assert item.video == "tAlgae49.avi"

