import pytest

from app.config import get_settings
from app.security import create_access_token
from app.services.experiments_store import RESOURCE_SETTINGS, settings_path


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


def upload(client, auth_headers, content: bytes):
    files = {"file": ("Clamidomoni_settings.txt", content, "text/plain")}
    return client.post("/api/experiments/import", files=files, headers=auth_headers)


def test_import_with_bom_then_export_gives_the_same_file(client, auth_headers):
    response = upload(client, auth_headers, b"\xef\xbb\xbf" + RESOURCE_SETTINGS.read_bytes())
    assert response.status_code == 200
    assert response.json()["errors"] == []

    exported = client.get("/api/experiments/export", headers=auth_headers)

    # 200 and not 422: GET /export is not read as GET /{exp_id}
    assert exported.status_code == 200
    assert "Clamidomoni_settings.txt" in exported.headers["content-disposition"]
    assert exported.content == RESOURCE_SETTINGS.read_bytes()


def test_line_with_9_numbers_gives_422_and_writes_nothing(client, auth_headers):
    path = settings_path(get_settings().data_dir)
    before = path.read_bytes()
    content = b"466 1 14 180 1.041667 1 0 0 0 0\n467 1 14 180 1.041667 1 0 0 0\n"

    response = upload(client, auth_headers, content)

    assert response.status_code == 422
    assert "Line 2" in response.json()["detail"]
    assert path.read_bytes() == before


def test_invalid_value_goes_in_errors_and_the_rest_is_imported(client, auth_headers):
    content = (
        b"466 1 14 180 1.041667 1 0 0 0 0\n"
        b"467 9 14 180 1.041667 1 0 0 0 0\n"
        b"468 0 0 0 0.000000 0 0 0 0 0\n"
        b"49 1 14 200 1.041667 1 0 0 0 0\n"
    )

    response = upload(client, auth_headers, content)

    assert response.status_code == 200
    result = response.json()
    assert result["created"] == 1
    assert result["updated"] == 1
    assert result["skipped_empty"] == 1
    assert result["errors"][0]["line"] == 2
    assert "exp_type" in result["errors"][0]["detail"]
    assert client.get("/api/experiments/466", headers=auth_headers).status_code == 200
    assert client.get("/api/experiments/467", headers=auth_headers).status_code == 404
    assert client.get("/api/experiments/49", headers=auth_headers).json()["intensity"] == 200


def test_file_larger_than_5_mb_gives_413(client, auth_headers):
    response = upload(client, auth_headers, b"0" * (5 * 1024 * 1024 + 1))

    assert response.status_code == 413
