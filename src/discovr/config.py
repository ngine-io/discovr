"""Application settings, read from the environment or a local ``.env`` file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Every field can be set through an environment variable of the same name,
    upper-cased (e.g. ``APP_NAME``, ``URL_PREFIX``).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Clouds Service Discovery API"
    url_prefix: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, parsed once."""
    return Settings()
