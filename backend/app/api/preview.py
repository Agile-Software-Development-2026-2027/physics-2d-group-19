from fastapi import APIRouter

from app.schemas.preview import PreviewRequest, PreviewResponse

router = APIRouter(prefix="/preview", tags=["preview"])


@router.post("", response_model=PreviewResponse)
def get_frame_preview(req: PreviewRequest) -> PreviewResponse:
    """Mock detection preview endpoint.

    Simulates cell detection on a single frame using provided tracking parameters.
    """
    # Deterministic mock calculation based on diameter and minmass
    mock_detected_cells = max(10, int(300 - req.minmass / 2 + req.diameter * 2))

    return PreviewResponse(
        frame_number=req.frame_number,
        detected_cells=mock_detected_cells,
        image_url=f"/api/preview/frames/{req.frame_number}?diameter={req.diameter}",
        note="Preview uses a sampled background; final tracking may vary slightly",
    )
