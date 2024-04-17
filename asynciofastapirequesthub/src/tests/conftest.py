from typing import Generator

import pytest
from httpx import AsyncClient

from ..main import app


@pytest.fixture(scope="function")
def async_client():
    return AsyncClient(app=app, base_url="http://testserver")
