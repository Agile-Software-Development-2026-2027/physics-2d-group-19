"""Pre-job uploads: opaque content plus metadata published after the copy completes."""

import json
import os
import re
import shutil
import stat
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

_CHUNK_BYTES = 1024 * 1024


class UploadTooLarge(ValueError):
    """The bytes read from an upload exceeded the caller's limit."""


def save_upload(
    data_dir: Path,
    source: BinaryIO,
    filename: str,
    max_bytes: int | None = None,
) -> str:
    """Save from the current stream position without closing or seeking it.

    Content lives at uploads/<id>/content; the original filename is metadata only.
    None imposes no limit, zero allows empty uploads, and negative limits are invalid.
    On failure only this operation's directory is removed; the original error propagates.
    """
    if max_bytes is not None and max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")
    uploads = data_dir / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    while True:
        upload_id = uuid.uuid4().hex[:12]
        directory = uploads / upload_id
        try:
            directory.mkdir()
        except FileExistsError:
            continue
        break
    try:
        size_bytes = 0
        with (directory / "content").open("xb") as destination:
            while chunk := source.read(_CHUNK_BYTES):
                size_bytes += len(chunk)
                if max_bytes is not None and size_bytes > max_bytes:
                    raise UploadTooLarge(f"Upload exceeds {max_bytes} bytes")
                destination.write(chunk)
        metadata = {
            "filename": filename,
            "size_bytes": size_bytes,
            "created_at": datetime.now(UTC).isoformat(),
        }
        temporary = directory / "meta.json.tmp"
        temporary.write_text(json.dumps(metadata), encoding="utf-8")
        os.replace(temporary, directory / "meta.json")
    except Exception as exc:
        try:
            shutil.rmtree(directory)
        except OSError as cleanup_error:
            exc.add_note(f"Could not clean up upload {upload_id}: {cleanup_error}")
        raise
    return upload_id


def upload_path(data_dir: Path, upload_id: str) -> Path:
    """Resolve completed content; invalid/missing/incomplete uploads raise KeyError.

    Metadata is a completion marker, never a source of filesystem paths.
    Malformed JSON and I/O errors other than missing paths propagate unchanged.
    """
    if not isinstance(upload_id, str) or re.fullmatch(r"[0-9a-f]{12}", upload_id) is None:
        raise KeyError(upload_id)
    directory = data_dir / "uploads" / upload_id
    content = directory / "content"
    try:
        if not stat.S_ISREG(content.stat().st_mode):
            raise KeyError(upload_id)
        json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise KeyError(upload_id) from exc
    return content
