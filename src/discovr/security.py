"""Authentication helpers shared by the provider endpoints."""

from fastapi import HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer


def bearer_scheme(scheme_name: str, description: str) -> HTTPBearer:
    """Build a bearer token security scheme for a provider."""
    return HTTPBearer(
        scheme_name=scheme_name,
        bearerFormat="Bearer",
        description=description,
    )


def split_key_secret(credentials: HTTPAuthorizationCredentials) -> tuple[str, str]:
    """Split a ``<key>:<secret>`` bearer token into its two parts.

    Raises:
        HTTPException: If the token does not carry both parts.
    """
    key, separator, secret = credentials.credentials.partition(":")
    if not separator or not key or not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unexpected token format, should be <key>:<secret>",
        )
    return key, secret
