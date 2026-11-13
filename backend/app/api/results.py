from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.jobs_store import job_dir, read_status
from app.services.results import RESULT_NAMES

router = APIRouter(prefix="/jobs", tags=["results"])


@router.get("/{job_id}/results")
def list_results(job_id: str) -> list[dict[str, str | None]]:
    data_dir = get_settings().data_dir
    try:
        status = read_status(data_dir, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found") from None

    if status["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not finished")

    results_dir = job_dir(data_dir, job_id) / "results"
    items = []

    for name in RESULT_NAMES:
        exists = (results_dir / f"{name}.csv").is_file()
        url = f"/api/jobs/{job_id}/results/{name}.csv" if exists else None
        items.append({"name": name, "url": url})
    return items


@router.get("/{job_id}/results/{filename}")
def get_result(job_id: str, filename: str) -> FileResponse:
    # Check the name against the known results before building any path,
    # so a request like ../status.json can never read other files.
    if filename.removesuffix(".csv") not in RESULT_NAMES or not filename.endswith(".csv"):
        raise HTTPException(status_code=404, detail="Result not found")

    try:
        path = job_dir(get_settings().data_dir, job_id) / "results" / filename
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found") from None

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Result not found")
    return FileResponse(path, media_type="text/csv", filename=filename)
