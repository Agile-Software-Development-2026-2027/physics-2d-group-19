from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    """Official lifecycle states of a processing job."""

    QUEUED = "queued"
    TRACKING = "tracking"
    ANALYSIS = "analysis"
    PLOTS = "plots"
    DONE = "done"
    ERROR = "error"


class JobCreateResponse(BaseModel):
    """Response returned when a new job is accepted by POST /api/jobs (HTTP 202)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="12-character hex identifier of the created job")
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Initial status, always 'queued'",
    )


class JobStatusResponse(BaseModel):
    """Full status response returned by GET /api/jobs/{job_id}."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="12-character hex job identifier")
    exp_id: int = Field(ge=0, description="Experiment ID being processed")
    status: JobStatus = Field(description="Current execution state")
    created_at: datetime | str | None = Field(
        default=None,
        description="Timestamp when the job was created",
    )
    plots: dict[str, str | None] | None = Field(
        default=None,
        description="Mapping of plot name to error message if plot failed, else None",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the job failed",
    )

