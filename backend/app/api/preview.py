import base64

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.params import TrackingParams
from app.schemas.preview import PreviewResponse
from app.services import preview as preview_service
from app.services.uploads import upload_path

router = APIRouter(prefix="/videos", tags=["preview"])

# Missing query values fall back to the lab defaults, kept in one place (3.2).
_DEFAULTS = TrackingParams()


@router.get("/{video_id}/preview", response_model=PreviewResponse)
def get_preview(
    video_id: str,
    frame: int = Query(0, ge=0),
    diameter: int = Query(_DEFAULTS.diameter),
    minmass: int = Query(_DEFAULTS.minmass),
    background_method: str = Query(_DEFAULTS.background_method),
) -> PreviewResponse:
    try:
        params = TrackingParams(
            diameter=diameter, minmass=minmass, background_method=background_method
        )
    except ValidationError as err:
        detail = jsonable_encoder(err.errors(include_url=False, include_context=False))
        raise HTTPException(status_code=422, detail=detail) from None

    try:
        video_path = upload_path(get_settings().data_dir, video_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Video not found") from None

    try:
        image, features = preview_service.detect_frame(video_path, frame, params)
    except ValueError as err:  # frame past the end of the video
        raise HTTPException(status_code=422, detail=str(err)) from None

    png = preview_service.render_png(image, features, params.diameter)
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return PreviewResponse(frame=frame, cell_count=len(features), image=data_url)
