from typing import List, Optional

import jmespath
from cs import CloudStack, CloudStackApiException
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from starlette.exceptions import HTTPException

from app.model.sd import Response

router = APIRouter()

format_json = """
    [].{
        "id": "id",
        "name": "name",
        "display_name": "displayname",
        "tags": tags[].{"key": key, "value": value},
        "default_ip": nic[?isdefault].ipaddress | [0],
        "state": "state",
        "vpc_id": "vpcid",
        "pod_id": "podid",
        "zone": "zonename",
        "account": "account",
        "os": "osdisplayname",
        "memory": "memory",
        "cpus": "cpunumber",
        "service_offering": "serviceofferingname"
    }
"""

security = HTTPBearer(
    scheme_name="CloudStack API <key>:<secret>",
    bearerFormat="Bearer",
    description="CloudStack read-only <key>:<secret> token"
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
def cloudstack(
    endpoint: str,
    account: Optional[str] = None,
    project_id: Optional[str] = None,
    vpc_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    pod_id: Optional[str] = None,
    name: Optional[str] = None,
    list_all: bool = False,
    token: HTTPAuthorizationCredentials = Depends(security)
    ):
        if ":" not in token.credentials:
            raise HTTPException(status_code=400, detail="Unexptected token format, sould be <key>:<secret>")

        try:
            user, secret = tuple(token.credentials.split(":", 1))

            cs = CloudStack(
                endpoint=endpoint,
                key=user,
                secret=secret,
            )

            instances = cs.listVirtualMachines(
                account=account,
                projectid=project_id,
                zoneid=zone_id,
                vpcid=vpc_id,
                podid=pod_id,
                name=name,
                listall=list_all,
                fetch_list=True,
            )

            result = []
            if instances:
                instances: list = jmespath.search(format_json, instances)
                for instance in instances:

                    for tag in instance['tags']:
                        instance[f"tag_{tag['key']}"] = tag['value']

                    del instance['tags']

                    labels = { f"__meta_cloudstack_{k}": str(v) for k, v in instance.items() }

                    target = f"{instance['default_ip']}:9100"

                    response = Response(
                        targets=[target],
                        labels=labels,
                    )

                    result.append(response)

            return result

        except CloudStackApiException as e:
            logger.error(f"{e}")
            raise HTTPException(status_code=e.error.get("errorcode", 500), detail="CloudStack: {0}".format(e.error.get("errortext", f"{e}")))

        except Exception as e:
            logger.error(f"{e}")
            raise HTTPException(status_code=500, detail=f"{e}")
