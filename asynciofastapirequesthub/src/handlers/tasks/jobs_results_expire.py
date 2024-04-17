import asyncio
import logging
import logging.config
from datetime import datetime, timezone

from ...conf import settings
from ...helpers.aws import AWSServiceAdapter
from ...helpers.utils import by_chunk

loop = asyncio.get_event_loop()
logger = logging.getLogger(__name__)
logging.config.dictConfig(settings.LOG_CONFIG)


from ...core import sentry


async def async_handler(event, context):
    service = AWSServiceAdapter()
    iterator = service.s3_get_obj_iterator(bucket=settings.JOBS_BUCKET)

    total = 0
    to_delete = []
    now = datetime.now(timezone.utc)

    for data in iterator:
        contents = data.get("Contents")
        if not contents:
            continue

        total += len(contents)

        for el in contents:
            is_key_expired = (
                now - el["LastModified"]
            ).total_seconds() >= settings.JOBS_RESULTS_EXPIRE
            if not is_key_expired:
                continue

            to_delete.append(el["Key"])

    logger.info(f"Total keys: {total}, deleting: {len(to_delete)}")

    if not to_delete:
        return

    for items in by_chunk(to_delete):
        response = service.s3_delete_objects(bucket=settings.JOBS_BUCKET, items=items)
        logger.info(f"Successfully deleted: {len(response['Deleted'])} keys")


def handler(event, context):
    return loop.run_until_complete(async_handler(event, context))


if __name__ == "__main__":
    handler(None, None)
