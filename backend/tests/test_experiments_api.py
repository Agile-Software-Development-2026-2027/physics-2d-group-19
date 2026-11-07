from app.config import get_settings
from app.services.experiments_store import settings_path


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