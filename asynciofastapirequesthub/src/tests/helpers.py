from ..conf import settings


def get_auth_headers():
    return {settings.API_KEY_HEADER_NAME: settings.API_KEY_HEADER_VALUE}
