from pydantic import BaseModel, ConfigDict, Field, field_validator


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_number: int = Field(default=0, ge=0, description="Video frame index to preview")
    diameter: int = Field(default=5, ge=3, description="Cell feature diameter (must be odd)")
    minmass: float = Field(default=180.0, ge=0.0, description="Minimum integrated brightness")
    bg_method: str = Field(
        default="mean",
        description="Background subtraction method: mean or median",
    )

    @field_validator("diameter")
    @classmethod
    def validate_diameter_odd(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError("diameter must be an odd integer")
        return v


class PreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_number: int = Field(description="Frame index analysed")
    detected_cells: int = Field(ge=0, description="Number of cells identified in the frame")
    image_url: str = Field(description="URL to the generated preview image with circles")
    note: str = Field(
        default="Preview uses a sampled background; final tracking may vary slightly",
        description="Disclaimer note about preview estimation",
    )
