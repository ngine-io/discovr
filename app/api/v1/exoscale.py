from typing import List

import jmespath
import requests
from exoscale_auth import ExoscaleV2Auth
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from starlette.exceptions import HTTPException

from app.model.exoscale import Zone
from app.model.sd import Response

router = APIRouter()

format_json = """
    [].{
        "id": "id",
        "name": "name",
        "labels": "labels",
        "public_ipv4": "public-ip",
        "private_networks": "private-networks",
        "public_ipv6": "ipv6-address",
        "state": "state"
    }
"""

security = HTTPBearer(
    scheme_name="Exoscale API <key>:<secret>",
    bearerFormat="Bearer",
    description="Exoscale read-only <key>:<secret> token"
)

@router.get(
    "",
    response_model=List[Response],
    status_code=200,
        responses={
        500: {},
        400: {},
        401: {},
        403: {},
    },

)
def exoscale(zone: Zone = Zone.CH_GVA_2, token: HTTPAuthorizationCredentials = Depends(security)):
        if ":" not in token.credentials:
            raise HTTPException(status_code=400, detail="Unexptected token format, sould be <key>:<secret>")

        try:
            user, secret = tuple(token.credentials.split(":", 1))

            auth = ExoscaleV2Auth(user, secret)
            response = requests.get(f"https://api-{zone.value}.exoscale.com/v2/instance", auth=auth)
            instance_api_response: dict = response.json()
            instances: list = jmespath.search(format_json, instance_api_response.get("instances", list()))

            result: list = []
            for instance in instances:
                private_networks: list = instance.get("private_networks", list())
                if private_networks:
                    del instance["private_networks"]
                    for private_network in private_networks:
                        private_network_id: str = private_network["id"]
                        response = requests.get(f"https://api-{zone.value}.exoscale.com/v2/private-network/{private_network_id}", auth=auth)
                        private_network_api_response: dict = response.json()
                        private_network_name: str = private_network_api_response["name"]
                        leases: list = private_network_api_response.get("leases", list())
                        for lease in leases:
                            if lease.get("instance-id") == instance["id"]:
                                instance[f"private_network_{private_network_name}_ip"] = lease.get("ip")

                for tag_key, tag_value in instance["labels"].items():
                    instance[f"label_{tag_key}"] = tag_value
                del instance["labels"]

                instance["zone"] = zone.value

                labels = { f"__meta_exoscale_{k}": str(v) for k, v in instance.items() }

                target = f"{instance['public_ipv4']}:9100"

                response = Response(
                    targets=[target],
                    labels=labels,
                )

                result.append(response)
            return result

        except Exception as e:
            logger.error(f"{e}")
            raise HTTPException(status_code=500, detail=f"{e}")
