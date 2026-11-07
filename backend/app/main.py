from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.types import Scope

from app.api import auth, experiments, health, history, jobs, params, plots, preview, upload
from app.api.deps import get_current_user
from app.config import get_settings

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class SPAStaticFiles(StaticFiles):
    """Serve build files, falling back only for extensionless SPA navigation."""

    async def get_response(self, path: str, scope: Scope):
        parts = Path(path).parts
        if (
            (parts and parts[0] == "api")
            or ".." in Path(scope["path"]).parts
            or "\\" in path
            or "\x00" in path
            or not (Path(self.directory) / path).resolve().is_relative_to(self.directory)
        ):
            raise HTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if (
                exc.status_code != 404
                or any("." in part for part in parts)
                or (parts and parts[0] == "assets")
            ):
                raise
            return await super().get_response("index.html", scope)


def create_app(*, frontend_dist: Path | None = None) -> FastAPI:
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
        history.router,
    ]
    for router in protected_routers:
        app.include_router(
            router,
            prefix="/api",
            dependencies=[Depends(get_current_user)],
        )

    dist = (frontend_dist if frontend_dist is not None else FRONTEND_DIST).resolve()
    index = dist / "index.html"
    if index.is_file() and index.resolve().is_relative_to(dist):
        app.mount("/", SPAStaticFiles(directory=dist), name="frontend")

    return app


app = create_app()
