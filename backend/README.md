# Backend

FastAPI (Python 3.12). Every endpoint is served under `/api`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000, API docs on /docs
pytest                          # tests
ruff check . && ruff format .   # lint and format
```

- `app/main.py`: builds the app, CORS, routers under `/api`.
- `app/config.py`: settings from `APP_*` environment variables (or `backend/.env`, never committed).
- `app/api/`: one file per group of endpoints.
- `tests/`: pytest tests; the `client` fixture gives a fresh app on a temporary data folder.

The frontend dev server (`frontend/`, port 5173) proxies `/api` to this backend on port 8000.
How to write tests and the team rules are in [`TESTING.md`](../TESTING.md).

## Users

Create the first user from `backend/` (the password is asked twice and never shown):

```bash
python -m app.users create operator
python -m app.users list
```

## Access tokens

`app.security` exports `create_access_token(username)` and `decode_access_token(token)`.
Tokens use HS256 with `sub` and UTC `exp` claims. Decoding returns the username;
invalid tokens raise `jwt.InvalidTokenError`, including `jwt.ExpiredSignatureError`.
The API authentication dependency is responsible for turning these errors into HTTP 401.

Set `APP_JWT_SECRET` through the environment or a local `.env` file before use;
the default `change-me` is only a local placeholder, not a deployment secret.
`APP_JWT_EXPIRE_MINUTES` defaults to 480. Tests may use a negative duration for expired tokens.

To configure a local secret, copy `.env.example` to `.env` and replace its placeholder
with a random value. Generate one from this directory with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Keep `.env` local; it is ignored by Git. The committed `.env.example` contains only a
placeholder, never a real signing secret.

## Pre-job upload storage (PHYSTUFF2D-130)

`app.services.uploads` saves opaque bytes independently of jobs:

```python
from io import BytesIO
from pathlib import Path

from app.services.uploads import UploadTooLarge, save_upload, upload_path

data_dir = Path("data")  # endpoints pass get_settings().data_dir
upload_id = save_upload(data_dir, BytesIO(b"example"), "video.avi", max_bytes=1024)
content = upload_path(data_dir, upload_id)  # Path to the saved file
assert content.read_bytes() == b"example"
```

The layout is `uploads/<12-lowercase-hex-id>/content` plus `meta.json`, for example
`{"filename": "video.avi", "size_bytes": 7, "created_at": "2026-11-09T12:00:00+00:00"}`.
The original filename is metadata only; physical content has a fixed name without a suffix.
Metadata is published atomically after content is closed and marks completion.

The service reads at most 1 MiB per call, from the current stream position, without
closing or rewinding it. It accepts empty streams and does not validate media formats.
`max_bytes=None` imposes no limit; equality is allowed, zero allows only empty streams,
and a negative limit raises `ValueError` before touching disk. Exceeding the limit raises
`UploadTooLarge` (a `ValueError`). Failed saves remove only their newly created directory;
I/O errors propagate. If cleanup itself fails, the original error retains a diagnostic note.

`upload_path` raises `KeyError` for invalid IDs, unknown uploads, missing content or missing
metadata. Malformed metadata JSON raises `json.JSONDecodeError`; other I/O errors propagate.
Readers never derive a path from metadata. Video/TIFF validation, configured size limits,
HTTP error mapping and canonical experiment/job copies belong to the consuming endpoints.

## Experiment illumination upload (PHYSTUFF2D-145, 16.3)

`POST /api/experiments/{exp_id}/illumination` requires a Bearer token and multipart field
`file`. `.tif`/`.tiff` extensions are case insensitive; bytes are not decoded or converted.
For experiment 49 (`ill=14`), success is `201 {"ill":14,"filename":"illumination14.tiff"}`.
Missing files/names or unsupported extensions return 422, empty files 400, unknown
experiments 404, and missing/invalid tokens 401. No illumination size limit is introduced.

The real pre-job storage service retains completed uploads and metadata. Its suffixless
`content` is copied in 1 MiB blocks to a unique temporary in
`APP_DATA_DIR/experiments/illumination`, then published with `os.replace`. Failed copies or
publication preserve the previous canonical file and remove the temporary; internal storage
errors return a generic 500. Concurrent successful uploads for the same `ill` share one file:
the last publication wins. Experiment settings are unchanged.

The canonical name always uses `ill`, including `illumination0.tiff` for zero. The current
core maps zero to `illumination1.tiff`; resolving that discrepancy belongs to job/core
integration, and zero is not yet usable end to end through the canonical file alone.
For 20.3, use this directory when the job has no illumination attached. For 16.4, call the
endpoint after saving the experiment and show the returned filename; the form is separate.

## Detection preview (PHYSTUFF2D-120, 10.1–10.2)

`app.services.preview` shows the cells found on one frame, before the full tracking:

- `detect_frame(video_path, frame, params)` reads only that frame and returns it with the
  positions found by `tp.locate`, using the same channel, background method, `diameter`,
  `minmass` and `invert` as the tracking. A frame outside the video raises `ValueError`.
- `render_png(frame, positions, diameter)` returns a PNG of the frame, with the same size,
  and a red circle of radius `diameter` around each cell.

The preview estimates the background on a sample of `BACKGROUND_SAMPLE_SIZE` frames
instead of the whole video, so its result can differ slightly from the full tracking.

