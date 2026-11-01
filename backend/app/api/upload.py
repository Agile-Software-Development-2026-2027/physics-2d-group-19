from fastapi import APIRouter, HTTPException, UploadFile, status

from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/video", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile) -> UploadResponse:
    """Mock video upload endpoint. Accepts only .avi files."""
    filename = file.filename or "unknown.avi"
    if not filename.lower().endswith(".avi"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video format. Only .avi files are supported.",
        )

    # In mock contract, simulate reading size
    content = await file.read()
    size_bytes = len(content) if content else 1024 * 1024

    return UploadResponse(
        filename=filename,
        file_type="video",
        size_bytes=size_bytes,
        message="Video uploaded successfully",
    )


@router.post("/illumination", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_illumination(file: UploadFile) -> UploadResponse:
    """Mock illumination image upload endpoint. Accepts .tiff or .tif files."""
    filename = file.filename or "unknown.tiff"
    if not (filename.lower().endswith(".tiff") or filename.lower().endswith(".tif")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid illumination image format. Only .tiff and .tif files are supported.",
        )

    content = await file.read()
    size_bytes = len(content) if content else 512 * 1024

    return UploadResponse(
        filename=filename,
        file_type="illumination",
        size_bytes=size_bytes,
        message="Illumination image uploaded successfully",
    )
