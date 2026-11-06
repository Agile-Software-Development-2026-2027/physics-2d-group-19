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

## Built frontend (single port)

Run `npm ci` and `npm run build` from `frontend/`, then start the backend normally.
Open http://localhost:8000. Keep `VITE_API_BASE_URL` unset or empty when building for
the same origin, and `VITE_USE_MSW` disabled for real API calls.

The backend looks for `frontend/dist` relative to the repository, independently of
the working directory. It mounts the build after the API routes only when
`index.html` is a file inside that directory. Missing or incomplete builds leave
the API available and frontend URLs return 404. Build before starting the server;
restart it after creating a previously missing build (handoff for task 22.2).

Existing files are served by `StaticFiles`. GET/HEAD requests to extensionless
paths (for example `/elaborazione` or `/risultati/<job_id>`) fall back to the index.
Missing paths containing a dotted segment or under `/assets` return 404. `/api`
and `/api/...` never fall back, and other HTTP methods never return the SPA index.
API authentication, `/docs`, `/redoc` and `/openapi.json` retain their behavior.
Tests can pass a temporary build using `create_app(frontend_dist=path)`.

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
