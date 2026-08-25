"""Router aggregating all v1 provider endpoints."""

from fastapi import APIRouter

from discovr.api.v1 import cloudscale_ch, cloudstack, exoscale

router = APIRouter()
router.include_router(cloudscale_ch.router, prefix="/cloudscale-ch", tags=["cloudscale.ch"])
router.include_router(exoscale.router, prefix="/exoscale", tags=["exoscale"])
router.include_router(cloudstack.router, prefix="/cloudstack", tags=["cloudstack"])
