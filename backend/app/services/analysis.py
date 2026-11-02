# Analysis service executing core physical computations on trajectories

from pathlib import Path

from app.resources import ANALYSIS_PARAMS, FILTER_PARAMS
from core.clam_pipeline.analyze import AnalysisOutputs, analyze_experiment
from core.clam_pipeline.io import load_settings, load_trajectories_txt


# Run core physical analysis on experiment trajectories.
def run_analysis(
    exp_id: int, settings_txt: Path, traj_txt: Path, illum_dir: Path
) -> AnalysisOutputs:

    settings_df = load_settings(settings_txt)

    # Filter configuration rows matching the specified experiment identifier
    matching_rows = settings_df.loc[settings_df["exps"] == exp_id]
    if matching_rows.empty:
        raise ValueError(f"Experiment {exp_id} not found in settings")

    # Extract the matching row as a Pandas Series for the core pipeline
    settings_row = matching_rows.iloc[0]

    try:
        # Parse the comma-separated particle trajectory coordinates file
        traj_df = load_trajectories_txt(traj_txt)
    except ValueError as exc:
        raise ValueError("No trajectories to analyse") from exc

    if traj_df.empty:
        raise ValueError("No trajectories to analyse")

    # Set dummy radial directory since radial_map=False skips disk reading
    radial_dir = illum_dir / "_no_radial_map"

    # Invoke the core pipeline and return physical computation metric tables
    return analyze_experiment(
        exp_id=exp_id,
        settings_row=settings_row,
        traj_df=traj_df,
        illum_dir=illum_dir,
        radial_dir=radial_dir,
        params=ANALYSIS_PARAMS,
        fparams=FILTER_PARAMS,
    )
