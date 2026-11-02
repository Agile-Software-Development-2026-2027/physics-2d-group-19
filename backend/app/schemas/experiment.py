from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExperimentSettings(BaseModel):
    # reject unknown fields
    model_config = ConfigDict(extra="forbid")

    # same order as the array "SETTINGS_COLUMNS " in backend\core\clam_pipeline\io.py
    exps: int = Field(ge=0, description="Experiment number")

    exp_type: Literal[0, 1, 2, 3, 4, 5] = Field(
        0,
        description="0=none , 1=normal , 2=gaussian , 3=outside , 4=single cell , 5=LED",
    )

    ill: int = Field(ge=0, description="Illumination image number")

    intensity: int = Field(ge=0, description="Illumination intensity")

    pix_arr: float = Field(gt=0, description="Pixel size")

    no_skip: bool = Field(True, description="Include the experiment in the analysis")

    ctr: Literal[-1, 0, 1] = Field(
        0, description="Illumination centre : 0 = centre , 1 = right , -1 = left"
    )

    fluo: Literal[0, 1, 2] = Field(
        0, description="Fluorescense image : 0=none , 1=ring , 2=gaussian"
    )

    lin: Literal[0, 1] = Field(0, description="Linear illumination : 0=no , 1=yes")

    axis: Literal[0, 1] = Field(0, description="Axis of the linear gradient : 0=x , 1=y")
