"""Service discovery for Exoscale compute instances."""

from enum import Enum
from typing import Annotated, Any

import jmespath
import requests
from exoscale_auth import ExoscaleV2Auth
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security.http import HTTPAuthorizationCredentials
from loguru import logger

from discovr.models import ERROR_RESPONSES, NODE_EXPORTER_PORT, Target
from discovr.security import bearer_scheme, split_key_secret

router = APIRouter()

#: Seconds to wait for a response from the Exoscale API.
TIMEOUT = 30


class Zone(str, Enum):
    """Exoscale zones serving the compute API."""

    CH_GVA_2 = "ch-gva-2"
    CH_DK_2 = "ch-dk-2"
    DE_FRA_1 = "de-fra-1"
    DE_MUC_1 = "de-muc-1"
    AT_VIE_1 = "at-vie-1"
    AT_VIE_2 = "at-vie-2"
    BG_SOF_1 = "bg-sof-1"


security = bearer_scheme(
    scheme_name="Exoscale API <key>:<secret>",
    description="Exoscale read-only <key>:<secret> token",
)

INSTANCE_QUERY = jmespath.compile("""
    [].{
        "id": id,
        "name": name,
        "labels": labels,
        "public_ipv4": "public-ip",
        "private_networks": "private-networks",
        "public_ipv6": "ipv6-address",
        "state": state
    }
""")


def _get(session: requests.Session, url: str) -> dict[str, Any]:
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _private_network_leases(
    session: requests.Session, zone: Zone, network_id: str
) -> tuple[str, dict[str, str]]:
    """Return a private network's name and its ``instance id -> ip`` mapping."""
    network = _get(
        session, f"https://api-{zone.value}.exoscale.com/v2/private-network/{network_id}"
    )
    leases = {
        lease["instance-id"]: lease["ip"]
        for lease in network.get("leases") or []
        if lease.get("instance-id") and lease.get("ip")
    }
    return network["name"], leases


@router.get(
    "",
    summary="Discover Exoscale instances",
    response_model=list[Target],
    responses=ERROR_RESPONSES | {502: {"description": "Exoscale API unreachable"}},
)
def exoscale(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    zone: Annotated[Zone, Query(description="Zone to list instances in.")] = Zone.CH_GVA_2,
) -> list[Target]:
    """Return every Exoscale instance in a zone as a Prometheus service discovery target."""
    key, secret = split_key_secret(token)

    try:
        with requests.Session() as session:
            session.auth = ExoscaleV2Auth(key, secret)
            instances = _get(session, f"https://api-{zone.value}.exoscale.com/v2/instance")
            parsed = INSTANCE_QUERY.search(instances.get("instances") or []) or []

            targets: list[Target] = []
            for instance in parsed:
                labels = instance.pop("labels", None) or {}
                private_networks = instance.pop("private_networks", None) or []
                public_ipv4 = instance.get("public_ipv4")

                if not public_ipv4:
                    logger.warning(
                        "Skipping Exoscale instance {} without a public address",
                        instance.get("name"),
                    )
                    continue

                for network in private_networks:
                    network_name, leases = _private_network_leases(session, zone, network["id"])
                    if address := leases.get(instance["id"]):
                        instance[f"private_network_{network_name}_ip"] = address

                for label_key, label_value in labels.items():
                    instance[f"label_{label_key}"] = label_value

                instance["zone"] = zone.value

                targets.append(
                    Target(
                        targets=[f"{public_ipv4}:{NODE_EXPORTER_PORT}"],
                        labels={
                            f"__meta_exoscale_{name}": str(value)
                            for name, value in instance.items()
                        },
                    )
                )
    except requests.HTTPError as exc:
        logger.error("Exoscale API error: {}", exc)
        raise HTTPException(
            status_code=exc.response.status_code, detail=f"Exoscale: {exc}"
        ) from exc
    except requests.RequestException as exc:
        logger.error("Exoscale request failed: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Exoscale: {exc}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected Exoscale error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{exc}"
        ) from exc

    return targets
