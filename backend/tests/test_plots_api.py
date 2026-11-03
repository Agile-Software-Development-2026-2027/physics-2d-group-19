import pytest

from app.api.deps import get_current_user
from app.config import get_settings
from app.services.jobs_store import create_job, job_dir, write_status
from app.services.plots import PLOT_NAMES

FAKE_PNG = b"\x89PNG\r\n\x1a\nfake"


@pytest.fixture
def auth_client(client):
    client.app.dependency_overrides[get_current_user] = lambda: "operator"
    return client


def _finished_job(plots: dict) -> str:
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    (job_dir(data_dir, job_id) / "plots" / "flux.png").write_bytes(FAKE_PNG)
    write_status(data_dir, job_id, "done", plots=plots)
    return job_id


@pytest.fixture
def finished_job(auth_client):
    return _finished_job({})


@pytest.fixture
def finished_job_with_flux_error(auth_client):
    return _finished_job({"flux": "boom"})


def test_list_has_one_item_per_plot(auth_client, finished_job):
    response = auth_client.get(f"/api/jobs/{finished_job}/plots")

    assert response.status_code == 200
    items = {item["name"]: item for item in response.json()}
    assert list(items) == PLOT_NAMES
    assert items["flux"] == {
        "name": "flux",
        "url": f"/api/jobs/{finished_job}/plots/flux.png",
        "error": None,
    }
    # only flux.png was written, so the other plots have no url
    assert items["angle_distribution"]["url"] is None


def test_failed_plot_has_no_url(auth_client, finished_job_with_flux_error):
    response = auth_client.get(f"/api/jobs/{finished_job_with_flux_error}/plots")

    items = {item["name"]: item for item in response.json()}
    assert items["flux"]["url"] is None
    assert items["flux"]["error"] == "boom"


def test_job_not_finished(auth_client):
    job_id = create_job(get_settings().data_dir, 49)

    assert auth_client.get(f"/api/jobs/{job_id}/plots").status_code == 409


def test_unknown_job(auth_client):
    assert auth_client.get("/api/jobs/000000000000/plots").status_code == 404
    assert auth_client.get("/api/jobs/000000000000/plots/flux.png").status_code == 404


def test_png_download(auth_client, finished_job):
    response = auth_client.get(f"/api/jobs/{finished_job}/plots/flux.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == FAKE_PNG


def test_missing_png(auth_client, finished_job):
    response = auth_client.get(f"/api/jobs/{finished_job}/plots/omega_distribution.png")

    assert response.status_code == 404


@pytest.mark.parametrize("filename", ["status.json", "flux.pdf", "flux", "secret.png"])
def test_name_outside_the_list(auth_client, finished_job, filename):
    response = auth_client.get(f"/api/jobs/{finished_job}/plots/{filename}")

    assert response.status_code == 404
