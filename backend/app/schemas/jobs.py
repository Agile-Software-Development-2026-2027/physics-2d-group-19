from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    TRACKING = "tracking"
    ANALYZING = "analyzing"
    PLOTS = "plots"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: int = Field(ge=0, description="Experiment identifier")
    video_filename: str = Field(min_length=1, description="Uploaded video filename")
    tracking_params: dict[str, Any] | None = Field(
        default=None,
        description="Tracking configuration overrides",
    )
    analysis_params: dict[str, Any] | None = Field(
        default=None,
        description="Analysis configuration overrides",
    )


class JobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job execution identifier")
    status: JobStatus = Field(description="Current status of the job")
    current_phase: str = Field(description="Human readable current processing phase")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    created_at: datetime = Field(description="Job submission timestamp")
    completed_at: datetime | None = Field(default=None, description="Job completion timestamp")
    error_message: str | None = Field(default=None, description="Error details if the job failed")
