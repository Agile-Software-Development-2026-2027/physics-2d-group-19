from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    TRACKING = "tracking"
    ANALYSIS = "analysis"
    PLOTS = "plots"
    DONE = "done"
    ERROR = "error"


class JobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job execution identifier")
    exp_id: int = Field(ge=0, description="Experiment identifier")
    status: JobStatus = Field(description="Current status of the job")
    error: str | None = Field(default=None, description="Error message if status is error")
