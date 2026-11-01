from pathlib import Path

from core.clam_pipeline.analyze import AnalysisParams, FilterParams

RESOURCES_DIR = Path(__file__).parent

SETTINGS_TXT = RESOURCES_DIR / "talgae_settings.txt"
TRACKING_CONFIG_JSON = RESOURCES_DIR / "config_tracking-49-65.json"


ANALYSIS_PARAMS = AnalysisParams(
    diam=10,
    dt=0.1,
    particle_show=5,
    disc_radius=350,
    flux_cg_in=1,
    flux_cg_out=150,
    tumbling_threshold=5.0,
    radial_map=False,
    nskip=1,
)

FILTER_PARAMS = FilterParams(
    lifetime_min=0,
    threshold_dist=0,
    threshold_dist_tot=0,
    dist_step=1,
    strict=True,
    only_inside=True,
    blinking_ratio=0,
    blinking_tolerance=0,
    long_track_min_snaps=0,
)
