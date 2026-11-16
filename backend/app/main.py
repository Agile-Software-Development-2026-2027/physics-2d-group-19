from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    experiments,
    health,
    history,
    jobs,
    params,
    plots,
    preview,
    results,
    upload,
)
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

    # Authentication (login is public; /me has its own dependency)
    app.include_router(auth.router, prefix="/api")

    # Protected API routers
    protected_routers = [
        experiments.router,
        upload.router,
        preview.router,
        params.router,
        jobs.router,
        plots.router,
        results.router,
        history.router,
    ]
    for router in protected_routers:
        app.include_router(
            router,
            prefix="/api",
            dependencies=[Depends(get_current_user)],
        )

    return app


app = create_app()
