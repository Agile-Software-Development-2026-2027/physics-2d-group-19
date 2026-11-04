# End-to-end integration test on experiment 49

from pathlib import Path

from app.config import get_settings
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
