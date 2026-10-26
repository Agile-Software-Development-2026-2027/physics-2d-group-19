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
