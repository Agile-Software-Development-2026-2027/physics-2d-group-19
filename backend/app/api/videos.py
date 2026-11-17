import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.schemas.videos import VideoUploadResponse
from app.services.tracking import VIDEO_UNREADABLE, check_video
from app.services.uploads import UploadTooLarge, save_upload, upload_path

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("", status_code=201)
def upload_video(
    file: Annotated[UploadFile, File(description="Experiment video (.avi)")],
) -> VideoUploadResponse:
    """Store the video for the preview and the job; the file is never loaded in RAM."""
    settings = get_settings()
    filename = file.filename or ""
    if Path(filename).suffix.lower() != ".avi":
        raise HTTPException(422, "Only .avi files are supported")

    try:
        video_id = save_upload(settings.data_dir, file.file, filename, settings.max_video_bytes)
    except UploadTooLarge:
        # save_upload has already removed the partial file.
        raise HTTPException(413, "The video exceeds the size limit") from None

    path = upload_path(settings.data_dir, video_id)
    try:
        frames, fps = check_video(path)
    except ValueError:
        shutil.rmtree(path.parent, ignore_errors=True)
        raise HTTPException(422, VIDEO_UNREADABLE) from None

    return VideoUploadResponse(
        video_id=video_id,
        filename=filename,
        size_bytes=path.stat().st_size,
        frames=frames,
        fps=fps,
    )
