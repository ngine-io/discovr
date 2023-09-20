from fastapi import APIRouter

from . import cloudscale_ch, cloudstack, exoscale

api_router = APIRouter()
api_router.include_router(cloudscale_ch.router, prefix="/cloudscale-ch", tags=["cloudscale.ch"])
api_router.include_router(exoscale.router, prefix="/exoscale", tags=["exoscale"])
api_router.include_router(cloudstack.router, prefix="/cloudstack", tags=["cloudstack"])
