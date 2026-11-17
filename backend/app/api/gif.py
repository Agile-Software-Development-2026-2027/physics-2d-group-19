import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.jobs_store import job_dir, read_status

router = APIRouter(prefix="/jobs", tags=["gif"])


def _gif_dir(job_id: str) -> Path:
    """The job's gif/ folder: 404 for an unknown job, 409 until the job is done."""
    data_dir = get_settings().data_dir
    try:
        status = read_status(data_dir, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found") from None

    if status["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not finished")
    if status.get("gif_error"):
        raise HTTPException(status_code=404, detail="GIF generation failed")
    return job_dir(data_dir, job_id) / "gif"


@router.get("/{job_id}/gif")
def get_gif(job_id: str) -> FileResponse:
    gif_path = _gif_dir(job_id) / "trajectories.gif"
    if not gif_path.is_file():
        raise HTTPException(status_code=404, detail="GIF not found")
    return FileResponse(gif_path, media_type="image/gif")


@router.get("/{job_id}/gif/frames")
def get_frames(job_id: str) -> FileResponse:
    frames_json = _gif_dir(job_id) / "frames.json"
    if not frames_json.is_file():
        raise HTTPException(status_code=404, detail="Frames not found")
    return FileResponse(frames_json, media_type="application/json")


@router.get("/{job_id}/gif/frames/{filename}")
def get_frame(job_id: str, filename: str) -> FileResponse:
    gif_dir = _gif_dir(job_id)

    # Only "<i>.png" with 0 <= i < count is accepted, checked before building
    # the path, so names like ../status.json never touch the disk.
    index = filename.removesuffix(".png")
    if not filename.endswith(".png") or not index.isdigit():
        raise HTTPException(status_code=404, detail="Frame not found")

    frames_json = gif_dir / "frames.json"
    if not frames_json.is_file():
        raise HTTPException(status_code=404, detail="Frames not found")
    count = json.loads(frames_json.read_text(encoding="utf-8"))["count"]
    if int(index) >= count:
        raise HTTPException(status_code=404, detail="Frame not found")

    frame_path = gif_dir / "frames" / f"{int(index)}.png"
    if not frame_path.is_file():
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(frame_path, media_type="image/png")
