from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.history import HistoryItem, HistoryResponse
from app.schemas.jobs import JobCreate, JobResponse, JobStatus
from app.schemas.preview import PreviewRequest, PreviewResponse
from app.schemas.results import JobResultsResponse, PlotItem
from app.schemas.upload import UploadResponse


def test_job_status_values():
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.TRACKING.value == "tracking"
    assert JobStatus.ANALYZING.value == "analyzing"
    assert JobStatus.PLOTS.value == "plots"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"


def test_job_create_valid():
    job_in = JobCreate(
        experiment_id=49,
        video_filename="tAlgae49.avi",
        tracking_params={"diameter": 5, "minmass": 180},
    )
    assert job_in.experiment_id == 49
    assert job_in.video_filename == "tAlgae49.avi"
    assert job_in.tracking_params["diameter"] == 5


def test_job_create_extra_field_forbidden():
    with pytest.raises(ValidationError):
        JobCreate(experiment_id=49, video_filename="test.avi", extra_field=123)


def test_job_response_valid():
    now = datetime.now(UTC)
    res = JobResponse(
        job_id="job-123",
        status=JobStatus.TRACKING,
        current_phase="Tracking cells",
        progress=0.45,
        created_at=now,
    )
    assert res.job_id == "job-123"
    assert res.status == JobStatus.TRACKING
    assert res.progress == 0.45
    assert res.error_message is None


def test_job_response_invalid_status():
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        JobResponse(
            job_id="job-123",
            status="unknown_status",
            current_phase="Unknown",
            created_at=now,
        )


def test_results_and_plots_schemas():
    plot = PlotItem(id="theta", title="Theta Plot", url="/api/jobs/job-1/plots/theta.png")
    results = JobResultsResponse(
        job_id="job-1",
        plots=[plot],
        data_files=["Theta_exp49.txt"],
        summary={"total_tracks": 150},
    )
    assert len(results.plots) == 1
    assert results.plots[0].id == "theta"
    assert results.data_files == ["Theta_exp49.txt"]


def test_history_schemas():
    now = datetime.now(UTC)
    item = HistoryItem(
        job_id="job-49",
        experiment_id=49,
        status=JobStatus.COMPLETED,
        video_filename="tAlgae49.avi",
        created_at=now,
        duration_seconds=124.5,
    )
    history = HistoryResponse(items=[item], total=1)
    assert history.total == 1
    assert history.items[0].job_id == "job-49"
    assert history.items[0].status == JobStatus.COMPLETED


def test_upload_schema():
    up = UploadResponse(filename="tAlgae49.avi", file_type="video", size_bytes=1024)
    assert up.filename == "tAlgae49.avi"
    assert up.file_type == "video"
    assert up.size_bytes == 1024
    assert up.message == "File uploaded successfully"


def test_preview_request_valid_and_defaults():
    req = PreviewRequest()
    assert req.frame_number == 0
    assert req.diameter == 5
    assert req.minmass == 180.0
    assert req.bg_method == "mean"


def test_preview_request_rejects_even_diameter():
    with pytest.raises(ValidationError, match="diameter must be an odd integer"):
        PreviewRequest(diameter=6)


def test_preview_request_rejects_negative_frame():
    with pytest.raises(ValidationError):
        PreviewRequest(frame_number=-1)


def test_preview_response():
    resp = PreviewResponse(
        frame_number=10,
        detected_cells=42,
        image_url="/api/preview/frame10.png",
    )
    assert resp.detected_cells == 42
    assert "sampled background" in resp.note
