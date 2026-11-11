from dataclasses import asdict
from pathlib import Path

from app.resources import ANALYSIS_PARAMS, FILTER_PARAMS, TRACKING_CONFIG_JSON
from app.schemas.params import AnalysisParams, FilterParams, ProcessingParams, TrackingParams
from app.services.analysis import run_analysis
from app.services.params_mapping import to_core
from core.clam_pipeline.analyze import AnalysisParams as CoreAnalysisParams
from core.clam_pipeline.analyze import FilterParams as CoreFilterParams
from core.tracking_core import TrackingConfig, load_config_json
from tests.core.test_regression_analysis import ATOL_LEGACY, RTOL_LEGACY, _load_fixture_table
from tests.helpers.compare import assert_tables_close

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "exp49"


# Ensure default ProcessingParams convert into exact laboratory baseline resources
def test_to_core_defaults_match_lab_resources():
    default_processing = ProcessingParams()
    tracking_cfg, analysis_params, filter_params = to_core(default_processing)

    # Verify tracking config matches laboratory config_tracking-49-65.json
    expected_tracking = load_config_json(TRACKING_CONFIG_JSON)
    assert isinstance(tracking_cfg, TrackingConfig)
    assert asdict(tracking_cfg) == asdict(expected_tracking)

    # Verify analysis params match laboratory default resources
    assert isinstance(analysis_params, CoreAnalysisParams)
    assert asdict(analysis_params) == asdict(ANALYSIS_PARAMS)

    # Verify filter params match laboratory default resources
    assert isinstance(filter_params, CoreFilterParams)
    assert asdict(filter_params) == asdict(FILTER_PARAMS)


# Verify that user-defined parameter overrides propagate accurately field by field
def test_to_core_custom_values_are_mapped():
    custom_processing = ProcessingParams(
        tracking=TrackingParams(
            diameter=7,
            minmass=250,
            search_range=15,
            background_method="median",
            memory=3,
        ),
        analysis=AnalysisParams(
            dt=0.05,
            disc_radius=150.0,
            tumbling_threshold=6.5,
        ),
        filters=FilterParams(
            lifetime_min=5.0,
            strict=False,
            blinking_ratio=0.8,
        ),
    )

    tracking_cfg, analysis_params, filter_params = to_core(custom_processing)

    assert tracking_cfg.diameter == 7
    assert tracking_cfg.minmass == 250
    assert tracking_cfg.search_range == 15
    assert tracking_cfg.background_method == "median"
    assert tracking_cfg.memory == 3

    assert analysis_params.dt == 0.05
    assert analysis_params.disc_radius == 150.0
    assert analysis_params.tumbling_threshold == 6.5

    assert filter_params.lifetime_min == 5.0
    assert filter_params.strict is False
    assert filter_params.blinking_ratio == 0.8


# Integration check: core analysis produces regression-exact outputs with mapped objects
def test_run_analysis_with_converted_core_params():
    # Pass explicit mapped parameters to run_analysis
    _, core_params, core_fparams = to_core(ProcessingParams())

    out = run_analysis(
        49,
        FIXTURES_DIR / "talgae_settings.txt",
        FIXTURES_DIR / "tAlgae49.txt",
        FIXTURES_DIR,
        params=core_params,
        fparams=core_fparams,
    )

    # Verify angle distribution metrics against confirmed laboratory reference fixture
    expected = _load_fixture_table(FIXTURES_DIR / "angle_exp49", ["angle", "dist", "v"])
    assert_tables_close(out.angle, expected, rtol=RTOL_LEGACY, atol=ATOL_LEGACY)


# Verify when params and fparams are omitted
def test_run_analysis_default_fallback():
    out = run_analysis(
        49, FIXTURES_DIR / "talgae_settings.txt", FIXTURES_DIR / "tAlgae49.txt", FIXTURES_DIR
    )
    expected = _load_fixture_table(FIXTURES_DIR / "angle_exp49", ["angle", "dist", "v"])
    assert_tables_close(out.angle, expected, rtol=RTOL_LEGACY, atol=ATOL_LEGACY)


# Verify that optional memory field set to None is preserved during mapping
def test_to_core_memory_none_is_preserved():
    params = ProcessingParams()
    assert params.tracking.memory is None
    tracking_cfg, _, _ = to_core(params)
    assert tracking_cfg.memory is None
