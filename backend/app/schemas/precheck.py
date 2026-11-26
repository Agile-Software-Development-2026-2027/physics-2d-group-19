from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_PRECHECK_IDS = 50


class PrecheckRequest(BaseModel):
    """Experiments to check before starting a batch (31.3)."""

    model_config = ConfigDict(extra="forbid")

    exp_ids: list[Annotated[int, Field(ge=0)]] = Field(
        min_length=1,
        max_length=MAX_PRECHECK_IDS,
        description="Experiment numbers, without duplicates",
    )

    @field_validator("exp_ids")
    @classmethod
    def no_duplicates(cls, exp_ids: list[int]) -> list[int]:
        if len(set(exp_ids)) != len(exp_ids):
            raise ValueError("exp_ids must not contain duplicates")
        return exp_ids


class PrecheckItem(BaseModel):
    """Whether one experiment can be processed, and why not."""

    model_config = ConfigDict(extra="forbid")

    exp_id: int
    registered: bool = Field(description="The experiment is in the settings file")
    no_skip: bool | None = Field(description="Include in analysis; None if not registered")
    video: str | None = Field(description="File name of the video found, if any")
    trajectories: str | None = Field(description="File name of the trajectories found, if any")
    illumination: str | None = Field(description="File name of the illumination found, if any")
    ready: bool = Field(description="True when the experiment can be processed")
    reason: str | None = Field(description="First missing requirement; None when ready")
