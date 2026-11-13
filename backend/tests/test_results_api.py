import pytest

from app.api.deps import get_current_user
from app.config import get_settings
from app.services.jobs_store import create_job, job_dir, write_status


@pytest.fixture
def auth_client(client):
    client.app.dependency_overrides[get_current_user] = lambda: "operator"
    return client


@pytest.fixture
def finished_job(auth_client):
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    (job_dir(data_dir, job_id) / "results" / "omega.csv").write_text("omega,dists,time\n1,2,3\n")
    write_status(data_dir, job_id, "done")
    return job_id


def test_list_has_only_the_existing_csv(auth_client, finished_job):
    response = auth_client.get(f"/api/jobs/{finished_job}/results")

    assert response.status_code == 200
    # only omega.csv was written, so it is the only item
    assert response.json() == [
        {"name": "omega", "url": f"/api/jobs/{finished_job}/results/omega.csv"},
    ]


def test_list_of_running_job_is_409(auth_client):
    job_id = create_job(get_settings().data_dir, 49)

    response = auth_client.get(f"/api/jobs/{job_id}/results")

    assert response.status_code == 409


def test_download_csv(auth_client, finished_job):
    response = auth_client.get(f"/api/jobs/{finished_job}/results/omega.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text == "omega,dists,time\n1,2,3\n"


@pytest.mark.parametrize("filename", ["status.json", "..%2Fstatus.json", "omega.txt", "foo.csv"])
def test_names_outside_the_list_are_404(auth_client, finished_job, filename):
    response = auth_client.get(f"/api/jobs/{finished_job}/results/{filename}")

    assert response.status_code == 404
