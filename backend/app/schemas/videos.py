from pydantic import BaseModel, ConfigDict, Field


class VideoUploadResponse(BaseModel):
    """Response returned after uploading a video via POST /api/videos (HTTP 201)."""

    model_config = ConfigDict(extra="forbid")

    video_id: str = Field(description="12-character hex identifier for the uploaded video")
    filename: str = Field(description="Original filename of the uploaded video")
    size_bytes: int = Field(ge=0, description="Size of the uploaded video in bytes")
    frames: int = Field(ge=0, description="Total number of frames in the video")
    fps: float = Field(gt=0.0, description="Frames per second of the video")

