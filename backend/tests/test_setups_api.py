# Tests for setups endpoints and service

import pytest

from app.schemas.experiment import ExperimentSettings
from app.schemas.setup import SetupValues
from app.security import create_access_token


# Generates valid JWT bearer authorization headers for tests
@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


# Ensure SetupValues constraints stay identical to ExperimentSettings for the 8 fields
def test_setup_values_match_experiment_settings_constraints():
    setup_props = SetupValues.model_json_schema()["properties"]
    exp_props = ExperimentSettings.model_json_schema()["properties"]

    fields = ["ill", "intensity", "pix_arr", "exp_type", "ctr", "fluo", "lin", "axis"]
    for f in fields:
        assert f in setup_props, f"Field {f} missing in SetupValues"
        assert f in exp_props, f"Field {f} missing in ExperimentSettings"
        # Compare constraints
        assert setup_props[f] == exp_props[f], f"Mismatch on field {f}"


# The first GET call must automatically seed the 'Default' setup
def test_first_get_auto_creates_default_setup(client, auth_headers):
    resp = client.get("/api/setups", headers=auth_headers)
    assert resp.status_code == 200
    setups = resp.json()
    assert len(setups) == 1
    default = setups[0]
    assert default["name"] == "Default"
    assert default["is_default"] is True
    assert default["ill"] == 14
    assert default["intensity"] == 180
    assert default["pix_arr"] == 1.041667
    assert default["exp_type"] == 1
    assert len(default["id"]) == 12


# A new setup can be created via POST, and GET must return the default setup first
def test_create_and_list_setups_with_default_first(client, auth_headers):
    new_setup = {
        "name": "High intensity",
        "is_default": False,
        "ill": 20,
        "intensity": 250,
        "pix_arr": 1.0,
        "exp_type": 2,
        "ctr": 1,
        "fluo": 1,
        "lin": 0,
        "axis": 0,
    }
    resp = client.post("/api/setups", json=new_setup, headers=auth_headers)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "High intensity"
    assert created["intensity"] == 250

    list_resp = client.get("/api/setups", headers=auth_headers)
    assert list_resp.status_code == 200
    setups = list_resp.json()
    assert len(setups) == 2
    # The default setup must be listed first
    assert setups[0]["is_default"] is True
    assert setups[1]["name"] == "High intensity"


# Duplicate setup names (case-insensitive) must be rejected with HTTP 409
def test_duplicate_name_returns_409(client, auth_headers):
    payload = {
        "name": "default",  # Lowercase should still conflict with 'Default'
        "is_default": False,
        "ill": 14,
        "intensity": 180,
        "pix_arr": 1.0,
        "exp_type": 1,
        "ctr": 0,
        "fluo": 0,
        "lin": 0,
        "axis": 0,
    }
    resp = client.post("/api/setups", json=payload, headers=auth_headers)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


# Marking a new setup as default must remove default status from any previous setup
def test_setting_new_default_clears_previous_default(client, auth_headers):
    payload = {
        "name": "New default",
        "is_default": True,
        "ill": 15,
        "intensity": 200,
        "pix_arr": 1.0,
        "exp_type": 1,
        "ctr": 0,
        "fluo": 0,
        "lin": 0,
        "axis": 0,
    }
    resp = client.post("/api/setups", json=payload, headers=auth_headers)
    assert resp.status_code == 201

    list_resp = client.get("/api/setups", headers=auth_headers).json()
    assert len(list_resp) == 2
    # New default is listed first
    assert list_resp[0]["name"] == "New default"
    assert list_resp[0]["is_default"] is True
    assert list_resp[1]["name"] == "Default"
    assert list_resp[1]["is_default"] is False


# PUT updates values, rejects duplicate names with 409, and returns 404 for unknown IDs
def test_put_setup_updates_and_handles_404_and_409(client, auth_headers):
    # Create a secondary setup
    post_resp = client.post(
        "/api/setups",
        json={
            "name": "Secondary",
            "is_default": False,
            "ill": 14,
            "intensity": 100,
            "pix_arr": 1.0,
            "exp_type": 0,
            "ctr": 0,
            "fluo": 0,
            "lin": 0,
            "axis": 0,
        },
        headers=auth_headers,
    )
    setup_id = post_resp.json()["id"]

    # Successful update
    update_data = post_resp.json()
    update_data.pop("id", None)
    update_data["name"] = "Secondary updated"
    update_data["intensity"] = 120
    put_resp = client.put(f"/api/setups/{setup_id}", json=update_data, headers=auth_headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Secondary updated"
    assert put_resp.json()["intensity"] == 120

    # Duplicate name on update (conflicts with 'Default') -> 409
    update_data["name"] = "Default"
    dup_resp = client.put(f"/api/setups/{setup_id}", json=update_data, headers=auth_headers)
    assert dup_resp.status_code == 409

    # Non-existent setup -> 404
    missing_resp = client.put("/api/setups/0123456789ab", json=update_data, headers=auth_headers)
    assert missing_resp.status_code == 404


# Deleting the default setup promotes another setup, deleting the last setup returns 409
def test_delete_setup_promotes_remaining_and_cannot_delete_last(client, auth_headers):
    # Create second setup
    post_resp = client.post(
        "/api/setups",
        json={
            "name": "Second",
            "is_default": False,
            "ill": 14,
            "intensity": 100,
            "pix_arr": 1.0,
            "exp_type": 0,
            "ctr": 0,
            "fluo": 0,
            "lin": 0,
            "axis": 0,
        },
        headers=auth_headers,
    )
    second_id = post_resp.json()["id"]

    # Delete the original default setup
    initial_default_id = client.get("/api/setups", headers=auth_headers).json()[0]["id"]
    del_resp = client.delete(f"/api/setups/{initial_default_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # 'Second' setup must now be the default
    list_resp = client.get("/api/setups", headers=auth_headers).json()
    assert len(list_resp) == 1
    assert list_resp[0]["id"] == second_id
    assert list_resp[0]["is_default"] is True

    # Attempting to delete the last remaining setup must return 409
    del_last = client.delete(f"/api/setups/{second_id}", headers=auth_headers)
    assert del_last.status_code == 409


# Invalid parameter values (e.g. pix_arr <= 0) must be rejected with HTTP 422
def test_validation_errors_return_422(client, auth_headers):
    payload = {
        "name": "Invalid",
        "is_default": False,
        "ill": 14,
        "intensity": 180,
        "pix_arr": 0.0,
        "exp_type": 1,
        "ctr": 0,
        "fluo": 0,
        "lin": 0,
        "axis": 0,
    }
    resp = client.post("/api/setups", json=payload, headers=auth_headers)
    assert resp.status_code == 422


# Unauthenticated requests must return HTTP 401 Unauthorized
def test_unauthenticated_request_returns_401(client):
    resp = client.get("/api/setups")
    assert resp.status_code == 401
