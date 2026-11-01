from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlotItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Plot identifier, e.g. theta, flux, omega")
    title: str = Field(description="Display title for the plot")
    url: str = Field(description="URL to retrieve the generated PNG plot")


class JobResultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Job execution identifier")
    status: str = Field(default="completed", description="Status of the result")
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
