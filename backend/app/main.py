from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, experiments, health, history, jobs, params, preview, upload
from app.api.deps import get_current_user
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Moving Chlamydomonas API",
        version="0.1.0",
        description="API contract and backend for Moving Chlamydomonas MVP",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    app.include_router(health.router, prefix="/api")

    # API routers
    app.include_router(auth.router, prefix="/api")
    app.include_router(experiments.router, prefix="/api")
    app.include_router(upload.router, prefix="/api")
    app.include_router(preview.router, prefix="/api")
    app.include_router(params.router, prefix="/api")
    app.include_router(
        jobs.router,
        prefix="/api",
        dependencies=[Depends(get_current_user)],
    )
    app.include_router(history.router, prefix="/api")

    return app


app = create_app()
