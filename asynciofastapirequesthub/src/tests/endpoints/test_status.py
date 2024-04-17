import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from ..helpers import get_auth_headers


@pytest.mark.asyncio
async def test_status_returns_successful_response(async_client: AsyncClient):
    async with async_client:
        r = await async_client.get("/api/status", headers=get_auth_headers())
        data = r.json()

        assert r.status_code == HTTP_200_OK
        assert "ENV_NAME" in data
        assert data["ENV_NAME"] == "test"
        assert "AWS_REGION" in data
        assert data["AWS_REGION"] == "test"
        assert "DEFAULT_LOCALSTACK_URL" in data
        assert data["DEFAULT_LOCALSTACK_URL"] == ""
        assert "SENTRY_DSN" in data
        assert data["SENTRY_DSN"] == ""
