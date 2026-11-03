from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jobs import JobStatus


class PlotItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Plot name, e.g. flux, theta")
    url: str | None = Field(default=None, description="PNG URL, null if the plot failed")
    error: str | None = Field(default=None, description="Error message if the plot failed")


class JobResultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Job execution identifier")
    status: JobStatus = Field(default=JobStatus.DONE, description="Status of the result")
    plots: list[PlotItem] = Field(
        default_factory=list,
        description="List of generated plot graphics",
    )
    data_files: list[str] = Field(
        default_factory=list,
        description="List of generated CSV or legacy TXT files",
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary physical metrics dictionary",
    )
