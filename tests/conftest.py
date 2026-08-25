"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from discovr.config import Settings
from discovr.main import create_app


@pytest.fixture
def client() -> TestClient:
    """A test client for a freshly built application."""
    return TestClient(create_app(Settings(url_prefix="", log_level="WARNING")))
