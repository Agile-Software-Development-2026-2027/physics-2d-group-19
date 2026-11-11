# API router for processing parameters defaults and schema metadata

from typing import Any

from fastapi import APIRouter

from app.schemas.params import ProcessingParams

router = APIRouter(prefix="/params", tags=["params"])


# Extract field limits, descriptions, and constraints from model JSON schema
def _extract_limits() -> dict[str, dict[str, Any]]:

    # In Pydantic v2, nested sub-models referenced by the root schema
    # are placed under the top-level '$defs' dictionary
    schema = ProcessingParams.model_json_schema()
    # '$defs' contains schema definitions for reusable/nested sub-models
    defs = schema.get("$defs", {})

    # Map client-facing grouping keys to their internal Pydantic class names in $defs
    mapping = {
        "tracking": "TrackingParams",
        "analysis": "AnalysisParams",
        "filters": "FilterParams",
    }

    # Keys to pull out from each field's JSON schema specification
    constraint_keys = [
        "description",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "enum",
    ]

    limits: dict[str, dict[str, Any]] = {}
    for group_name, model_name in mapping.items():
        properties = defs.get(model_name, {}).get("properties", {})
        group_limits: dict[str, Any] = {}

        for prop_name, prop_data in properties.items():
            field_limit: dict[str, Any] = {}

            # Direct constraints
            for key in constraint_keys:
                if key in prop_data:
                    field_limit[key] = prop_data[key]

            # Nested constraints inside anyOf (e.g. Optional / int | None)
            if "anyOf" in prop_data:
                for variant in prop_data["anyOf"]:
                    for key in constraint_keys:
                        if key in variant and key not in field_limit:
                            field_limit[key] = variant[key]

            group_limits[prop_name] = field_limit

        limits[group_name] = group_limits

    return limits


# Return verified laboratory default parameters and schema constraints
@router.get("/defaults")
def get_default_parameters() -> dict[str, Any]:

    params = ProcessingParams()
    return {
        **params.model_dump(),
        "limits": _extract_limits(),
    }
