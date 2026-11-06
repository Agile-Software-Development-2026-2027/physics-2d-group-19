from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.jobs_store import job_dir, read_status
from app.services.plots import PLOT_NAMES

router = APIRouter(prefix="/jobs", tags=["plots"])


@router.get("/{job_id}/plots")
def list_plots(job_id: str) -> list[dict[str, str | None]]:
    data_dir = get_settings().data_dir
    try:
        status = read_status(data_dir, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found") from None

    if status["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not finished")

    plots_dir = job_dir(data_dir, job_id) / "plots"
    errors = status.get("plots") or {}
    items = []
    for name in PLOT_NAMES:
        error = errors.get(name)
        exists = (plots_dir / f"{name}.png").is_file()
        url = f"/api/jobs/{job_id}/plots/{name}.png" if error is None and exists else None
        items.append({"name": name, "url": url, "error": error})
    return items


@router.get("/{job_id}/plots/{filename}")
def get_plot(job_id: str, filename: str) -> FileResponse:
    # Check the name against the known plots before building any path,
    # so a request like ../status.json can never read other files.
    if filename.removesuffix(".png") not in PLOT_NAMES or not filename.endswith(".png"):
        raise HTTPException(status_code=404, detail="Plot not found")

    try:
        path = job_dir(get_settings().data_dir, job_id) / "plots" / filename
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found") from None

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Plot not found")
    return FileResponse(path, media_type="image/png")
