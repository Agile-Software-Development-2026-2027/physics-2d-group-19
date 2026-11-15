import io
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from app.services import uploads as store

CHUNK_BYTES = 1024 * 1024


@pytest.mark.parametrize(
    "filename", ["video.avi", "../meta.json", "/tmp/escape", "meta.json", r"C:\x"]
)
def test_round_trip_and_metadata_keep_filename_separate(tmp_path, filename):
    before = datetime.now(UTC)
    source = io.BytesIO(b"skip\x00\xffpayload")
    source.read(4)
    upload_id = store.save_upload(tmp_path, source, filename)
    path = store.upload_path(tmp_path, upload_id)
    assert re.fullmatch(r"[0-9a-f]{12}", upload_id)
    assert path == tmp_path / "uploads" / upload_id / "content"
    assert path.read_bytes() == b"\x00\xffpayload"
    metadata = json.loads((path.parent / "meta.json").read_text())
    created = datetime.fromisoformat(metadata.pop("created_at"))
    assert created.utcoffset().total_seconds() == 0
    assert before <= created <= datetime.now(UTC)
    assert metadata == {"filename": filename, "size_bytes": 9}
    assert {p.name for p in path.parent.iterdir()} == {"content", "meta.json"}
    assert {p.name for p in tmp_path.iterdir()} == {"uploads"}
    assert not source.closed
    assert source.read(1) == b""


def test_same_filename_and_id_collision_preserve_existing_upload(tmp_path, monkeypatch):
    ids = iter([UUID(int=0), UUID(int=0), UUID(hex="1" * 32)])
    monkeypatch.setattr(store.uuid, "uuid4", lambda: next(ids))
    first = store.save_upload(tmp_path, io.BytesIO(b"first"), "same.avi")
    first_metadata = (store.upload_path(tmp_path, first).parent / "meta.json").read_bytes()
    second = store.save_upload(tmp_path, io.BytesIO(b"second"), "same.avi")
    assert first != second
    assert store.upload_path(tmp_path, first).read_bytes() == b"first"
    assert store.upload_path(tmp_path, second).read_bytes() == b"second"
    assert (store.upload_path(tmp_path, first).parent / "meta.json").read_bytes() == first_metadata


class NonSeekableStream:
    def __init__(self, content):
        self.source = io.BytesIO(content)
        self.read_sizes = []

    def read(self, size):
        assert size == CHUNK_BYTES
        self.read_sizes.append(size)
        return self.source.read(size)


def test_non_seekable_stream_is_copied_in_bounded_blocks(tmp_path):
    content = b"x" * (2 * CHUNK_BYTES + 17)
    source = NonSeekableStream(content)
    upload_id = store.save_upload(tmp_path, source, "anything")
    assert store.upload_path(tmp_path, upload_id).read_bytes() == content
    assert len(source.read_sizes) == 4
    assert not source.source.closed


def test_short_reads_do_not_end_the_copy(tmp_path):
    class ShortReads(NonSeekableStream):
        def read(self, size):
            assert size == CHUNK_BYTES
            return self.source.read(2)

    source = ShortReads(b"abcdefg")
    upload_id = store.save_upload(tmp_path, source, "input")
    assert store.upload_path(tmp_path, upload_id).read_bytes() == b"abcdefg"


@pytest.mark.parametrize(
    ("content", "limit", "too_large"),
    [
        (b"abc", None, False),
        (b"abc", 4, False),
        (b"abc", 3, False),
        (b"abc", 2, True),
        (b"", 0, False),
        (b"x", 0, True),
        (b"", None, False),
    ],
)
def test_limits_and_empty_uploads(tmp_path, content, limit, too_large):
    source = io.BytesIO(content)
    if too_large:
        with pytest.raises(store.UploadTooLarge):
            store.save_upload(tmp_path, source, "input", limit)
        assert list((tmp_path / "uploads").iterdir()) == []
    else:
        upload_id = store.save_upload(tmp_path, source, "input", limit)
        assert store.upload_path(tmp_path, upload_id).read_bytes() == content
    assert not source.closed


def test_negative_limit_does_not_touch_disk_or_stream(tmp_path):
    source = io.BytesIO(b"abc")
    with pytest.raises(ValueError, match="non-negative"):
        store.save_upload(tmp_path, source, "input", -1)
    assert list(tmp_path.iterdir()) == []
    assert source.tell() == 0
    assert not source.closed


@pytest.mark.parametrize("failure", ["limit", "read", "write", "metadata", "publish"])
def test_failures_remove_only_new_upload_and_propagate_error(tmp_path, monkeypatch, failure):
    previous = store.save_upload(tmp_path, io.BytesIO(b"keep"), "previous")
    original_files = {p.name: p.read_bytes() for p in (tmp_path / "uploads" / previous).iterdir()}
    source = NonSeekableStream(b"x" * (2 * CHUNK_BYTES + 1))
    error = OSError(f"simulated {failure}")

    def fail(*args, **kwargs):
        raise error

    if failure == "read":
        read = source.read

        def broken_read(size):
            if source.read_sizes:
                raise error
            return read(size)

        monkeypatch.setattr(source, "read", broken_read)
    elif failure == "write":
        original_open = Path.open

        class BrokenDestination(io.BytesIO):
            def write(self, chunk):
                raise error

        def broken_open(path, *args, **kwargs):
            if path.name == "content" and args == ("xb",):
                path.touch()
                return BrokenDestination()
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", broken_open)
    elif failure == "metadata":
        write_text = Path.write_text

        def partial_metadata(path, *args, **kwargs):
            write_text(path, "{", encoding="utf-8")
            raise error

        monkeypatch.setattr(Path, "write_text", partial_metadata)
    elif failure == "publish":
        monkeypatch.setattr(store.os, "replace", fail)
    with pytest.raises(store.UploadTooLarge if failure == "limit" else OSError) as caught:
        store.save_upload(
            tmp_path, source, "input", 2 * CHUNK_BYTES if failure == "limit" else None
        )
    if failure != "limit":
        assert caught.value is error
    assert {p.name for p in (tmp_path / "uploads").iterdir()} == {previous}
    assert {
        p.name: p.read_bytes() for p in (tmp_path / "uploads" / previous).iterdir()
    } == original_files
    assert not source.source.closed


def test_cleanup_failure_keeps_the_original_error(tmp_path, monkeypatch):
    error = OSError("read failed")

    def broken_read(size):
        raise error

    def denied(directory):
        raise PermissionError("cleanup denied")

    source = io.BytesIO(b"abc")
    monkeypatch.setattr(source, "read", broken_read)
    monkeypatch.setattr(store.shutil, "rmtree", denied)
    with pytest.raises(OSError, match="read failed") as caught:
        store.save_upload(tmp_path, source, "input")
    assert caught.value is error
    assert "cleanup denied" in error.__notes__[0]
    assert not source.closed


@pytest.mark.parametrize(
    "upload_id",
    [
        "a" * 12,
        "",
        "a" * 11,
        "a" * 13,
        "A" * 12,
        "g" * 12,
        "a" * 12 + "\n",
        "../x",
        "/etc/passwd",
        None,
        123,
    ],
)
def test_invalid_or_unknown_id_does_not_create_files(tmp_path, upload_id):
    with pytest.raises(KeyError):
        store.upload_path(tmp_path, upload_id)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("missing", ["content", "meta.json"])
def test_missing_content_or_completion_marker(tmp_path, missing):
    upload_id = store.save_upload(tmp_path, io.BytesIO(b"abc"), "input")
    (tmp_path / "uploads" / upload_id / missing).unlink()
    with pytest.raises(KeyError):
        store.upload_path(tmp_path, upload_id)


def test_corrupt_metadata_and_io_errors_are_not_missing_uploads(tmp_path, monkeypatch):
    upload_id = store.save_upload(tmp_path, io.BytesIO(b"abc"), "input")
    (tmp_path / "uploads" / upload_id / "meta.json").write_text("broken json")
    with pytest.raises(json.JSONDecodeError):
        store.upload_path(tmp_path, upload_id)

    def denied(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "read_text", denied)
    with pytest.raises(PermissionError, match="denied"):
        store.upload_path(tmp_path, upload_id)


def test_completion_marker_is_published_after_content(tmp_path, monkeypatch):
    replace = store.os.replace

    def inspect_replace(source, target):
        upload_id = target.parent.name
        assert (target.parent / "content").read_bytes() == b"complete"
        assert json.loads(source.read_bytes())["size_bytes"] == 8
        with pytest.raises(KeyError):
            store.upload_path(tmp_path, upload_id)
        replace(source, target)

    monkeypatch.setattr(store.os, "replace", inspect_replace)
    upload_id = store.save_upload(tmp_path, io.BytesIO(b"complete"), "input")
    assert store.upload_path(tmp_path, upload_id).read_bytes() == b"complete"


@pytest.mark.parametrize("file_as_id", [True, False])
def test_file_as_upload_directory_or_directory_as_content_is_missing(tmp_path, file_as_id):
    directory = tmp_path / "uploads" / ("a" * 12)
    directory.parent.mkdir()
    if file_as_id:
        directory.touch()
    else:
        (directory / "content").mkdir(parents=True)
    with pytest.raises(KeyError):
        store.upload_path(tmp_path, "a" * 12)
