"""Service discovery for cloudscale.ch servers."""

from typing import Annotated

import jmespath
from cloudscale import Cloudscale, CloudscaleApiException
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security.http import HTTPAuthorizationCredentials
from loguru import logger

from discovr.models import ERROR_RESPONSES, NODE_EXPORTER_PORT, Target
from discovr.security import bearer_scheme

router = APIRouter()

security = bearer_scheme(
    scheme_name="cloudscale.ch API token",
    description="cloudscale.ch read-only API token",
)

SERVER_QUERY = jmespath.compile("""
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
""")


@router.get(
    "",
    summary="Discover cloudscale.ch servers",
    response_model=list[Target],
    responses=ERROR_RESPONSES,
)
def cloudscale_ch(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    filter_tag: Annotated[
        str | None, Query(description="Only return servers carrying this tag.")
    ] = None,
) -> list[Target]:
    """Return every cloudscale.ch server as a Prometheus service discovery target."""
    try:
        client = Cloudscale(api_token=token.credentials)
        servers = client.server.get_all(filter_tag=filter_tag)
    except CloudscaleApiException as exc:
        logger.error("cloudscale.ch API error: {}", exc)
        raise HTTPException(status_code=exc.status_code, detail=f"cloudscale.ch: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected cloudscale.ch error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{exc}"
        ) from exc

    targets: list[Target] = []
    for server in SERVER_QUERY.search(servers) or []:
        public_ips = server.pop("public_ips", None) or []
        private_ips = server.pop("private_ips", None) or []
        tags = server.pop("tags", None) or {}

        if not public_ips:
            logger.warning(
                "Skipping cloudscale.ch server {} without a public address", server.get("name")
            )
            continue

        for key, value in tags.items():
            server[f"tag_{key}"] = value
        for index, address in enumerate(public_ips, start=1):
            server[f"public_ip_{index}"] = address
        for index, address in enumerate(private_ips, start=1):
            server[f"private_ip_{index}"] = address

        targets.append(
            Target(
                targets=[f"{public_ips[0]}:{NODE_EXPORTER_PORT}"],
                labels={f"__meta_cloudscale_{key}": str(value) for key, value in server.items()},
            )
        )

    return targets
