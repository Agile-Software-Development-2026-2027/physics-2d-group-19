import json
from datetime import datetime

import pytest

from app.api import experiments as api
from app.security import create_access_token
from app.services.experiments_store import settings_path

URL = "/api/experiments/49/illumination"


@pytest.fixture
def auth_headers(client):
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


@pytest.fixture
def upload(client, auth_headers):
    def send(filename="original.tiff", content=b"synthetic image", exp_id=49, headers=None):
        return client.post(
            f"/api/experiments/{exp_id}/illumination",
            files={"file": (filename, content, "application/octet-stream")},
            headers=auth_headers if headers is None else headers,
        )

    return send


def canonical(data_dir, ill=14):
    return data_dir / "experiments" / "illumination" / f"illumination{ill}.tiff"


@pytest.mark.parametrize(
    "filename",
    ["other.tif", "original.tiff", "upper.TIF", "upper.TIFF", "../../escape.tif", "/tmp/x.tiff"],
)
def test_real_storage_and_canonical_bytes(upload, tmp_path, filename):
    settings = settings_path(tmp_path)
    before = settings.read_bytes()
    content = b"synthetic\x00\xffimage"
    response = upload(filename, content)
    assert response.status_code == 201
    assert response.json() == {"ill": 14, "filename": "illumination14.tiff"}
    assert canonical(tmp_path).read_bytes() == content
    assert settings.read_bytes() == before
    [directory] = (tmp_path / "uploads").iterdir()
    assert api.upload_path(tmp_path, directory.name) == directory / "content"
    assert {p.name for p in directory.iterdir()} == {"content", "meta.json"}
    assert (directory / "content").read_bytes() == content
    metadata = json.loads((directory / "meta.json").read_text())
    assert metadata["filename"] == filename
    assert metadata["size_bytes"] == len(content)
    assert datetime.fromisoformat(metadata["created_at"]).utcoffset().total_seconds() == 0
    assert set(tmp_path.rglob("*")) == {
        settings.parent,
        settings,
        canonical(tmp_path).parent,
        canonical(tmp_path),
        directory.parent,
        directory,
        directory / "content",
        directory / "meta.json",
    }


@pytest.mark.parametrize("ill", [0, 14, 27])
def test_new_experiment_uses_ill_and_shared_upload_replaces(
    upload, client, auth_headers, tmp_path, ill
):
    assert upload(content=b"previous").status_code == 201
    body = client.get("/api/experiments/49", headers=auth_headers).json()
    body.update(exps=400, ill=ill)
    assert client.put("/api/experiments/400", json=body, headers=auth_headers).status_code == 200
    before = settings_path(tmp_path).read_bytes()
    response = upload(content=b"replacement", exp_id=400)
    assert response.status_code == 201
    assert response.json() == {"ill": ill, "filename": f"illumination{ill}.tiff"}
    assert canonical(tmp_path, ill).read_bytes() == b"replacement"
    assert not canonical(tmp_path, 400).exists()
    assert canonical(tmp_path).read_bytes() == (b"replacement" if ill == 14 else b"previous")
    assert settings_path(tmp_path).read_bytes() == before
    assert len(list((tmp_path / "uploads").iterdir())) == 2
    assert sorted(p.name for p in canonical(tmp_path).parent.iterdir()) == sorted(
        {"illumination14.tiff", f"illumination{ill}.tiff"}
    )


@pytest.mark.parametrize(
    ("filename", "content", "status"),
    [
        ("x.png", b"x", 422),
        ("x", b"x", 422),
        ("x.tiff.exe", b"x", 422),
        (None, b"x", 422),
        ("", b"x", 422),
        ("empty.tif", b"", 400),
    ],
)
def test_invalid_upload_leaves_existing_files_unchanged(
    upload, tmp_path, filename, content, status
):
    settings_path(tmp_path)
    target = canonical(tmp_path)
    target.parent.mkdir()
    target.write_bytes(b"keep")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert upload(filename, content).status_code == status
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    assert not (tmp_path / "uploads").exists()


def test_unregistered_experiment_has_no_upload(upload, client, auth_headers, tmp_path):
    assert client.get("/api/experiments/9999999", headers=auth_headers).status_code == 404
    assert upload(exp_id=9999999).status_code == 404
    assert not (tmp_path / "uploads").exists()
    assert not canonical(tmp_path).parent.exists()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid"}])
def test_unauthorized_upload_saves_nothing(upload, tmp_path, headers):
    assert upload(headers=headers).status_code == 401
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("files", [None, {"img": ("image.tiff", b"x")}])
def test_file_field_is_required(client, auth_headers, tmp_path, files):
    assert client.post(URL, headers=auth_headers, files=files).status_code == 422
    assert not list(tmp_path.iterdir())
