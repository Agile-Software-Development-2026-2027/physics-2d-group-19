import pytest

from app.api.deps import get_current_user
from app.config import get_settings
from app.schemas.experiment import ExperimentSettings
from app.schemas.params import ProcessingParams
from app.services.job_config import save_config
from app.services.jobs_store import create_job


@pytest.fixture
def auth_client(client):
    client.app.dependency_overrides[get_current_user] = lambda: "operator"
    return client


def test_returns_the_saved_config(auth_client):
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    exp = ExperimentSettings(exps=49, exp_type=1, ill=14, intensity=180, pix_arr=1.041667)
    save_config(data_dir, job_id, exp, ProcessingParams(), {"video": "tAlgae49.avi"})

    response = auth_client.get(f"/api/jobs/{job_id}/config")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["experiment"]["exps"] == 49
    assert body["params"]["analysis"]["disc_radius"] == 350
    assert body["inputs"] == {"video": "tAlgae49.avi"}


def test_job_without_config_is_404(auth_client):
    job_id = create_job(get_settings().data_dir, 49)

    assert auth_client.get(f"/api/jobs/{job_id}/config").status_code == 404


@pytest.mark.parametrize("job_id", ["000000000000", "not-a-job", "..%2Fstatus.json"])
def test_unknown_job_is_404(auth_client, job_id):
    assert auth_client.get(f"/api/jobs/{job_id}/config").status_code == 404


def test_new_job_saves_its_config(auth_client, monkeypatch):
    monkeypatch.setattr("app.api.jobs.run_job", lambda *args: None)
    files = {
        "video": ("my_video.avi", b"video"),
        "illumination": ("my_ill.tiff", b"illumination"),
    }

    job_id = auth_client.post("/api/jobs", files=files).json()["job_id"]
    response = auth_client.get(f"/api/jobs/{job_id}/config")

    assert response.status_code == 200
    body = response.json()
    assert body["experiment"]["exps"] == 49
    assert body["experiment"]["ill"] == 14
    assert body["params"] == ProcessingParams().model_dump(mode="json")
    assert body["inputs"] == {"video": "my_video.avi", "illumination": "my_ill.tiff"}
