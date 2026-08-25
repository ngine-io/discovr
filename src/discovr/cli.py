"""Command line entrypoint: ``discovr``."""

import argparse

import uvicorn

from discovr import __version__
from discovr.config import get_settings


def main(argv: list[str] | None = None) -> None:
    """Run the service discovery API with uvicorn."""
    settings = get_settings()

    parser = argparse.ArgumentParser(prog="discovr", description=settings.app_name)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--host", default=settings.host, help="Address to bind to.")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to.")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes.")
    parser.add_argument("--reload", action="store_true", help="Reload on code changes.")
    args = parser.parse_args(argv)

    uvicorn.run(
        "discovr.main:app",
        host=args.host,
        port=args.port,
        workers=None if args.reload else args.workers,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
