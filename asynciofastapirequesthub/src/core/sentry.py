import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from ..conf import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[AwsLambdaIntegration()],
        # traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        sample_rate=settings.SENTRY_SAMPLE_RATE,
        max_request_body_size="medium",
        send_default_pii=True,
    )
