import io
import json
import shutil

import pytest

from app.api import jobs
from app.config import get_settings
from app.resources import SETTINGS_TXT
from app.schemas.experiment import ExperimentSettings
from app.schemas.params import ProcessingParams
from app.security import create_access_token
from app.services import job_factory
from app.services.experiments_store import save_experiment
from app.services.job_config import load_config
from app.services.jobs_store import create_job, job_dir, read_status, write_status
from app.services.uploads import save_upload
from tests.conftest import EXP49_FIXTURES


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
        (uploads(), {"exp_id": "999"}),
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

    monkeypatch.setattr(job_factory.shutil, operation, fail)
    if status_fails:
        monkeypatch.setattr(job_factory, "write_status", fail)
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


def test_illumination_id_comes_from_settings(client, headers, calls):
    data_dir = get_settings().data_dir
    save_experiment(
        data_dir,
        ExperimentSettings(exps=49, exp_type=1, ill=27, intensity=180, pix_arr=1.041667),
    )
    response = client.post("/api/jobs", files=uploads(), headers=headers)
    assert response.status_code == 202
    inp = job_dir(data_dir, response.json()["job_id"]) / "input"
    assert (inp / "illumination27.tiff").read_bytes() == b"illumination"
    assert not (inp / "illumination14.tiff").exists()


def test_create_job_with_registered_experiment_50(client, headers, calls):
    data_dir = get_settings().data_dir
    save_experiment(
        data_dir,
        ExperimentSettings(exps=50, exp_type=1, ill=20, intensity=150, pix_arr=1.0),
    )
    response = client.post("/api/jobs", files=uploads(), data={"exp_id": "50"}, headers=headers)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    inp = job_dir(data_dir, job_id) / "input"
    assert (inp / "tAlgae50.txt").read_bytes() == b"trajectories"
    assert (inp / "illumination20.tiff").read_bytes() == b"illumination"
    cfg = load_config(data_dir, job_id)
    assert cfg["experiment"]["exps"] == 50


def test_create_job_with_video_id(client, headers, calls):
    data_dir = get_settings().data_dir
    video_id = save_upload(data_dir, io.BytesIO(b"video-bytes"), "clip.avi")
    response = client.post(
        "/api/jobs",
        files={"illumination": ("illum.tiff", b"illumination")},
        data={"exp_id": "49", "video_id": video_id},
        headers=headers,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    inp = job_dir(data_dir, job_id) / "input"
    assert (inp / "tAlgae49.avi").read_bytes() == b"video-bytes"
    cfg = load_config(data_dir, job_id)
    assert cfg["inputs"]["video"] == "clip.avi"
    assert cfg["inputs"]["video_id"] == video_id


@pytest.mark.parametrize("bad_video_id", ["000000000000", "../invalid"])
def test_create_job_with_unknown_video_id_returns_404(client, headers, calls, bad_video_id):
    response = client.post(
        "/api/jobs",
        files={"illumination": ("illum.tiff", b"illumination")},
        data={"exp_id": "49", "video_id": bad_video_id},
        headers=headers,
    )
    assert response.status_code == 404
    assert not (get_settings().data_dir / "jobs").exists()
    assert calls == []


def test_create_job_rejects_video_id_with_trajectories(client, headers, calls):
    data_dir = get_settings().data_dir
    video_id = save_upload(data_dir, io.BytesIO(b"video-bytes"), "clip.avi")
    response = client.post(
        "/api/jobs",
        files=uploads("trajectories"),
        data={"exp_id": "49", "video_id": video_id},
        headers=headers,
    )
    assert response.status_code == 422
    assert calls == []


def test_create_job_with_custom_params_and_make_gif(client, headers, calls):
    data_dir = get_settings().data_dir
    params = ProcessingParams()
    params.tracking.diameter = 7
    params.analysis.disc_radius = 150
    response = client.post(
        "/api/jobs",
        files=uploads(),
        data={"exp_id": "49", "params": params.model_dump_json(), "make_gif": "true"},
        headers=headers,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    cfg = load_config(data_dir, job_id)
    assert cfg["params"]["tracking"]["diameter"] == 7
    assert cfg["params"]["analysis"]["disc_radius"] == 150
    assert cfg["make_gif"] is True


def test_create_job_with_invalid_params_returns_422(client, headers, calls):
    response = client.post(
        "/api/jobs",
        files=uploads(),
        data={"exp_id": "49", "params": json.dumps({"tracking": {"diameter": 6}})},
        headers=headers,
    )
    assert response.status_code == 422
    assert not (get_settings().data_dir / "jobs").exists()
    assert calls == []


def test_create_job_uses_stored_illumination_when_omitted(client, headers, calls):
    data_dir = get_settings().data_dir
    ill_dir = data_dir / "experiments" / "illumination"
    ill_dir.mkdir(parents=True, exist_ok=True)
    (ill_dir / "illumination14.tiff").write_bytes(b"stored-illum")

    response = client.post(
        "/api/jobs",
        files={"trajectories": ("t.txt", b"traj-bytes")},
        data={"exp_id": "49"},
        headers=headers,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    inp = job_dir(data_dir, job_id) / "input"
    assert (inp / "illumination14.tiff").read_bytes() == b"stored-illum"
    assert (inp / "tAlgae49.txt").read_bytes() == b"traj-bytes"


def test_create_job_with_only_exp_id_resolves_trajectories_and_illumination(
    client, headers, calls, tmp_path, monkeypatch
):
    traj_dir = tmp_path / "lab_traj"
    illum_dir = tmp_path / "lab_illum"
    traj_dir.mkdir()
    illum_dir.mkdir()
    shutil.copy(EXP49_FIXTURES / "tAlgae49.txt", traj_dir / "tPhot50.txt")
    (illum_dir / "illumination14.tif").write_bytes(b"lab-illum")

    monkeypatch.setenv("APP_TRAJECTORIES_DIR", str(traj_dir))
    monkeypatch.setenv("APP_ILLUMINATION_DIR", str(illum_dir))
    get_settings.cache_clear()

    data_dir = get_settings().data_dir
    save_experiment(
        data_dir,
        ExperimentSettings(exps=50, exp_type=1, ill=14, intensity=180, pix_arr=1.041667),
    )

    response = client.post("/api/jobs", data={"exp_id": "50"}, headers=headers)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    inp = job_dir(data_dir, job_id) / "input"
    assert (inp / "tAlgae50.txt").read_bytes() == (EXP49_FIXTURES / "tAlgae49.txt").read_bytes()
    assert (inp / "illumination14.tiff").read_bytes() == b"lab-illum"
    cfg = load_config(data_dir, job_id)
    assert cfg["inputs"] == {
        "trajectories": "tPhot50.txt",
        "illumination": "illumination14.tif",
    }
    assert calls == [(data_dir, job_id)]


def test_create_job_with_resolved_video_does_not_copy_video(
    client, headers, calls, tmp_path, monkeypatch
):
    video_dir = tmp_path / "lab_videos"
    traj_dir = tmp_path / "lab_traj"
    illum_dir = tmp_path / "lab_illum"
    video_dir.mkdir()
    traj_dir.mkdir()
    illum_dir.mkdir()
    video_file = video_dir / "tAlgae49.avi"
    video_file.write_bytes(b"large-video")
    (traj_dir / "tAlgae49.txt").write_bytes(b"traj")
    (illum_dir / "illumination14.tiff").write_bytes(b"lab-illum")

    monkeypatch.setenv("APP_VIDEO_DIR", str(video_dir))
    monkeypatch.setenv("APP_TRAJECTORIES_DIR", str(traj_dir))
    monkeypatch.setenv("APP_ILLUMINATION_DIR", str(illum_dir))
    get_settings.cache_clear()

    response = client.post("/api/jobs", data={"exp_id": "49"}, headers=headers)
    assert response.status_code == 202
    data_dir = get_settings().data_dir
    job_id = response.json()["job_id"]
    inp = job_dir(data_dir, job_id) / "input"
    assert not list(inp.glob("*.avi"))
    assert not (inp / "tAlgae49.txt").exists()
    cfg = load_config(data_dir, job_id)
    assert cfg["inputs"] == {
        "video": "tAlgae49.avi",
        "video_path": str(video_file.resolve()),
        "illumination": "illumination14.tiff",
    }


def test_create_job_with_only_exp_id_missing_files_returns_422(
    client, headers, calls, tmp_path, monkeypatch
):
    video_dir = tmp_path / "lab_videos"
    video_dir.mkdir()
    monkeypatch.setenv("APP_VIDEO_DIR", str(video_dir))
    get_settings.cache_clear()

    missing_media = client.post("/api/jobs", data={"exp_id": "49"}, headers=headers)
    assert missing_media.status_code == 422
    assert "Missing video or trajectories for experiment 49" in missing_media.json()["detail"]

    (video_dir / "tAlgae49.avi").write_bytes(b"video")
    missing_illum = client.post("/api/jobs", data={"exp_id": "49"}, headers=headers)
    assert missing_illum.status_code == 422
    assert "illumination14.tiff" in missing_illum.json()["detail"]
    assert calls == []
