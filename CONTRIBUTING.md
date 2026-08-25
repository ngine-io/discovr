# Contributing

Thanks for taking the time to contribute.

## Getting started

```sh
uv sync
uv run pytest
```

## Before opening a pull request

```sh
uv run ruff format .
uv run ruff check .
uv run pytest
```

CI runs the same checks against Python 3.10–3.13.

## Adding a provider

Each provider is a self-contained module in [`src/discovr/api/v1/`](src/discovr/api/v1/) that:

1. declares a bearer security scheme via `discovr.security.bearer_scheme`,
2. queries the provider API and maps instances to `discovr.models.Target`,
3. prefixes its metadata labels with `__meta_<provider>_`.

Register the new router in [`src/discovr/api/v1/router.py`](src/discovr/api/v1/router.py) and add
it to the table in the README.

## Releasing

Bump `version` in `pyproject.toml`, then push a matching `vX.Y.Z` tag. That publishes the package to
PyPI and the container image to GHCR.

By contributing you agree that your contributions are licensed under the
[Apache-2.0](LICENSE) license.
