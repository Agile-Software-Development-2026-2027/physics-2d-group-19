import pandas as pd

from app.schemas.experiment import ExperimentSettings


# this function write down the 10 values in a string row
def to_settings_line(settings: ExperimentSettings):

    if settings.no_skip:
        no_skip = 1
    else:
        no_skip = 0

    pix_arr = f"{settings.pix_arr:.6f}"

    data = [
        settings.exps,
        settings.exp_type,
        settings.ill,
        settings.intensity,
        pix_arr,
        no_skip,
        settings.ctr,
        settings.fluo,
        settings.lin,
        settings.axis,
    ]

    text_data = []

    for d in data:
        text_data.append(str(d))

    return " ".join(text_data)


# this function write down the 10 values in a pandas row , with the column use


def to_setting_row(settings: ExperimentSettings):

    if settings.no_skip:
        no_skip = 1
    else:
        no_skip = 0

    row = {
        "exps": settings.exps,
        "exp_type": settings.exp_type,
        "ill": settings.ill,
        "intensity": settings.intensity,
        "pix_arr": settings.pix_arr,
        "no_skip": no_skip,
        "ctr": settings.ctr,
        "fluo": settings.fluo,
        "lin": settings.lin,
        "axis": settings.axis,
        # load_settings adds this column too: True if the experiment is used
        "use": settings.no_skip,
    }

    return pd.Series(row)
