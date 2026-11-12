from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jobs import JobStatus


class HistoryItem(BaseModel):
    """Single historical job summary returned by GET /api/history."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job execution identifier")
    exp_id: int = Field(ge=0, description="Experiment identifier")
    status: JobStatus = Field(description="Execution status")
    created_at: datetime | str = Field(description="Timestamp when the job was created")
    video: str | None = Field(default=None, description="Original video filename if available")
