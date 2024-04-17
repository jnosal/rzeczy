from fastapi import APIRouter, Depends

from ..conf import settings
from ..core import auth

router = APIRouter()


@router.get("/status", tags=["status"])
async def get_status(key: str = Depends(auth.api_key_header_scheme)):
    auth.check(value=key)
    return {
        "VERSION": "1.1.0",
        "ENV_NAME": settings.ENV_NAME,
        "AWS_REGION": settings.DEFAULT_AWS_REGION,
        "DEFAULT_LOCALSTACK_URL": settings.DEFAULT_LOCALSTACK_URL,
        "SENTRY_DSN": settings.SENTRY_DSN,
    }
