import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from ...conf import settings
from ...core import auth


def test_returns_error_for_invalid_header():
    with pytest.raises(HTTPException):
        auth.check("Invalid header value")


def test_passes_with_none_for_valid_value():
    assert auth.check(settings.API_KEY_HEADER_VALUE) is None


@pytest.mark.asyncio
async def test_status_403_if_auth_header_missing(async_client: AsyncClient):
    async with async_client:
        r = await async_client.get("/api/status")
        assert r.status_code == HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_returns_403_if_auth_header_has_invalid_value(async_client: AsyncClient):
    async with async_client:
        r = await async_client.get(
            "/api/status", headers={settings.API_KEY_HEADER_NAME: "invalid"}
        )
        assert r.status_code == HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_auth_is_ok_for_status_endpoint(async_client: AsyncClient):
    async with async_client:
        r = await async_client.get(
            "/api/status",
            headers={settings.API_KEY_HEADER_NAME: settings.API_KEY_HEADER_VALUE},
        )
        assert r.status_code == HTTP_200_OK
