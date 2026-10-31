import json
import re
from uuid import UUID

import pytest

from app.services import jobs_store as store


def test_create_job_has_isolated_folders_and_initial_status(tmp_path):
    job_id = store.create_job(tmp_path, 49)
    directory = store.job_dir(tmp_path, job_id)
    assert re.fullmatch(r"[0-9a-f]{12}", job_id)
    assert directory == tmp_path / "jobs" / job_id
    assert {p.name for p in directory.iterdir()} == {
        "input",
        "tracking",
        "results",
        "plots",
        "status.json",
    }
    assert all((directory / name).is_dir() for name in ("input", "tracking", "results", "plots"))
    assert store.read_status(tmp_path, job_id) == {
        "job_id": job_id,
        "exp_id": 49,
        "status": "queued",
        "error": None,
    }
    other = store.create_job(tmp_path, 700)
    assert other != job_id
    assert store.read_status(tmp_path, other)["exp_id"] == 700


def test_updates_preserve_metadata_and_clear_error(tmp_path):
    job_id = store.create_job(tmp_path, 49)
    for status in ("queued", "tracking", "analysis", "plots", "done", "error"):
        store.write_status(
            tmp_path, job_id, status, error="failed", progress=1, plots={"flux": None}
        )
        assert store.read_status(tmp_path, job_id)["status"] == status
        assert store.read_status(tmp_path, job_id)["error"] == "failed"
    store.write_status(tmp_path, job_id, "done", progress=2)
    expected = {
        "job_id": job_id,
        "exp_id": 49,
        "status": "done",
        "error": None,
        "progress": 2,
        "plots": {"flux": None},
    }
    assert store.read_status(tmp_path, job_id) == expected
    assert json.loads((store.job_dir(tmp_path, job_id) / "status.json").read_bytes()) == expected
    with pytest.raises(ValueError):
        store.write_status(tmp_path, job_id, "done", exp_id=50)
    assert store.read_status(tmp_path, job_id) == expected


@pytest.mark.parametrize(
    "job_id",
    [
        "",
        "abc",
        "a" * 13,
        "A" * 12,
        "g" * 12,
        "../abcdefghi",
        "/etc/passwd",
        "a" * 12 + "\n",
        "a1b2c3d4e5f6",
        None,
        123,
    ],
)
def test_invalid_or_unknown_job(tmp_path, job_id):
    for operation in (store.job_dir, store.read_status):
        with pytest.raises(KeyError):
            operation(tmp_path, job_id)
    with pytest.raises(KeyError):
        store.write_status(tmp_path, job_id, "done")
    assert not (tmp_path / "jobs").exists()


def test_missing_and_corrupt_status_are_distinct(tmp_path):
    job_id = store.create_job(tmp_path, 49)
    status = store.job_dir(tmp_path, job_id) / "status.json"
    status.unlink()
    with pytest.raises(KeyError):
        store.read_status(tmp_path, job_id)
    status.write_text("broken json")
    with pytest.raises(json.JSONDecodeError):
        store.read_status(tmp_path, job_id)


def test_file_is_not_a_job_directory(tmp_path):
    (tmp_path / "jobs").mkdir()
    (tmp_path / "jobs" / ("a" * 12)).touch()
    with pytest.raises(KeyError):
        store.job_dir(tmp_path, "a" * 12)


def test_id_collision_does_not_overwrite_existing_job(tmp_path, monkeypatch):
    ids = iter([UUID(int=0), UUID(int=0), UUID(hex="1" * 32)])
    monkeypatch.setattr(store.uuid, "uuid4", lambda: next(ids))
    first = store.create_job(tmp_path, 49)
    second = store.create_job(tmp_path, 700)
    assert first != second
    assert store.read_status(tmp_path, first)["exp_id"] == 49
    assert store.read_status(tmp_path, second)["exp_id"] == 700


def test_status_is_published_only_after_temp_file_is_complete(tmp_path, monkeypatch):
    replace = store.os.replace
    seen = []

    def inspect_replace(source, target):
        assert source == target.with_name("status.json.tmp")
        seen.append(json.loads(source.read_bytes())["status"])
        if target.exists():
            assert json.loads(target.read_bytes())["status"] == "queued"
        replace(source, target)

    monkeypatch.setattr(store.os, "replace", inspect_replace)
    job_id = store.create_job(tmp_path, 49)
    store.write_status(tmp_path, job_id, "done")
    assert seen == ["queued", "done"]
    assert not (store.job_dir(tmp_path, job_id) / "status.json.tmp").exists()


def test_failed_replace_preserves_published_status(tmp_path, monkeypatch):
    job_id = store.create_job(tmp_path, 49)
    original = store.read_status(tmp_path, job_id)

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(store.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        store.write_status(tmp_path, job_id, "done")
    assert store.read_status(tmp_path, job_id) == original


def test_non_serializable_extra_does_not_touch_status_files(tmp_path):
    job_id = store.create_job(tmp_path, 49)
    directory = store.job_dir(tmp_path, job_id)
    original = (directory / "status.json").read_bytes()
    with pytest.raises(TypeError):
        store.write_status(tmp_path, job_id, "done", plots={object()})
    assert (directory / "status.json").read_bytes() == original
    assert not (directory / "status.json.tmp").exists()
