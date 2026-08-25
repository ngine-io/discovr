# discovr

[![CI](https://github.com/ngine-io/discovr/actions/workflows/ci.yml/badge.svg)](https://github.com/ngine-io/discovr/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/discovr-ngine)](https://pypi.org/project/discovr-ngine/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

HTTP service discovery for [Prometheus](https://prometheus.io/), backed by cloud provider APIs.

`discovr` exposes one endpoint per provider that returns your running instances in the
[`http_sd_config`](https://prometheus.io/docs/prometheus/latest/http_sd/) format, so Prometheus can
scrape them without a static target list. Provider credentials are never stored: Prometheus passes
them per request as a bearer token, and `discovr` forwards them to the provider API.

Supported providers:

| Provider | Endpoint | Credentials |
| --- | --- | --- |
| [cloudscale.ch](https://www.cloudscale.ch/) | `GET /v1/cloudscale-ch` | API token |
| [Exoscale](https://www.exoscale.com/) | `GET /v1/exoscale` | `<key>:<secret>` |
| [CloudStack](https://cloudstack.apache.org/) | `GET /v1/cloudstack` | `<key>:<secret>` |

Targets are returned on port `9100` (the Prometheus
[node_exporter](https://github.com/prometheus/node_exporter) default). Instance metadata is exposed
as `__meta_<provider>_*` labels; use Prometheus `relabel_configs` to keep the ones you want.

## Install

With [uv](https://docs.astral.sh/uv/):

```sh
uv tool install discovr-ngine
discovr --host 0.0.0.0 --port 8000
```

Or with the container image:

```sh
docker run --rm -p 8000:8000 ghcr.io/ngine-io/discovr:latest
```

Interactive API docs are then served at <http://localhost:8000/>.

## Configure

All settings are optional and read from the environment or a local `.env` file.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `Clouds Service Discovery API` | Title shown in the API docs. |
| `URL_PREFIX` | *(empty)* | Path prefix, e.g. `/api` when running behind a reverse proxy. |
| `HOST` | `127.0.0.1` | Address to bind to. |
| `PORT` | `8000` | Port to bind to. |
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Use with Prometheus

```yaml
scrape_configs:
  - job_name: cloudscale.ch nodes
    http_sd_configs:
      - url: "http://discovr:8000/v1/cloudscale-ch"
        authorization:
          type: Bearer
          credentials: <your-cloudscale-api-token>
```

`discovr` has no authentication of its own — the bearer token is the provider credential. Run it on
a trusted network, or put it behind a reverse proxy that terminates TLS and restricts access. Use a read-only API token of your provider if possible.

A runnable Prometheus setup is in [`sample/`](sample/):

```sh
docker compose up
```

## Develop

```sh
uv sync           # create the virtualenv and install everything
uv run discovr --reload
uv run pytest
uv run ruff check .
uv run ruff format .
```

## License

[Apache-2.0](LICENSE)
