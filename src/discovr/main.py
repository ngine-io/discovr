"""Application factory and ASGI entrypoint."""

import sys

from fastapi import FastAPI
from loguru import logger

from discovr import __version__
from discovr.api.v1.router import router as v1_router
from discovr.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application."""
    settings = settings or get_settings()

    logger.remove()
    logger.add(sys.stderr, level=settings.log_level.upper())
    logger.debug("Starting {name} {version}", name=settings.app_name, version=__version__)

    prefix = settings.url_prefix.rstrip("/")

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        openapi_url=f"{prefix}/openapi.json",
        docs_url=f"{prefix}/",
    )
    app.include_router(v1_router, prefix=f"{prefix}/v1")
    return app


app = create_app()
