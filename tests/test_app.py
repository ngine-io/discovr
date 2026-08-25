"""Tests for the application wiring."""

from fastapi.testclient import TestClient

from discovr import __version__
from discovr.config import Settings
from discovr.main import create_app


def test_openapi_is_served(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["version"] == __version__


def test_all_providers_are_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/v1/cloudscale-ch", "/v1/exoscale", "/v1/cloudstack"}


def test_url_prefix_is_applied() -> None:
    prefixed = TestClient(create_app(Settings(url_prefix="/api")))
    assert prefixed.get("/api/openapi.json").status_code == 200
    assert "/api/v1/exoscale" in prefixed.get("/api/openapi.json").json()["paths"]


def test_endpoints_require_credentials(client: TestClient) -> None:
    for path in ("/v1/cloudscale-ch", "/v1/exoscale"):
        assert client.get(path).status_code == 401
