"""Check which experiments of a batch can be processed, without reading any video (31.3)."""

from pathlib import Path

from app.config import Settings
from app.schemas.precheck import PrecheckItem
from app.services.experiments_store import list_experiments
from app.services.file_resolver import resolve_files


def _name(path: Path | None) -> str | None:
    return path.name if path is not None else None


def precheck(settings: Settings, data_dir: Path, exp_ids: list[int]) -> list[PrecheckItem]:
    """One item per experiment, in the order of exp_ids."""
    # Read the settings file once, not once per experiment.
    registered = {exp.exps: exp for exp in list_experiments(data_dir)}

    items = []
    for exp_id in exp_ids:
        exp = registered.get(exp_id)
        if exp is None:
            items.append(
                PrecheckItem(
                    exp_id=exp_id,
                    registered=False,
                    no_skip=None,
                    video=None,
                    trajectories=None,
                    illumination=None,
                    ready=False,
                    reason="not registered",
                )
            )
            continue

        files = resolve_files(settings, data_dir, exp)
        if not exp.no_skip:
            reason = "excluded (no_skip = 0)"
        elif files.video is None and files.trajectories is None:
            reason = "no video or trajectories"
        elif files.illumination is None:
            reason = f"no illumination{exp.ill}.tiff"
        else:
            reason = None

        items.append(
            PrecheckItem(
                exp_id=exp_id,
                registered=True,
                no_skip=exp.no_skip,
                video=_name(files.video),
                trajectories=_name(files.trajectories),
                illumination=_name(files.illumination),
                ready=reason is None,
                reason=reason,
            )
        )
    return items
