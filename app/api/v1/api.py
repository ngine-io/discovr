from fastapi import APIRouter

from . import cloudscale_ch

api_router = APIRouter()
api_router.include_router(cloudscale_ch.router, prefix="/cloudscale-ch", tags=["cloudscale.ch"])
