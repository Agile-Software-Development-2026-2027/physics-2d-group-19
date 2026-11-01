from pathlib import Path

import pandas as pd

from core.clam_pipeline.analyze import AnalysisOutputs


def save_analysis_results(
    exp_id: str | int,
    disc_radius: float,
    tumbling_threshold: float,
    results_data: AnalysisOutputs,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files: dict[str, Path] = {}

    disc_str = int(disc_radius) if disc_radius else 0
    tthres_str = f"{tumbling_threshold:.1f}"

    file_mapping = {
        "theta": (f"Theta_exp{exp_id}_FluoRadialised.txt", False),
        "flux": (f"Flux_exp{exp_id}_disc{disc_str}.txt", False),
        "tumbling_orientation": (f"tumb_exp{exp_id}_tthres{tthres_str}.txt", False),
        "tumbling_duration": (f"tumb_dur_exp{exp_id}_tthres{tthres_str}.txt", False),
        "angle": (f"angle_exp{exp_id}.txt", False),
        "omega": (f"omega_exp{exp_id}.txt", False),
        "theta_y_axis0": (f"ThetaY_axis0_exp{exp_id}.txt.gz", True),
        "theta_y_axis1": (f"ThetaY_axis1_exp{exp_id}.txt.gz", True),
    }

    for attr_name, (legacy_filename, use_gzip) in file_mapping.items():
        df = getattr(results_data, attr_name, None)

        if isinstance(df, pd.DataFrame):
            # 1. Salvataggio CSV per le API / Frontend
            csv_path = output_dir / f"{attr_name}.csv"
            df.to_csv(csv_path, index=False)
            saved_files[f"csv_{attr_name}"] = csv_path

            # 2. Salvataggio file Legacy .txt / .txt.gz
            legacy_path = output_dir / legacy_filename
            compression = "gzip" if use_gzip else None
            df.to_csv(legacy_path, sep="\t", index=False, compression=compression)
            saved_files[f"{attr_name}"] = legacy_path

    return saved_files
