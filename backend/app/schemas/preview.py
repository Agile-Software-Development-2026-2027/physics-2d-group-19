from pydantic import BaseModel, ConfigDict, Field


class PreviewResponse(BaseModel):
    """Response returned by GET /api/videos/{video_id}/preview (HTTP 200)."""

    model_config = ConfigDict(extra="forbid")

    frame: int = Field(ge=0, description="Index of the frame analyzed")
    cell_count: int = Field(ge=0, description="Number of cells identified in the frame")
    image: str = Field(
        description="Base64 encoded data URL (e.g. data:image/png;base64,...)",
    )
