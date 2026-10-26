# Testing

How we write and run tests in this project. Read this before your first pull request.

## How CI runs the tests

`.github/workflows/ci.yml` runs on every pull request and on every push to `main`:

| Job | What it runs (in this order) |
|---|---|
| `backend` | `ruff check .`, `ruff format --check .`, `pytest --cov=app --cov-fail-under=60` |
| `frontend` | `npm run lint`, `npm test`, `npm run build` |
| `test` | Passes only if `backend` and `frontend` passed. It is the required check on `main`. |

You never list your tests in the YAML. `pytest` and `vitest` find every file that follows the
naming rules below, so a new test file runs in CI as soon as you push it.

Change the YAML only to add a new kind of check (a new job or a new step). When you add a job,
add it to the `needs` list of `test`, otherwise it does not block the merge. Do not rename `test`.

## Run the tests locally

Run them before you push: CI runs exactly the same commands.

```bash
cd backend
pytest                       # all tests
pytest tests/test_health.py  # one file
pytest -k diameter           # only tests whose name contains "diameter"
pytest --cov=app             # with coverage
ruff check . && ruff format .

cd frontend
npm test                     # all tests once
npm run test:watch           # rerun on every save
npm run lint
```

## Backend tests (pytest)

- Put them in `backend/tests/`, one file per module: `test_<module>.py`
  (code in `app/services/config_store.py` → tests in `tests/test_config_store.py`).
- Every test is a function whose name starts with `test_` and describes the behaviour:
  `test_even_diameter_is_rejected`, not `test_params_2`.
- Shared fixtures go in `tests/conftest.py`. The `client` fixture gives you a `TestClient` on a
  fresh app whose data directory is a temporary folder, so tests never touch real data.

Example: an API test (see `tests/test_health.py`).

```python
def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Example: a unit test with several inputs and an expected error.

```python
import pytest
from pydantic import ValidationError

from app.schemas.params import TrackingParams


@pytest.mark.parametrize("diameter", [0, 4, -3])
def test_invalid_diameter_is_rejected(diameter):
    with pytest.raises(ValidationError):
        TrackingParams(diameter=diameter)
```

For physics functions, build a small synthetic input whose result you can compute by hand (a
straight trajectory, a uniform rotation) and compare floats with `pytest.approx` or
`numpy.testing.assert_allclose`, never with `==`.

## Frontend tests (Vitest + Testing Library)

- Put the test next to the file it tests: `ParamsForm.jsx` → `ParamsForm.test.jsx`.
- Import `describe`, `it`, `expect` and `vi` from `vitest` (there are no globals).
- Test what the user sees and does: find elements by text, label or role
  (`screen.getByRole('button', { name: 'Run' })`), not by CSS class.
- Never call the real backend: replace `fetch` with `vi.stubGlobal('fetch', ...)` and restore it
  with `vi.unstubAllGlobals()` (see `src/App.test.jsx`).
- Simulate clicks and typing with `@testing-library/user-event`.

Example (see `src/App.test.jsx`).

```jsx
it('shows the backend status when the health check succeeds', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ status: 'ok' }),
  }))
  render(<App />)
  expect(await screen.findByText('Backend: ok')).toBeInTheDocument()
})
```

## Team rules

1. A pull request that adds or changes code adds or changes its tests in the same pull request.
2. A bug fix starts with a test that fails because of the bug.
3. Coverage of the backend must not go below the threshold in `ci.yml` (60% now, 75% by the end
   of Sprint 1). Raise the threshold when coverage goes up, never lower it.
4. Tests are fast and independent: no real videos, no network, no files outside `tmp_path`,
   no order between tests. Use small fixtures in `backend/tests/fixtures/`.
5. A test that needs the full sample videos is marked `@pytest.mark.slow` and skipped when the
   files are missing. It never runs on pull requests.
6. Do not skip or delete a failing test to make CI green: fix the code or discuss it in the PR.
7. `legacy-code/` has no tests and is not linted: it is only the reference for the regression
   tests.

## Tests to write in Sprint 1

Use this list to split the work. Tick a line when its tests are merged.

**Dependencies and CI**
- [ ] A pull request with a failing test cannot be merged (check it once by hand on a test PR).

**Single video pipeline (tracking + analysis)**
- [ ] Tracking parameters: `diameter` odd and > 0; `minmass` and `search_range` > 0; background
      method only `mean` or `median`; `memory` empty or ≥ 0.
- [ ] Background subtraction (`mean`, `median`, unknown method) on small synthetic frames.
- [ ] Short trajectories are removed (`filter_stubs`); the output has the columns
      `frame, y, x, particle`.
- [ ] Physics functions on synthetic data: theta and angle of a straight trajectory, omega of a
      uniform rotation, flux through the disc, tumbling threshold, N(t), empty input.
- [ ] Regression: on a short lossless clip of video 49 the new pipeline gives the same numbers as
      `legacy-code/` (`pandas.testing.assert_frame_equal`, `rtol=1e-9`). The expected results are
      produced once by running the legacy code and committed as fixtures.

**Parameters and history**
- [ ] Analysis defaults: `scradius` between 120 and 150 (not 350), circle thickness 0, the zero
      values that crashed the legacy app are rejected.
- [ ] A config saved to JSON (or YAML) and loaded back is identical; unknown fields are rejected.
- [ ] History: every save gets a unique ID and timestamp, the list is sorted by time, loading an
      ID returns the same config, an unknown ID gives 404, IDs containing `../` are rejected.
- [ ] API: upload accepts only `.avi`; a job goes `queued → running → done` or `failed`
      (with the pipeline replaced by a fake one).

**User interface**
- [ ] The parameters form shows the correct defaults.
- [ ] With an even `diameter` the form shows an error and the Run button is disabled.
- [ ] Upload accepts only `.avi` files and shows the file name.
- [ ] While a job runs the Run button is disabled; when it ends the page shows "completed" or the
      error.
- [ ] A config from the history can be loaded back into the form.

## Later

Smoke test with `docker compose`, end-to-end tests with Playwright, dependency audits
(`pip-audit`, `npm audit`), CodeQL, Docker images and releases. Each one will be added to
`ci.yml` as its own job when we need it.
