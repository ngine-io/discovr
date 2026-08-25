"""discovr — HTTP service discovery for Prometheus, backed by cloud provider APIs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("discovr-ngine")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
