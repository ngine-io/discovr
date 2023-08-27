import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.v1.api import api_router
from app.log import logger
from app.version import __version__

load_dotenv(verbose=True)

app_name = os.getenv("APP_NAME", "Clouds Service Discovery API")

logger.debug(f"App started: {app_name}")

prefix: str = "/api/v1"

app = FastAPI(
    title=app_name,
    version=__version__,
    openapi_url=f"{prefix}/openapi.json",
    docs_url="/",
)

app.include_router(api_router, prefix=prefix)
