"""Models shared by all service discovery endpoints."""

from pydantic import BaseModel, Field


class Target(BaseModel):
    """A single entry of a Prometheus ``http_sd_config`` response.

    See https://prometheus.io/docs/prometheus/latest/http_sd/ for the format.
    """

    targets: list[str] = Field(description="Target addresses, as ``<host>:<port>``.")
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Metadata labels attached to every target in this entry.",
    )


#: Port the Prometheus node_exporter listens on by default.
NODE_EXPORTER_PORT = 9100

#: Error responses documented on every provider endpoint.
ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {"description": "Malformed request or credentials"},
    401: {"description": "Missing or rejected credentials"},
    403: {"description": "Credentials lack the required permissions"},
    500: {"description": "Upstream provider error"},
}
