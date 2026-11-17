# End-to-end integration test on experiment 49

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import trackpy as tp
from PIL import Image

from app.config import get_settings
from app.services import pipeline
from app.users import create_user

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "exp49"

LAB_FILES = [
    "angle_exp49.txt",
    "omega_exp49.txt",
    "Theta_exp49_FluoRadialised.txt",
    "tumb_exp49_tthres5.0.txt",
    "tumb_dur_exp49_tthres5.0.txt",
]


# Full vertical slice: auth -> upload -> pipeline execution -> results -> plots
def test_exp49_from_upload_to_plots(client):
    data_dir = get_settings().data_dir
    db_path = data_dir / "users.db"

    # User creation and login via real API
    create_user(db_path, "operator", "secret")
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "secret"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Uploading experiment 49 input files
    files = {
        "trajectories": (
            "tAlgae49.txt",
            (FIXTURES_DIR / "tAlgae49.txt").read_bytes(),
        ),
        "illumination": (
            "illumination14.tiff",
            (FIXTURES_DIR / "illumination14.tiff").read_bytes(),
        ),
    }
    upload_resp = client.post(
        "/api/jobs",
        headers=headers,
        data={"exp_id": "49"},
        files=files,
    )
    assert upload_resp.status_code == 202
    job_id = upload_resp.json()["job_id"]

    # Check job completion
    status_resp = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "done"
    assert status_resp.json()["error"] is None

    # Integrity check on .txt files generated in results/
    results_dir = data_dir / "jobs" / job_id / "results"
    assert results_dir.is_dir()

    for filename in LAB_FILES:
        generated_file = results_dir / filename
        expected_file = FIXTURES_DIR / filename
        assert generated_file.exists(), f"Missing output file: {filename}"

        # Byte comparison
        gen_bytes = generated_file.read_bytes().replace(b"\r\n", b"\n")
        exp_bytes = expected_file.read_bytes().replace(b"\r\n", b"\n")
        assert gen_bytes == exp_bytes, f"Mismatch in content for {filename}"

    # Checking the list of charts
    plots_resp = client.get(f"/api/jobs/{job_id}/plots", headers=headers)
    assert plots_resp.status_code == 200
    plots = plots_resp.json()
    assert len(plots) == 8
    assert all(p["error"] is None for p in plots)
    assert all(p["url"] is not None for p in plots)

    # Actual download of the first graphic and PNG control
    sample_plot_url = plots[0]["url"]
    png_resp = client.get(sample_plot_url, headers=headers)
    assert png_resp.status_code == 200
    assert png_resp.headers["content-type"] == "image/png"
    # The first 4 bytes of the response are read to ensure the file
    # is not corrupt, empty, or a disguised error JSON
    assert png_resp.content[:4] == b"\x89PNG"


def test_exp49_from_video_clip_to_plots(client, monkeypatch):
    data_dir = get_settings().data_dir
    create_user(data_dir / "users.db", "operator", "secret")
    login = client.post("/api/auth/login", json={"username": "operator", "password": "secret"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    phases = []
    events = []
    tracked_paths = []
    real_write = pipeline.write_status
    real_tracking = pipeline.run_tracking
    real_analysis = pipeline.run_analysis
    real_batch = tp.batch

    def record_status(d, j, status, **kwargs):
        real_write(d, j, status, **kwargs)
        phases.append(pipeline.read_status(d, j)["status"])

    def track(*args, **kwargs):
        events.append("tracking_start")
        path = real_tracking(*args, **kwargs)
        tracked_paths.append(path)
        events.append("tracking_end")
        return path

    def analyse(exp_id, settings_txt, traj_path, *args, **kwargs):
        events.append("analysis_start")
        assert tracked_paths == [traj_path]
        return real_analysis(exp_id, settings_txt, traj_path, *args, **kwargs)

    def serial_batch(*args, **kwargs):
        # Keep real detection, but avoid spawning workers from TestClient's thread.
        kwargs["processes"] = 1
        return real_batch(*args, **kwargs)

    tracking_spy = Mock(side_effect=track)
    analysis_spy = Mock(side_effect=analyse)
    monkeypatch.setattr(pipeline, "write_status", record_status)
    monkeypatch.setattr(pipeline, "run_tracking", tracking_spy)
    monkeypatch.setattr(pipeline, "run_analysis", analysis_spy)
    monkeypatch.setattr(tp, "batch", serial_batch)

    with (
        (FIXTURES_DIR / "clip" / "tAlgae49_clip.avi").open("rb") as video,
        (FIXTURES_DIR / "illumination14.tiff").open("rb") as illumination,
    ):
        response = client.post(
            "/api/jobs",
            headers=headers,
            data={"exp_id": "49"},
            files={
                "video": ("tAlgae49_clip.avi", video, "video/x-msvideo"),
                "illumination": ("illumination14.tiff", illumination, "image/tiff"),
            },
        )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert len(job_id) == 12 and all(c in "0123456789abcdef" for c in job_id)
    assert response.json()["status"] == "queued"

    # TestClient has already awaited the real background task at this point.
    status = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "done", status.json()
    assert status.json()["error"] is None
    assert phases == ["tracking", "analysis", "plots", "done"]
    tracking_spy.assert_called_once()
    analysis_spy.assert_called_once()
    assert events == ["tracking_start", "tracking_end", "analysis_start"]

    base = data_dir / "jobs" / job_id
    assert tracked_paths == [base / "tracking" / "tAlgae49.txt"]
    assert not (base / "input" / "tAlgae49.txt").exists()
    trajectories = pd.read_csv(tracked_paths[0])
    assert not trajectories.empty
    assert list(trajectories.columns) == ["frame", "y", "x", "particle"]

    expected_results = LAB_FILES + [
        "N_dist_exp49_disc350.txt",
        "N_dist_compare_exp49_disc350.txt",
        "Flux_exp49_disc350.txt",
        "ThetaY_exp49.txt",
        "ThetaY_axis0_exp49.txt",
        "ThetaY_axis1_exp49.txt",
    ]
    for filename in expected_results:
        path = base / "results" / filename
        assert path.is_file(), filename
        # Header-only tables are valid; full-video reference values do not apply.
        assert path.read_text().strip(), filename

    response = client.get(f"/api/jobs/{job_id}/plots", headers=headers)
    assert response.status_code == 200
    plots = response.json()
    assert len(plots) == 8
    assert {plot["name"] for plot in plots} == {
        "theta_distribution",
        "flux",
        "density_vs_distance",
        "angle_distribution",
        "omega_distribution",
        "nt_stats",
        "tumbling_vs_gradient",
        "tumbling_duration_vs_distance",
    }
    for plot in plots:
        assert plot["error"] is None, plot
        assert plot["url"] is not None, plot
        png = client.get(plot["url"], headers=headers)
        assert png.status_code == 200
        assert png.headers["content-type"] == "image/png"
        with Image.open(BytesIO(png.content)) as image:
            assert image.format == "PNG"
            image.load()
