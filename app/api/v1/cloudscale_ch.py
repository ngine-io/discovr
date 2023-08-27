

from typing import List

import jmespath
from cloudscale import Cloudscale, CloudscaleApiException
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException

from app.log import logger
from app.model.sd import Response

router = APIRouter()

format_json = """
    [].{
        "name": name,
        "image": image.slug,
        "flavor": flavor.slug,
        "vcpu_count": flavor.vcpu_count,
        "memory_gb": flavor.memory_gb,
        "tags": tags,
        "public_ips": interfaces[?type=='public'].addresses[].address,
        "private_ips": interfaces[?type=='private'].addresses[].address,
        "zone": zone.slug,
        "status": status,
        "uuid": uuid
        }
"""

security = HTTPBearer(
    scheme_name="cloudscale.ch API token",
    bearerFormat="Bearer",
    description="cloudscale.ch read-only API token"
)

@router.get(
    "",
    response_model=List[Response],
    status_code=200,
        responses={
        500: {},
        401: {},
        403: {},
    },

)
def cloudscale(token: HTTPAuthorizationCredentials = Depends(security)):
        try:
            client = Cloudscale(
                api_token=token.credentials,
            )

            instances = client.server.get_all()
            instances = jmespath.search(format_json, instances)

            result = []
            for instance in instances:

                for tag_key, tag_value in instance['tags'].items():
                    instance[f"tag_{tag_key}"] = tag_value
                del instance['tags']

                for i, public_ip in enumerate(instance["public_ips"]):
                    instance[f"public_ip_{i + 1}"] = public_ip
                del instance['public_ips']

                for i, private_ip in enumerate(instance['private_ips']):
                    instance[f"private_ip_{i + 1}"] = private_ip
                del instance['private_ips']

                labels = { f"__meta_cloudscale_{k}": str(v) for k, v in instance.items() }

                target = f"{instance['public_ip_1']}:9100"

                response = Response(
                    targets=[target],
                    labels=labels,
                )

                result.append(response)
            return result

        except CloudscaleApiException as e:
            logger.error(f"{e}")
            raise HTTPException(status_code=e.status_code, detail=f"{e}")

        except Exception as e:
            logger.error(f"{e}")
            raise HTTPException(status_code=500, detail=f"{e}")
