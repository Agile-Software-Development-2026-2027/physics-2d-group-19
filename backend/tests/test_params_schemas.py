from dataclasses import asdict

import pytest
from pydantic import ValidationError

from app.resources import ANALYSIS_PARAMS, FILTER_PARAMS, TRACKING_CONFIG_JSON
from app.schemas.params import AnalysisParams, FilterParams, ProcessingParams, TrackingParams
from core.tracking_core import load_config_json

GROUPS = {"tracking": TrackingParams, "analysis": AnalysisParams, "filters": FilterParams}
POSITIVE = {
    "analysis": {"dt", "particle_show", "flux_cg_in", "flux_cg_out", "nskip"},
    "filters": {"dist_step"},
}
NUMERIC_FIELDS = [
    (group, name)
    for group, model in GROUPS.items()
    for name, field in model.model_fields.items()
    if field.annotation in (int, float, int | None)
]


def test_defaults_match_lab_resources():
    assert ProcessingParams().model_dump() == {
        "tracking": asdict(load_config_json(TRACKING_CONFIG_JSON)),
        "analysis": asdict(ANALYSIS_PARAMS),
        "filters": asdict(FILTER_PARAMS),
    }


def test_groups_are_independent():
    first, second = ProcessingParams(), ProcessingParams()
    first.tracking.diameter = 7
    first.analysis.dt = 0.2
    first.filters.lifetime_min = 10
    for group in GROUPS:
        assert getattr(first, group) is not getattr(second, group)
        assert getattr(first, group) != getattr(second, group)
        assert getattr(second, group) == GROUPS[group]()


@pytest.mark.parametrize("diameter", [-3, 0, 1, 2, 6])
def test_invalid_diameter_is_rejected(diameter):
    with pytest.raises(ValidationError) as exc:
        TrackingParams(diameter=diameter)
    assert exc.value.errors()[0]["loc"] == ("diameter",)


@pytest.mark.parametrize("diameter", [3, 5])
def test_valid_diameter_is_accepted(diameter):
    assert TrackingParams(diameter=diameter).diameter == diameter


@pytest.mark.parametrize(("group", "field"), NUMERIC_FIELDS)
def test_numeric_boundaries(group, field):
    for invalid in [-1, 0] if field in POSITIVE.get(group, set()) else [-1]:
        with pytest.raises(ValidationError) as exc:
            ProcessingParams(**{group: {field: invalid}})
        assert exc.value.errors()[0]["loc"] == (group, field)
    boundary = 3 if field == "diameter" else int(field in POSITIVE.get(group, set()))
    assert (
        getattr(getattr(ProcessingParams(**{group: {field: boundary}}), group), field) == boundary
    )


@pytest.mark.parametrize("method", ["mean", "median"])
def test_background_methods(method):
    assert TrackingParams(background_method=method).background_method == method


def test_unknown_background_method_is_rejected():
    with pytest.raises(ValidationError) as exc:
        TrackingParams(background_method="unknown")
    assert exc.value.errors()[0]["loc"] == ("background_method",)


@pytest.mark.parametrize("group", [None, *GROUPS])
def test_unknown_fields_are_rejected(group):
    payload = {"unknown": 1} if group is None else {group: {"unknown": 1}}
    with pytest.raises(ValidationError) as exc:
        ProcessingParams(**payload)
    assert exc.value.errors()[0]["loc"] == ((group, "unknown") if group else ("unknown",))


@pytest.mark.parametrize("memory", [None, 0, 3])
def test_json_round_trip(memory):
    params = ProcessingParams(
        tracking={"memory": memory, "background_method": "median"},
        analysis={"dt": 0.2},
        filters={"strict": False},
    )
    assert ProcessingParams.model_validate_json(params.model_dump_json()) == params
    assert ProcessingParams.model_validate(params.model_dump()) == params


def test_json_schema_contract():
    schema = ProcessingParams.model_json_schema()
    assert set(schema["properties"]) == set(GROUPS)
    assert schema["additionalProperties"] is False
    for group, model in GROUPS.items():
        assert schema["properties"][group]["description"]
        assert schema["properties"][group]["$ref"] == f"#/$defs/{model.__name__}"
        definition = schema["$defs"][model.__name__]
        assert definition["additionalProperties"] is False
        assert set(definition["properties"]) == set(model.model_fields)
        for name, default in model().model_dump().items():
            prop = definition["properties"][name]
            assert prop["default"] == default
            assert prop["description"]
            if (group, name) in NUMERIC_FIELDS:
                limit = prop["anyOf"][0] if name == "memory" else prop
                key = "exclusiveMinimum" if name == "dt" else "minimum"
                expected = 3 if name == "diameter" else int(name in POSITIVE.get(group, set()))
                assert limit[key] == (0 if name == "dt" else expected)
    tracking = schema["$defs"]["TrackingParams"]["properties"]
    assert tracking["background_method"]["enum"] == ["mean", "median"]
    assert "odd" in tracking["diameter"]["description"]
    assert {"type": "null"} in tracking["memory"]["anyOf"]
