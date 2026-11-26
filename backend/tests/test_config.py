from pathlib import Path

import pytest

from app.config import Settings

LAB_VARS = ("APP_VIDEO_DIR", "APP_TRAJECTORIES_DIR", "APP_ILLUMINATION_DIR")


@pytest.fixture(autouse=True)
def _clear_lab_vars(monkeypatch):
    for name in LAB_VARS:
        monkeypatch.delenv(name, raising=False)


def test_lab_folders_default_to_none():
    settings = Settings(_env_file=None)

    assert settings.video_dir is None
    assert settings.trajectories_dir is None
    assert settings.illumination_dir is None


def test_lab_folders_read_from_app_variables(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_VIDEO_DIR", str(tmp_path / "videos"))
    monkeypatch.setenv("APP_TRAJECTORIES_DIR", str(tmp_path / "trajectories"))
    monkeypatch.setenv("APP_ILLUMINATION_DIR", str(tmp_path / "illumination"))

    settings = Settings(_env_file=None)

    assert settings.video_dir == tmp_path / "videos"
    assert settings.trajectories_dir == tmp_path / "trajectories"
    assert settings.illumination_dir == tmp_path / "illumination"
    assert isinstance(settings.video_dir, Path)
