import os
import secrets
from typing import Dict, List

from pydantic import computed_field
from pydantic_settings import BaseSettings

env = os.getenv("ENV_NAME", "local")


class Settings(BaseSettings):
    DEFAULT_AWS_REGION: str = "test"
    DEFAULT_LOCALSTACK_URL: str = ""
    DEBUG: bool = False
    ENV_NAME: str = "local"
    API_PREFIX: str = "/api"
    API_KEY_HEADER_VALUE: str = secrets.token_urlsafe(32)
    API_KEY_HEADER_NAME: str = "X-GPH-Auth"
    BACKEND_CORS_ORIGINS: List[int] = []
    PROJECT_NAME: str = "Provider Hub"
    JOBS_QUEUE_NAME: str = f"ProviderHubApiJobsQueue{env}"
    JOBS_BUCKET: str = f"provider-hub-api-jobs-{env}"
    JOBS_RESULTS_EXPIRE: int = 3600 * 24

    AMADEUS_API_KEY: str = "<key>"
    AMADEUS_API_SECRET: str = "<secret>"
    AMADEUS_API_URL: str = "https://travel.api.amadeus.com"

    # theoretical limit is 150, but let's keep a slight buffer,
    # see also taskJobsHandler reservedConcurrency
    AMADEUS_MAX_REQUESTS_AT_ONCE: int = 70
    AMADEUS_MAX_REQUESTS_PER_SECOND: int = 70

    LOG_CONFIG: Dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s][%(levelname)s] %(name)s: %(message)s "
                "(%(filename)s:%(lineno)d)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "null": {"class": "logging.NullHandler"},
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "INFO", "propagate": True},
            "httpx": {"handlers": ["default"], "level": "CRITICAL", "propagate": True},
            "httpcore": {
                "handlers": ["default"],
                "level": "CRITICAL",
                "propagate": True,
            },
        },
    }
    SENTRY_DSN: str = ""
    SENTRY_SAMPLE_RATE: float = 1.0
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    @computed_field
    @property
    def use_localstack(self) -> bool:
        return self.ENV_NAME == "local" and bool(self.DEFAULT_LOCALSTACK_URL)

    class Config:
        case_sensitive = True


class TestSettings(Settings):
    LOG_CONFIG: Dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s][%(levelname)s] %(name)s: %(message)s "
                "(%(filename)s:%(lineno)d)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "null": {"class": "logging.NullHandler"},
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "CRITICAL", "propagate": True},
        },
    }


class LocalSettings(Settings):
    LOG_CONFIG: Dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s][%(levelname)s] %(name)s: %(message)s "
                "(%(filename)s:%(lineno)d)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "null": {"class": "logging.NullHandler"},
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
            "httpx": {"handlers": ["default"], "level": "CRITICAL", "propagate": True},
            "httpcore": {
                "handlers": ["default"],
                "level": "CRITICAL",
                "propagate": True,
            },
            "urllib3": {
                "handlers": ["default"],
                "level": "CRITICAL",
                "propagate": True,
            },
            "botocore": {
                "handlers": ["default"],
                "level": "CRITICAL",
                "propagate": True,
            },
        },
    }


def get_settings():
    config_type = {"test": TestSettings(), "local": LocalSettings()}
    return config_type.get(env, Settings())


settings: Settings = get_settings()
