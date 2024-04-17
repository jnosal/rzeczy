import logging
import logging.config

from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .conf import env, settings
from .core.exceptions import ApiBaseException
from .endpoints.status import router as status_router
from .endpoints.tasks import router as tasks_router

logging.config.dictConfig(settings.LOG_CONFIG)
logger = logging.getLogger(__name__)

from .core import sentry


def init_routers(instance: FastAPI) -> None:
    instance.include_router(status_router, prefix=settings.API_PREFIX)
    instance.include_router(tasks_router, prefix=settings.API_PREFIX)


def init_listeners(instance: FastAPI) -> None:
    @instance.exception_handler(ApiBaseException)
    async def custom_exception_handler(request: Request, exc: ApiBaseException):
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def make_middleware() -> list[Middleware]:
    allow_origins = ["*"]
    if settings.BACKEND_CORS_ORIGINS:
        logger.info(f"Installing CORS Middleware for: {settings.BACKEND_CORS_ORIGINS}")
        allow_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
    return middleware


def create_app() -> FastAPI:
    instance = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        debug=settings.DEBUG,
        middleware=make_middleware(),
    )
    logger.info(f"Initialised app. Environment: {env}")
    init_routers(instance)
    init_listeners(instance)
    return instance


app = create_app()
