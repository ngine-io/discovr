"""Tests for the shared credential helpers."""

import pytest
from fastapi import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials

from discovr.security import split_key_secret


def credentials(value: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=value)


def test_splits_key_and_secret() -> None:
    assert split_key_secret(credentials("key:secret")) == ("key", "secret")


def test_secret_may_contain_colons() -> None:
    assert split_key_secret(credentials("key:se:cret")) == ("key", "se:cret")


@pytest.mark.parametrize("value", ["", "key", "key:", ":secret", ":"])
def test_rejects_malformed_tokens(value: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        split_key_secret(credentials(value))
    assert exc_info.value.status_code == 400
