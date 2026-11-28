from pathlib import Path

import pytest

from app.config import Settings, get_settings
from app.schemas.experiment import ExperimentSettings
from app.services.file_resolver import ResolvedFiles, resolve_files

EXP_49 = ExperimentSettings(exps=49, exp_type=1, ill=14, intensity=180, pix_arr=1.041667)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    """Lab folders in tmp_path, configured through the APP_ variables."""
    folders = {name: tmp_path / name for name in ("videos", "traj", "illum")}
    for folder in folders.values():
        folder.mkdir()
    monkeypatch.setenv("APP_VIDEO_DIR", str(folders["videos"]))
    monkeypatch.setenv("APP_TRAJECTORIES_DIR", str(folders["traj"]))
    monkeypatch.setenv("APP_ILLUMINATION_DIR", str(folders["illum"]))
    get_settings.cache_clear()
    yield folders
    get_settings.cache_clear()


def _touch(path: Path) -> Path:
    path.write_bytes(b"x")
    return path


def test_all_files_found(lab, tmp_path):
    video = _touch(lab["videos"] / "tAlgae49.avi")
    traj = _touch(lab["traj"] / "tAlgae49.txt")
    illum = _touch(lab["illum"] / "illumination14.tiff")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found == ResolvedFiles(
        video=video.resolve(), trajectories=traj.resolve(), illumination=illum.resolve()
    )


def test_missing_files_are_none(lab, tmp_path):
    _touch(lab["videos"] / "tAlgae50.avi")  # another experiment

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found == ResolvedFiles(video=None, trajectories=None, illumination=None)


def test_tif_extension(lab, tmp_path):
    illum = _touch(lab["illum"] / "illumination14.tif")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.illumination == illum.resolve()


def test_tiff_preferred_over_tif(lab, tmp_path):
    tiff = _touch(lab["illum"] / "illumination14.tiff")
    _touch(lab["illum"] / "illumination14.tif")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.illumination == tiff.resolve()


def test_tphot_prefix(lab, tmp_path):
    video = _touch(lab["videos"] / "tPhot49.avi")
    traj = _touch(lab["traj"] / "tPhot49.txt")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.video == video.resolve()
    assert found.trajectories == traj.resolve()


def test_talgae_preferred_over_other_prefixes(lab, tmp_path):
    talgae = _touch(lab["videos"] / "tAlgae49.avi")
    _touch(lab["videos"] / "tPhot49.avi")
    _touch(lab["videos"] / "td49.avi")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.video == talgae.resolve()


def test_folders_not_configured(tmp_path, monkeypatch):
    for name in ("APP_VIDEO_DIR", "APP_TRAJECTORIES_DIR", "APP_ILLUMINATION_DIR"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)

    found = resolve_files(settings, tmp_path / "data", EXP_49)

    assert found == ResolvedFiles(video=None, trajectories=None, illumination=None)


def test_configured_folder_that_does_not_exist(tmp_path):
    settings = Settings(_env_file=None, video_dir=tmp_path / "missing")

    assert resolve_files(settings, tmp_path, EXP_49).video is None


def test_illumination_falls_back_to_uploaded_images(lab, tmp_path):
    uploaded_dir = tmp_path / "data" / "experiments" / "illumination"
    uploaded_dir.mkdir(parents=True)
    uploaded = _touch(uploaded_dir / "illumination14.tiff")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.illumination == uploaded.resolve()


def test_lab_illumination_preferred_over_uploaded(lab, tmp_path):
    lab_file = _touch(lab["illum"] / "illumination14.tiff")
    uploaded_dir = tmp_path / "data" / "experiments" / "illumination"
    uploaded_dir.mkdir(parents=True)
    _touch(uploaded_dir / "illumination14.tiff")

    found = resolve_files(get_settings(), tmp_path / "data", EXP_49)

    assert found.illumination == lab_file.resolve()


def test_directory_with_the_expected_name_is_ignored(lab, tmp_path):
    (lab["videos"] / "tAlgae49.avi").mkdir()

    assert resolve_files(get_settings(), tmp_path, EXP_49).video is None


def test_symlink_outside_the_folder_is_ignored(lab, tmp_path):
    outside = _touch(tmp_path / "secret.avi")
    try:
        (lab["videos"] / "tAlgae49.avi").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks need extra privileges on Windows")

    assert resolve_files(get_settings(), tmp_path, EXP_49).video is None
