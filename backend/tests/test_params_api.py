# Integration tests for the default parameters API endpoint

import pytest

from app.security import create_access_token


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


def test_get_defaults_without_token_returns_401(client):
    response = client.get("/api/params/defaults")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_defaults_with_invalid_token_returns_401(client):
    response = client.get("/api/params/defaults", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_defaults_with_token_returns_lab_defaults(client, auth_headers):
    response = client.get("/api/params/defaults", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    # Structure checks
    assert "tracking" in data
    assert "analysis" in data
    assert "filters" in data
    assert "limits" in data

    # Default values checks
    assert data["tracking"]["diameter"] == 5
    assert data["tracking"]["minmass"] == 180
    assert data["tracking"]["background_method"] == "mean"
    assert data["analysis"]["disc_radius"] == 350
    assert data["analysis"]["radial_map"] is False
    assert data["analysis"]["tumbling_threshold"] == 5.0

    # Limits checks
    limits = data["limits"]
    assert limits["tracking"]["diameter"]["minimum"] == 3
    assert limits["tracking"]["memory"]["minimum"] == 0  # Extracted from anyOf
    assert "description" in limits["tracking"]["diameter"]
    assert limits["analysis"]["dt"]["exclusiveMinimum"] == 0
    assert limits["analysis"]["disc_radius"]["minimum"] == 0
    assert limits["filters"]["dist_step"]["minimum"] == 1
