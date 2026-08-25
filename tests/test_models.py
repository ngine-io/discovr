"""Tests for the service discovery response model."""

from discovr.models import Target


def test_labels_default_to_empty() -> None:
    assert Target(targets=["10.0.0.1:9100"]).labels == {}


def test_serialises_to_the_prometheus_http_sd_shape() -> None:
    target = Target(targets=["10.0.0.1:9100"], labels={"__meta_exoscale_zone": "ch-gva-2"})
    assert target.model_dump() == {
        "targets": ["10.0.0.1:9100"],
        "labels": {"__meta_exoscale_zone": "ch-gva-2"},
    }
