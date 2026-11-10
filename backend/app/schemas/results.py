from pydantic import BaseModel, ConfigDict, Field


class ResultFileItem(BaseModel):
    """Single CSV result file descriptor returned in GET /api/jobs/{job_id}/results."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Name of the physical metric, e.g. theta, flux, omega")
    url: str = Field(description="Download URL endpoint for the CSV file")

