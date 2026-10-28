# Calculation core (`backend/core`)

This package contains the core scientific algorithms for cell tracking, physical analysis, and figure plotting migrated from the laboratory's legacy repository.

The physical equations and algorithms remain frozen and identical to the laboratory reference. Only package import paths have been updated to turn the legacy codebase into a standard Python package.

---

## 1. Core structure

### Copied modules (byte-for-byte origin)

| Destination path in `backend/core/` | Source path in legacy repository | Scope / Purpose |
| :--- | :--- | :--- |
| `clamutils_exp.py` | `clamutils_exp.py` | Core classes: `particle_class`, `Speckle`, `Filters` |
| `tracking_core.py` | `tracking_from_video/src/tracking_core.py` | Particle detection and tracking with `trackpy` |
| `clam_pipeline/analyze.py` | `clam_pipeline/analyze.py` | `analyze_experiment` pipeline and data structures |
| `clam_pipeline/io.py` | `clam_pipeline/io.py` | Experimental settings parser and legacy loaders |
| `analyses/common.py` | `analyses/common.py` | Shared plotting constants, styles, and binning helpers |
| `analyses/load_results.py` | `analyses/load_results.py` | Dataframe loaders for computed experiment outputs |
| `analyses/plot_*.py` | `analyses/plot_*.py` | Domain-specific plot generators (theta, omega, flux, etc.) |

### Intentionally excluded files

The following legacy files were deliberately omitted and replaced by our FastAPI/React application:
- **Streamlit UIs:** `app.py`, `tracking_from_video/tracking_app.py` (replaced by React frontend).
- **CLI & batch launchers:** `clam_pipeline/cli.py`, `clam_pipeline/_launcher.py`, `clam_pipeline/_track_launcher.py`, `analyses/run_all_plots.py`, `tracking_from_video/src/tracking_algae.py`.
- **Unused plotting scripts:** `clam_pipeline/plots.py` (contained `plot_theta_hist`, unused across the application).

---

## 2. Record of modified import lines

To ensure and verify that physical algorithms were not altered, all calculations, logic, and constants are identical to legacy.

### Detailed line changes

#### 1. `backend/core/clam_pipeline/analyze.py`
- Old: `import clamutils_exp as cu`
- New: `from core import clamutils_exp as cu`

#### 2. `backend/core/analyses/plot_density_vs_distance.py`
- Old: `import clamutils_exp as cu`
- New: `from core import clamutils_exp as cu`
- Old: `from analyses.load_results import load_settings, load_omega_file`
- New: `from core.analyses.load_results import load_settings, load_omega_file`
- Old: `from analyses.common import (`
- New: `from core.analyses.common import (`

#### 3. `backend/core/analyses/plot_flux.py`
- Old: `from analyses.load_results import load_settings, load_flux_file`
- New: `from core.analyses.load_results import load_settings, load_flux_file`
- Old: `from analyses.common import COLOR_PINK`
- New: `from core.analyses.common import COLOR_PINK`

#### 4. `backend/core/analyses/plot_theta_distribution.py`
- Old: `from analyses.load_results import load_settings, load_theta_file`
- New: `from core.analyses.load_results import load_settings, load_theta_file`
- Old: `from analyses.common import COLOR_GREEN, COLOR_ORANGE`
- New: `from core.analyses.common import COLOR_GREEN, COLOR_ORANGE`

#### 5. `backend/core/analyses/plot_theta_y_distribution.py`
- Old: `from analyses.load_results import load_theta_y_file`
- New: `from core.analyses.load_results import load_theta_y_file`
- Old: `from analyses.common import COLOR_GREEN, COLOR_ORANGE`
- New: `from core.analyses.common import COLOR_GREEN, COLOR_ORANGE`

#### 6. `backend/core/analyses/plot_tumbling.py`
- Old: `from analyses.common import bin_data, COLOR_PINK`
- New: `from core.analyses.common import bin_data, COLOR_PINK`

---

## 3. Known quirks and operational constraints

1. **`radial_map` requirement in core:**  
   In `clam_pipeline/analyze.py`, `AnalysisParams.radial_map` defaults to `True`. When enabled, the core attempts to read a local `radialEnergyDensityMap_<intensity>µW.txt` file, which does not exist in the laboratory dataset. Callers (such as application services and smoke tests) must explicitly pass `radial_map=False` to analyze movement with respect to distance from the center.
2. **Matplotlib headless configuration (`MPLBACKEND=Agg`):**  
   To prevent interactive graphical backends from blocking headless CI runners or unit tests (such as script entry points and plotting utilities), `MPLBACKEND=Agg` is enforced in `tests/conftest.py` and GitHub Actions.
3. **Empty trajectories bug in `analyze_experiment`:**  
   If trajectory DataFrames are empty, `analyze_experiment` fails when creating `AnalysisOutputs` due to missing `theta_y_axis0` and `theta_y_axis1`. This legacy bug is not fixed in the core.
4. **Parameter defaults:**  
   Legacy defaults for `disc_radius` (350 in `analyze.py`, 300 in `plot_flux.py`) differ from actual laboratory practice (120–150). Valid defaults are defined in application schemas rather than modifying core files.
5. **Linter exclusion:**  
   `backend/core/` is excluded from Ruff via `pyproject.toml` (`extend-exclude = ["core"]` and `force-exclude = true`) to preserve original formatting and line numbering.

---

## 4. Verification and smoke testing

A dedicated headless smoke test (`backend/tests/core/test_smoke.py`) verifies that the core package executes cleanly inside the backend environment using lightweight synthetic data:
- Verifies that all core modules import successfully without `ModuleNotFoundError`.
- Tests synthetic cell tracking linking 3 simulated cells across 10 frames.
- Tests `analyze_experiment(..., params=AnalysisParams(radial_map=False))` verifying that all 10 analysis tables are correctly populated with expected column schemas.