"""Service discovery for CloudStack virtual machines."""

from typing import Annotated

import jmespath
from cs import CloudStack, CloudStackApiException
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security.http import HTTPAuthorizationCredentials
from loguru import logger

from discovr.models import ERROR_RESPONSES, NODE_EXPORTER_PORT, Target
from discovr.security import bearer_scheme, split_key_secret

router = APIRouter()

security = bearer_scheme(
    scheme_name="CloudStack API <key>:<secret>",
    description="CloudStack read-only <key>:<secret> token",
)

INSTANCE_QUERY = jmespath.compile("""
    [].{
        "id": id,
        "name": name,
        "display_name": displayname,
        "tags": tags[].{"key": key, "value": value},
        "default_ip": nic[?isdefault].ipaddress | [0],
        "state": state,
        "vpc_id": vpcid,
        "pod_id": podid,
        "zone": zonename,
        "account": account,
        "os": osdisplayname,
        "memory": memory,
        "cpus": cpunumber,
        "service_offering": serviceofferingname
    }
""")


@router.get(
    "",
    summary="Discover CloudStack virtual machines",
    response_model=list[Target],
    responses=ERROR_RESPONSES,
)
def cloudstack(  # noqa: PLR0913, PLR0917 - each parameter maps to a CloudStack API filter
    endpoint: Annotated[str, Query(description="CloudStack API endpoint URL.")],
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    account: Annotated[str | None, Query(description="Limit to this account.")] = None,
    project_id: Annotated[str | None, Query(description="Limit to this project.")] = None,
    vpc_id: Annotated[str | None, Query(description="Limit to this VPC.")] = None,
    zone_id: Annotated[str | None, Query(description="Limit to this zone.")] = None,
    pod_id: Annotated[str | None, Query(description="Limit to this pod.")] = None,
    name: Annotated[str | None, Query(description="Limit to machines with this name.")] = None,
    list_all: Annotated[
        bool, Query(description="List resources of all accessible accounts.")
    ] = False,
) -> list[Target]:
    """Return matching CloudStack virtual machines as Prometheus service discovery targets."""
    key, secret = split_key_secret(token)

    try:
        client = CloudStack(endpoint=endpoint, key=key, secret=secret)
        instances = client.listVirtualMachines(
            account=account,
            projectid=project_id,
            zoneid=zone_id,
            vpcid=vpc_id,
            podid=pod_id,
            name=name,
            listall=list_all,
            fetch_list=True,
        )
    except CloudStackApiException as exc:
        logger.error("CloudStack API error: {}", exc)
        raise HTTPException(
            status_code=exc.error.get("errorcode", status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="CloudStack: {}".format(exc.error.get("errortext", exc)),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected CloudStack error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{exc}"
        ) from exc

    targets: list[Target] = []
    for instance in INSTANCE_QUERY.search(instances or []) or []:
        tags = instance.pop("tags", None) or []
        default_ip = instance.get("default_ip")

        if not default_ip:
            logger.warning(
                "Skipping CloudStack instance {} without a default NIC address",
                instance.get("name"),
            )
            continue

        for tag in tags:
            instance[f"tag_{tag['key']}"] = tag["value"]

        targets.append(
            Target(
                targets=[f"{default_ip}:{NODE_EXPORTER_PORT}"],
                labels={
                    f"__meta_cloudstack_{label}": str(value) for label, value in instance.items()
                },
            )
        )

    return targets
