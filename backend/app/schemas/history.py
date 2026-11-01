from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jobs import JobStatus


class HistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job execution identifier")
    experiment_id: int = Field(ge=0, description="Experiment identifier")
    status: JobStatus = Field(description="Final or current status")
    video_filename: str = Field(description="Name of the processed video")
    created_at: datetime = Field(description="Execution start timestamp")
    duration_seconds: float | None = Field(default=None, ge=0.0, description="Processing duration in seconds")


class HistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[HistoryItem] = Field(default_factory=list, description="List of previous jobs")
    total: int = Field(ge=0, description="Total number of historical runs")

