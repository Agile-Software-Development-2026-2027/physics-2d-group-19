import json

import pytest

from app.api import jobs
from app.config import get_settings
from app.resources import SETTINGS_TXT
from app.security import create_access_token
from app.services.jobs_store import create_job, job_dir, read_status, write_status


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    monkeypatch.setattr(jobs, "run_job", lambda *args: recorded.append(args))
    return recorded


def uploads(kind="trajectories", content=b"trajectories"):
    return {
        kind: ("arbitrary.name", content),
        "illumination": ("another.name", b"illumination"),
    }


@pytest.mark.parametrize(("kind", "extension"), [("video", "avi"), ("trajectories", "txt")])
def test_create_job(client, headers, calls, kind, extension):
    response = client.post("/api/jobs", files=uploads(kind), headers=headers)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert response.json() == {"job_id": job_id, "status": "queued"}
    data_dir = get_settings().data_dir
    inp = job_dir(data_dir, job_id) / "input"
    assert (inp / f"tAlgae49.{extension}").read_bytes() == b"trajectories"
    assert (inp / "illumination14.tiff").read_bytes() == b"illumination"
    assert (inp / "talgae_settings.txt").read_bytes() == SETTINGS_TXT.read_bytes()
    assert len(list(inp.iterdir())) == 3
    assert calls == [(data_dir, job_id)]
    status = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert status.status_code == 200
    assert status.json() == read_status(data_dir, job_id)
    assert status.json()["exp_id"] == 49
    assert status.json()["status"] == "queued"


def test_jobs_are_isolated(client, headers, calls):
    ids = [
        client.post("/api/jobs", files=uploads(content=value), headers=headers).json()["job_id"]
        for value in (b"first", b"second")
    ]
    assert ids[0] != ids[1]
    assert [
        (job_dir(get_settings().data_dir, jid) / "input/tAlgae49.txt").read_bytes() for jid in ids
    ] == [b"first", b"second"]
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("files", "data"),
    [
        ({"trajectories": ("t.txt", b"x")}, {}),
        ({"illumination": ("i.tiff", b"x")}, {}),
        ({**uploads(), "video": ("v.avi", b"x")}, {}),
        (uploads(), {"exp_id": "50"}),
        (uploads(), {"exp_id": "invalid"}),
    ],
)
def test_invalid_input_creates_nothing(client, headers, calls, files, data):
    response = client.post("/api/jobs", files=files, data=data, headers=headers)
    assert response.status_code == 422
    assert not (get_settings().data_dir / "jobs").exists()
    assert calls == []


@pytest.mark.parametrize("state", ["tracking", "analysis", "plots", "done", "error"])
def test_get_preserves_status(client, headers, state):
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    write_status(data_dir, job_id, state, error="failure", plots={"flux": "plot failure"})
    response = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == read_status(data_dir, job_id)


@pytest.mark.parametrize("job_id", ["000000000000", "invalid"])
def test_unknown_job(client, headers, job_id):
    response = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_corrupt_status_is_not_404(client, headers):
    job_id = create_job(get_settings().data_dir, 49)
    (job_dir(get_settings().data_dir, job_id) / "status.json").write_text("broken")
    with pytest.raises(json.JSONDecodeError):
        client.get(f"/api/jobs/{job_id}", headers=headers)


def test_authentication_required(client, calls):
    assert client.post("/api/jobs", files=uploads()).status_code == 401
    assert client.get("/api/jobs/000000000000").status_code == 401
    assert not (get_settings().data_dir / "jobs").exists()
    assert calls == []


@pytest.mark.parametrize("operation", ["copyfileobj", "copy"])
@pytest.mark.parametrize("status_fails", [False, True])
def test_copy_failure_does_not_start_pipeline(
    client, headers, calls, monkeypatch, operation, status_fails
):
    def fail(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(jobs.shutil, operation, fail)
    if status_fails:
        monkeypatch.setattr(jobs, "write_status", fail)
    response = client.post("/api/jobs", files=uploads(), headers=headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Could not save job input"}
    assert calls == []
    directories = list((get_settings().data_dir / "jobs").iterdir())
    assert len(directories) == 1
    if not status_fails:
        status = read_status(get_settings().data_dir, directories[0].name)
        assert status["status"] == "error"
        assert status["error"] == "disk unavailable"


def test_illumination_id_comes_from_settings(client, headers, calls, monkeypatch):
    settings = jobs.load_settings(SETTINGS_TXT)
    settings.loc[settings["exps"] == 49, "ill"] = 27
    monkeypatch.setattr(jobs, "load_settings", lambda path: settings)
    response = client.post("/api/jobs", files=uploads(), headers=headers)
    assert response.status_code == 202
    inp = job_dir(get_settings().data_dir, response.json()["job_id"]) / "input"
    assert (inp / "illumination27.tiff").read_bytes() == b"illumination"
    assert not (inp / "illumination14.tiff").exists()
