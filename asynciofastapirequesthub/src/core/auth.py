from fastapi import HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from ..conf import settings

api_key_header_scheme = APIKeyHeader(name=settings.API_KEY_HEADER_NAME)


def check(value):
    if not value == settings.API_KEY_HEADER_VALUE:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
