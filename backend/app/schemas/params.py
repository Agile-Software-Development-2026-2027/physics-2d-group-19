"""Shared processing contract, with experiment 49 laboratory defaults."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrackingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: int = Field(2, ge=0, description="Video channel index")
    background_subtraction: bool = Field(True, description="Subtract the video background")
    background_method: Literal["mean", "median"] = Field(
        "mean", description="Method used to estimate the video background"
    )
    diameter: int = Field(5, ge=3, description="Feature diameter in pixels; odd and at least 3")
    minmass: int = Field(180, ge=0, description="Minimum integrated feature brightness")
    invert: bool = Field(False, description="Detect dark features on a bright background")
    search_range: int = Field(10, ge=0, description="Maximum displacement between linked frames")
    adaptive_stop: int = Field(5, ge=0, description="Minimum search range during adaptive linking")
    adaptive_step: float = Field(0.98, ge=0, description="Adaptive linking search range multiplier")
    memory: int | None = Field(
        None, ge=0, description="Missing frames allowed; null uses the video frame count minus one"
    )
    filter_stubs: int = Field(0, ge=0, description="Minimum observations per retained track")

    @field_validator("diameter")
    @classmethod
    def diameter_must_be_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("diameter must be odd")
        return value


class AnalysisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diam: float = Field(10, ge=0, description="Diameter used to smooth the illumination field")
    dt: float = Field(0.1, gt=0, description="Time interval between consecutive frames")
    particle_show: int = Field(5, ge=1, description="Gradient and velocity frame spacing")
    disc_radius: float = Field(350, ge=0, description="Disc radius for flux and particle counts")
    flux_cg_in: int = Field(1, ge=1, description="Frame spacing for detecting disc crossings")
    flux_cg_out: int = Field(150, ge=1, description="Frames per flux aggregation interval")
    tumbling_threshold: float = Field(5.0, ge=0, description="Tumbling angular velocity threshold")
    radial_map: bool = Field(False, description="Use a radial energy density map")
    nskip: int = Field(1, ge=1, description="Frame spacing for particle count statistics")


class FilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lifetime_min: float = Field(0, ge=0, description="Minimum track lifetime")
    threshold_dist: float = Field(0, ge=0, description="Minimum median step displacement")
    threshold_dist_tot: float = Field(0, ge=0, description="Minimum track endpoint displacement")
    dist_step: int = Field(1, ge=1, description="Observation spacing used by trajectory cleaning")
    strict: bool = Field(True, description="Apply strict trajectory endpoint filtering")
    only_inside: bool = Field(True, description="Keep only trajectory points inside the image")
    blinking_ratio: float = Field(0, ge=0, description="Minimum track presence ratio")
    blinking_tolerance: float = Field(0, ge=0, description="Long track presence ratio tolerance")
    long_track_min_snaps: int = Field(
        0, ge=0, description="Observations required for long track tolerance"
    )


class ProcessingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tracking: TrackingParams = Field(
        default_factory=TrackingParams, description="Tracking settings"
    )
    analysis: AnalysisParams = Field(
        default_factory=AnalysisParams, description="Analysis settings"
    )
    filters: FilterParams = Field(default_factory=FilterParams, description="Track filters")
