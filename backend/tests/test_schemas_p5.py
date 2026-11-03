from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.history import HistoryItem, HistoryResponse
from app.schemas.jobs import JobResponse, JobStatus
from app.schemas.preview import PreviewRequest, PreviewResponse
from app.schemas.results import JobResultsResponse, PlotItem
from app.schemas.upload import UploadResponse


def test_job_status_values():
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.TRACKING.value == "tracking"
    assert JobStatus.ANALYSIS.value == "analysis"
    assert JobStatus.PLOTS.value == "plots"
    assert JobStatus.DONE.value == "done"
    assert JobStatus.ERROR.value == "error"


def test_job_response_valid():
    res = JobResponse(
        job_id="job-123",
        exp_id=49,
        status=JobStatus.TRACKING,
    )
    assert res.job_id == "job-123"
    assert res.exp_id == 49
    assert res.status == JobStatus.TRACKING
    assert res.error is None


def test_job_response_error_status():
    res = JobResponse(
        job_id="job-123",
        exp_id=49,
        status=JobStatus.ERROR,
        error="Failed during tracking",
    )
    assert res.status == JobStatus.ERROR
    assert res.error == "Failed during tracking"


def test_job_response_invalid_status():
    with pytest.raises(ValidationError):
        JobResponse(
            job_id="job-123",
            exp_id=49,
            status="unknown_status",
        )


def test_results_and_plots_schemas():
    plot_ok = PlotItem(name="theta", url="/api/jobs/job-1/plots/theta.png")
    plot_failed = PlotItem(name="flux", url=None, error="Failed generating flux plot")
    results = JobResultsResponse(
        job_id="job-1",
        status=JobStatus.DONE,
        plots=[plot_ok, plot_failed],
        data_files=["Theta_exp49.txt"],
        summary={"total_tracks": 150},
    )
    assert len(results.plots) == 2
    assert results.plots[0].name == "theta"
    assert results.plots[0].url == "/api/jobs/job-1/plots/theta.png"
    assert results.plots[0].error is None
    assert results.plots[1].name == "flux"
    assert results.plots[1].url is None
    assert results.plots[1].error == "Failed generating flux plot"
    assert results.status == JobStatus.DONE


def test_history_schemas():
    now = datetime.now(UTC)
    item = HistoryItem(
        job_id="job-49",
        exp_id=49,
        status=JobStatus.DONE,
        video_filename="tAlgae49.avi",
        created_at=now,
        duration_seconds=124.5,
    )
    history = HistoryResponse(items=[item], total=1)
    assert history.total == 1
    assert history.items[0].job_id == "job-49"
    assert history.items[0].exp_id == 49
    assert history.items[0].status == JobStatus.DONE


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
