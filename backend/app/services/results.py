from pathlib import Path
import numpy as np
from core.clam_pipeline.analyze import AnalysisOutputs, AnalysisParams


# This function is from the legacy-code/clam-pipeline-cli.py file
def _save_legacy_txt(df, out_path: Path, header: str, float_fmt: str = "%.6f") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header)
        return

    arr = df.to_numpy()
    fmt = [float_fmt] * arr.shape[1]
    np.savetxt(out_path, np.array([]))
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(header)
        np.savetxt(f, arr, fmt=fmt)


def save_legacy_txt(
    outputs: AnalysisOutputs,
    results_dir: Path,
    exp_id: int,
    params: AnalysisParams,
) -> list[Path]:
    results_dir.mkdir(parents=True, exist_ok=True)

    disc_str = int(params.disc_radius)
    tthres_str = f"{params.tumbling_threshold:.1f}"

    files_to_save = [
        (
            outputs.nt_stats[["N", "n_disc", "dists"]],
            results_dir / f"N_dist_exp{exp_id}_disc{disc_str}.txt",
            "N n_disc dists\n",
        ),
        (
            outputs.nt_stats[["N_raw", "n_disc_raw", "dists_raw", "N", "n_disc", "dists"]],
            results_dir / f"N_dist_compare_exp{exp_id}_disc{disc_str}.txt",
            "N_raw n_disc_raw dists_raw N n_disc dists\n",
        ),
        (
            outputs.flux,
            results_dir / f"Flux_exp{exp_id}_disc{disc_str}.txt",
            "time flux\n",
        ),
        (
            outputs.theta,
            results_dir / f"Theta_exp{exp_id}_FluoRadialised.txt",
            "Theta dists\n",
        ),
        (
            outputs.theta_y,
            results_dir / f"ThetaY_exp{exp_id}.txt",
            "theta_y dist\n",
        ),
        (
            outputs.theta_y_axis0,
            results_dir / f"ThetaY_axis0_exp{exp_id}.txt",
            "theta_y dist\n",
        ),
        (
            outputs.theta_y_axis1,
            results_dir / f"ThetaY_axis1_exp{exp_id}.txt",
            "theta_y dist\n",
        ),
        (
            outputs.angle,
            results_dir / f"angle_exp{exp_id}.txt",
            "angle dists v\n",
        ),
        (
            outputs.omega,
            results_dir / f"omega_exp{exp_id}.txt",
            "omega dists time\n",
        ),
        (
            outputs.tumbling_orientation,
            results_dir / f"tumb_exp{exp_id}_tthres{tthres_str}.txt",
            "theta dists duration time\n",
        ),
        (
            outputs.tumbling_duration,
            results_dir / f"tumb_dur_exp{exp_id}_tthres{tthres_str}.txt",
            "dists duration time\n",
        ),
    ]

    saved_paths: list[Path] = []
    for df, out_path, header in files_to_save:
        _save_legacy_txt(df, out_path, header)
        saved_paths.append(out_path)

    return saved_paths
