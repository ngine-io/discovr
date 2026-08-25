# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first so they stay cached across source changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM docker.io/python:${PYTHON_VERSION}-alpine

LABEL org.opencontainers.image.source="https://github.com/ngine-io/discovr" \
      org.opencontainers.image.description="HTTP service discovery for Prometheus, backed by cloud provider APIs." \
      org.opencontainers.image.licenses="Apache-2.0"

RUN adduser --disabled-password --uid 1001 --shell /sbin/nologin discovr

COPY --from=builder --chown=1001:1001 /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1

USER 1001
EXPOSE 8000/tcp

ENTRYPOINT ["discovr"]
