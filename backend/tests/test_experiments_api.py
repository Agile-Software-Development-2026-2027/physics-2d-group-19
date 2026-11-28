import pytest

from app.config import get_settings
from app.security import create_access_token
from app.services.experiments_store import settings_path


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


def test_get_experiment_49(client, auth_headers):
    response = client.get("/api/experiments/49", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["exps"] == 49


def test_put_49_keeps_file_identical(client, auth_headers):
    body = client.get("/api/experiments/49", headers=auth_headers).json()
    path = settings_path(get_settings().data_dir)
    before = path.read_bytes()

    response = client.put("/api/experiments/49", json=body, headers=auth_headers)

    assert response.status_code == 200
    assert path.read_bytes() == before


def test_put_new_experiment_is_listed(client, auth_headers):
    body = client.get("/api/experiments/49", headers=auth_headers).json()
    body["exps"] = 400

    response = client.put("/api/experiments/400", json=body, headers=auth_headers)
    assert response.status_code == 200

    listed = client.get("/api/experiments", headers=auth_headers).json()
    numbers = []
    for experiment in listed:
        numbers.append(experiment["exps"])
    assert 400 in numbers


def test_put_invalid_value_gives_422(client, auth_headers):
    body = client.get("/api/experiments/49", headers=auth_headers).json()
    body["ill"] = "abc"

    response = client.put("/api/experiments/49", json=body, headers=auth_headers)

    assert response.status_code == 422
    assert "ill" in response.json()["detail"][0]["loc"]


# the values of experiment 49, without its number, to use in a batch request
def batch_body(client, auth_headers, exp_ids):
    body = client.get("/api/experiments/49", headers=auth_headers).json()
    del body["exps"]
    body["exp_ids"] = exp_ids
    return body


def test_batch_creates_466_to_470(client, auth_headers):
    body = batch_body(client, auth_headers, [466, 467, 468, 469, 470])

    response = client.post("/api/experiments/batch", json=body, headers=auth_headers)

    assert response.status_code == 201
    assert response.json() == {"created": [466, 467, 468, 469, 470]}
    for exp_id in [466, 467, 468, 469, 470]:
        experiment = client.get(f"/api/experiments/{exp_id}", headers=auth_headers).json()
        assert experiment["ill"] == 14


def test_batch_with_existing_number_writes_nothing(client, auth_headers):
    body = batch_body(client, auth_headers, [48, 49, 50, 500])
    path = settings_path(get_settings().data_dir)
    before = path.read_bytes()

    response = client.post("/api/experiments/batch", json=body, headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["existing"] == [49, 50]
    assert path.read_bytes() == before


def test_batch_empty_list_gives_422(client, auth_headers):
    body = batch_body(client, auth_headers, [])

    response = client.post("/api/experiments/batch", json=body, headers=auth_headers)

    assert response.status_code == 422


def test_batch_101_numbers_gives_422(client, auth_headers):
    body = batch_body(client, auth_headers, list(range(1000, 1101)))

    response = client.post("/api/experiments/batch", json=body, headers=auth_headers)

    assert response.status_code == 422


def test_batch_same_number_twice_gives_422(client, auth_headers):
    body = batch_body(client, auth_headers, [466, 466])

    response = client.post("/api/experiments/batch", json=body, headers=auth_headers)

    assert response.status_code == 422
