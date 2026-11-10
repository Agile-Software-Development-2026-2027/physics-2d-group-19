# Mapping between API parameter schemas and core execution dataclasses

from app.schemas.params import ProcessingParams
from core.clam_pipeline.analyze import AnalysisParams as CoreAnalysisParams
from core.clam_pipeline.analyze import FilterParams as CoreFilterParams
from core.tracking_core import TrackingConfig


# Convert API ProcessingParams into core dataclasses for tracking and analysis
def to_core(
    params: ProcessingParams,
) -> tuple[TrackingConfig, CoreAnalysisParams, CoreFilterParams]:

    # Map video particle detection and trajectory linking parameters
    t = params.tracking
    tracking_cfg = TrackingConfig(
        channel=t.channel,
        background_subtraction=t.background_subtraction,
        background_method=t.background_method,
        diameter=t.diameter,
        minmass=t.minmass,
        invert=t.invert,
        search_range=t.search_range,
        adaptive_stop=t.adaptive_stop,
        adaptive_step=t.adaptive_step,
        memory=t.memory,
        filter_stubs=t.filter_stubs,
    )

    # Map physical observables analysis configuration
    a = params.analysis
    analysis_params = CoreAnalysisParams(
        diam=a.diam,
        dt=a.dt,
        particle_show=a.particle_show,
        disc_radius=a.disc_radius,
        flux_cg_in=a.flux_cg_in,
        flux_cg_out=a.flux_cg_out,
        tumbling_threshold=a.tumbling_threshold,
        radial_map=a.radial_map,
        nskip=a.nskip,
    )

    # Map trajectory cleaning and outlier filtration thresholds
    f = params.filters
    filter_params = CoreFilterParams(
        lifetime_min=f.lifetime_min,
        threshold_dist=f.threshold_dist,
        threshold_dist_tot=f.threshold_dist_tot,
        dist_step=f.dist_step,
        strict=f.strict,
        only_inside=f.only_inside,
        blinking_ratio=f.blinking_ratio,
        blinking_tolerance=f.blinking_tolerance,
        long_track_min_snaps=f.long_track_min_snaps,
    )

    return tracking_cfg, analysis_params, filter_params
