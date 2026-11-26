# Pydantic schemas for experimental setups

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# The physical setup fields with identical constraints to ExperimentSettings
class SetupValues(BaseModel):
    # Reject unknown fields
    model_config = ConfigDict(extra="forbid")

    exp_type: Literal[0, 1, 2, 3, 4, 5] = Field(
        0,
        description="0=none , 1=normal , 2=gaussian , 3=outside , 4=single cell , 5=LED",
    )
    ill: int = Field(ge=0, description="Illumination image number")
    intensity: int = Field(ge=0, description="Illumination intensity")
    pix_arr: float = Field(gt=0, description="Pixel size")
    ctr: Literal[-1, 0, 1] = Field(
        0, description="Illumination centre : 0 = centre , 1 = right , -1 = left"
    )
    fluo: Literal[0, 1, 2] = Field(
        0, description="Fluorescense image : 0=none , 1=ring , 2=gaussian"
    )
    lin: Literal[0, 1] = Field(0, description="Linear illumination : 0=no , 1=yes")
    axis: Literal[0, 1] = Field(0, description="Axis of the linear gradient : 0=x , 1=y")


# Payload to create or update a setup
class SetupCreate(SetupValues):
    name: str = Field(min_length=1, max_length=60, description="Unique setup name")
    is_default: bool = Field(False, description="Whether this setup is the default one")

    # Strips leading/trailing whitespace and ensures the name is not empty
    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Setup name cannot be empty or only whitespace")
        if len(trimmed) > 60:
            raise ValueError("Setup name cannot exceed 60 characters")
        return trimmed


# Full setup with generated 12-char identifier
class Setup(SetupCreate):
    id: str = Field(pattern=r"^[0-9a-f]{12}$", description="Unique 12 character identifier")
