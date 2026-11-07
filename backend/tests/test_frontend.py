from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import FRONTEND_DIST, create_app

INDEX = "<!doctype html><title>Temporary SPA</title>"


@pytest.fixture
def spa(client, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(INDEX)
    (dist / "assets").mkdir()
    (dist / "assets/app.js").write_text("console.log('build');")
    (dist / "assets/app.css").write_text("body { color: green; }")
    (dist / "api").mkdir()
    (dist / "api/nonexistent").write_text("must not be served")
    outside = tmp_path / "outside"
    outside.write_text("private content")
    (dist / "escape").symlink_to(outside)
    with TestClient(create_app(frontend_dist=dist)) as c:
        yield c


@pytest.mark.parametrize("path", ["/", "/login", "/elaborazione", "/risultati/abc123"])
def test_spa_navigation_and_head(spa, path):
    response = spa.get(path)
    assert response.status_code == 200
    assert response.text == INDEX
    assert response.headers["content-type"].startswith("text/html")
    head = spa.head(path)
    assert head.status_code == 200
    assert head.content == b""
    assert head.headers["content-length"] == response.headers["content-length"]


@pytest.mark.parametrize(
    "name, mime, content",
    [
        ("app.js", "javascript", "console.log('build');"),
        ("app.css", "text/css", "body { color: green; }"),
    ],
)
def test_existing_assets(spa, name, mime, content):
    response = spa.get(f"/assets/{name}")
    assert response.status_code == 200
    assert mime in response.headers["content-type"]
    assert response.text == content


@pytest.mark.parametrize(
    "path",
    [
        "/assets/missing.js",
        "/assets/missing",
        "/missing.css",
        "/escape",
        "/%2e%2e/outside",
        "/assets/%2e%2e/%2e%2e/outside",
        "/..%5coutside",
        "/api",
        "/api/",
        "/api/nonexistent",
    ],
)
def test_missing_assets_api_and_unsafe_paths_return_404(spa, path):
    response = spa.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_writes_do_not_fall_back(spa, method):
    response = spa.request(method, "/elaborazione")
    assert response.status_code == 405
    assert INDEX not in response.text


def test_api_and_documentation_keep_precedence(spa):
    assert spa.get("/api/health").json() == {"status": "ok"}
    assert spa.get("/api/auth/me").status_code == 401
    login = spa.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
    assert login.status_code == 401
    assert login.json()["detail"] == "Username or password incorrect"
    for path in ["/docs", "/redoc", "/openapi.json"]:
        response = spa.get(path)
        assert response.status_code == 200
        assert response.text != INDEX
    assert spa.get("/openapi.json").json()["info"]["title"] == "Moving Chlamydomonas API"


@pytest.mark.parametrize("build", ["absent", "incomplete", "external-index"])
def test_unavailable_build_keeps_api_usable(client, tmp_path, build):
    dist = tmp_path / "unavailable"
    if build != "absent":
        dist.mkdir()
        (dist / "app.js").write_text("not a complete build")
    if build == "external-index":
        outside = tmp_path / "outside.html"
        outside.write_text("private content")
        (dist / "index.html").symlink_to(outside)
    with TestClient(create_app(frontend_dist=dist)) as c:
        assert c.get("/api/health").json() == {"status": "ok"}
        assert c.get("/").status_code == 404
        assert c.get("/api/nonexistent").status_code == 404


def test_default_build_path_is_independent_of_cwd(client, monkeypatch, tmp_path):
    import app.main as main

    assert FRONTEND_DIST == Path(main.__file__).resolve().parents[2] / "frontend/dist"
    dist = tmp_path / "build"
    dist.mkdir()
    (dist / "index.html").write_text(INDEX)
    monkeypatch.setattr(main, "FRONTEND_DIST", dist)
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app()) as c:
        assert c.get("/elaborazione").text == INDEX
