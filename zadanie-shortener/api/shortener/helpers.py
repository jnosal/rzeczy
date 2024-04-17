import random
import string

from django.conf import settings


def get_random_identifier():
    alphabet = string.ascii_letters + string.digits
    system = random.SystemRandom()
    return "".join(
        system.choice(alphabet) for _ in range(settings.SHORTENING_SIGNATURE_LENGTH)
    ).upper()
