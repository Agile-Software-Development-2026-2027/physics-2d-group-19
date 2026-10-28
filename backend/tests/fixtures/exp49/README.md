# Experiment 49 fixtures

Data for the regression tests of US-1: the core must give the same results as the lab code on experiment 49.

## Files from the lab

All files in this folder come from the project Google Drive (`R&D Physics 2D/2d/2d`) and are byte-identical to it. They are never regenerated.

| File | What it is | md5 |
| --- | --- | --- |
| `tAlgae49.txt` | Trajectories from the lab tracking of video 49 (input of the analysis) | `310d7ed27141c726224e1775f1a62334` |
| `talgae_settings.txt` | Lab settings for every experiment (row 49: `49 1 14 180 1.041667 1 0 0 0 0`) | `a79400bbfbdd2c499806e4d6f7cdcacb` |
| `illumination14.tiff` | Illumination image 14, used by experiment 49 | `7598764c6a883937baea9daab6ed5114` |
| `tumb_exp49_tthres5.0.txt` | Lab output: tumbling events | `388672ffa4f01aa75594c93e85f0c1eb` |
| `tumb_dur_exp49_tthres5.0.txt` | Lab output: tumbling durations | `a6230cc6d600d88e96cead3f69081082` |
| `Theta_exp49_FluoRadialised.txt` | Lab output: theta | `0def3cdd835aa3d34e344afafd6823d9` |
| `angle_exp49.txt` | Lab output: angle | `9c5255d86e461b0bbc1939952841c247` |
| `omega_exp49.txt` | Lab output: omega | `7c57ff1fbc6e0c97f94d3fb62ed979f4` |

Check them with `md5sum backend/tests/fixtures/exp49/*.txt backend/tests/fixtures/exp49/*.tiff`.

The five lab outputs are the expected values of the regression test: running the legacy analysis with the parameters below reproduces all of them byte for byte.

## Generated reference (`reference/`)

For these outputs there is no lab file, so the expected values come from the legacy code, run by `backend/scripts/make_reference.py`. The files are gzipped text (`np.loadtxt` and `pd.read_csv` read them directly), with a header row, space separators and LF line endings.

| File | Columns | Data rows |
| --- | --- | --- |
| `Flux_exp49_disc350.txt.gz` | `time flux` | 10 |
| `N_dist_exp49_disc350.txt.gz` | `N n_disc dists` | 1,500 |
| `N_dist_compare_exp49_disc350.txt.gz` | `N_raw n_disc_raw dists_raw N n_disc dists` | 1,500 |
| `ThetaY_exp49.txt.gz` | `theta_y dist` | 222,702 |
| `ThetaY_axis0_exp49.txt.gz` | `theta_y dist` | 222,702 |
| `ThetaY_axis1_exp49.txt.gz` | `theta_y dist` | 0 (the legacy writes only the header) |

These are not confirmed by the lab yet. `Flux` and `N_dist` depend on the disc radius, which was taken from the live demo and not checked against a lab file.

## Parameters

Analysis (`AnalysisParams`):

| Parameter | Value | Note |
| --- | --- | --- |
| `dt` | 0.1 | Confirmed by the lab outputs |
| `tumbling_threshold` | 5.0 | Confirmed by the lab outputs |
| `disc_radius` | 350 | Not confirmed; also in the `Flux` and `N_dist` file names |
| `diam` | 10 | |
| `particle_show` | 5 | |
| `flux_cg_in`, `flux_cg_out` | 1, 150 | |
| `radial_map` | False | Distance from the centre; there is no radial map for experiment 49 |
| `nskip` | 1 | |

Trajectory filters (`FilterParams`) are all off: `lifetime_min`, `threshold_dist`, `threshold_dist_tot`, `blinking_ratio`, `blinking_tolerance` and `long_track_min_snaps` are 0, `dist_step` is 1, `strict` and `only_inside` are True. The planning document listed `threshold_dist` 1, `threshold_dist_tot` 3 and `blinking_ratio` 0.5, but only with the filters off do the outputs match the lab files.

Library versions: Python 3.12, numpy 2.3.5, pandas 2.3.3, scipy 1.17.0, matplotlib 3.10.8, the same as `legacy-code/requirements.txt`.

## Still to confirm with the lab

- The disc radius for `Flux` and `N_dist` (350 here; the operator mentioned 120–150 in the meeting).
- Whether `ThetaY_axis1` is expected to be empty.
- Whether `tAlgae49.txt` was tracked with `legacy-code/tracking_from_video/configs/config_tracking-49-65.json`.

When the lab answers, record the answer here. If a parameter changes, regenerate `reference/` in a dedicated PR and explain why in its description: the `.gz` files are binary, so the diff does not show what changed.

## Regenerating `reference/`

From the repository root, with the backend environment (Python 3.12 and `backend/requirements.txt`):

```bash
backend/.venv/bin/python backend/scripts/make_reference.py
```

On Windows the interpreter is `backend\.venv\Scripts\python`. The script runs the legacy analysis in a temporary folder, writes only the `reference/` files and compares the five generated lab outputs with the files above. The output is reproducible: with the same inputs and versions, `git status` stays clean.

Add `--plots <folder>` to also save the PDF plots. Keep them out of the repository.
