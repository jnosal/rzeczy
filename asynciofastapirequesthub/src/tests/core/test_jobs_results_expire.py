from datetime import datetime, timedelta, timezone

import pytest

from ...conf import settings
from ...handlers.tasks.jobs_results_expire import async_handler


@pytest.mark.asyncio
async def test_does_not_delete_when_empty_iterator(mocker):
    mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_get_obj_iterator",
        return_value=[],
    )
    mocked_s3_delete_objects = mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_delete_objects"
    )

    await async_handler(None, None)
    assert mocked_s3_delete_objects.call_count == 0


@pytest.mark.asyncio
async def test_does_not_delete_when_not_expired(mocker):
    mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_get_obj_iterator",
        return_value=[{"Contents": [{"LastModified": datetime.now(timezone.utc)}]}],
    )
    mocked_s3_delete_objects = mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_delete_objects"
    )

    await async_handler(None, None)
    assert mocked_s3_delete_objects.call_count == 0


@pytest.mark.asyncio
async def test_schedules_delete(mocker):
    mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_get_obj_iterator",
        return_value=[
            {
                "Contents": [
                    {
                        "Key": "test-key",
                        "LastModified": datetime.now(timezone.utc)
                        - timedelta(seconds=settings.JOBS_RESULTS_EXPIRE + 1),
                    }
                ]
            }
        ],
    )
    mocked_s3_delete_objects = mocker.patch(
        "src.handlers.tasks.jobs_results_expire.AWSServiceAdapter.s3_delete_objects"
    )

    await async_handler(None, None)
    assert mocked_s3_delete_objects.call_count == 1
    mocked_s3_delete_objects.assert_called_with(
        bucket=settings.JOBS_BUCKET, items=["test-key"]
    )
