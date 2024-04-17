import hashlib
import json
import logging

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from ..conf import settings
from ..core import auth
from ..helpers import consts
from ..helpers.aws import AWSServiceAdapter, client_s3

logger = logging.getLogger(__name__)
router = APIRouter()


class TaskScheduleModel(BaseModel):
    task_name: str
    task_params: dict
    task_skip_cache: bool = False


def get_task_id(task_name, task_params):
    sig = {"task_name": task_name, "task_params": task_params}
    return hashlib.md5(
        json.dumps(sig, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@router.post("/tasks/schedule", tags=["tasks"], response_class=ORJSONResponse)
async def handler_task_schedule(
    task: TaskScheduleModel, key: str = Depends(auth.api_key_header_scheme)
):
    """
    later on results can be fetched by:
    1. using S3 presigned task_results_url
    2. using task_id to call /tasks/{task_id}/status API
    """
    auth.check(value=key)
    try:
        task_id = get_task_id(task.task_name, task.task_params)

        aws = AWSServiceAdapter()
        should_use_cache = not task.task_skip_cache and aws.s3_check_key_exists(
            bucket=settings.JOBS_BUCKET, key=aws.key_results(task_id)
        )
        if should_use_cache:
            task_results_url = aws.s3_generate_presigned_url(
                bucket=settings.JOBS_BUCKET, key=aws.key_results(task_id)
            )
            logger.info(f"Served {task.task_name} task results from cache. {task_id=}")
        else:
            url = aws.sqs_get_queue_url(settings.JOBS_QUEUE_NAME)
            message = {
                "task_id": task_id,
                "task_name": task.task_name,
                "task_params": task.task_params,
            }
            aws.s3_put_json_obj(
                bucket=settings.JOBS_BUCKET,
                key=aws.key_results(task_id),
                message={"status": consts.TaskStatus.SCHEDULED, "results": None},
            )
            r = aws.sqs_send_json_message(queue_url=url, message=message)

            if settings.use_localstack:
                logger.info(f"[LOCALSTACK] Running using local executor {message=}")
                from ..handlers.tasks.jobs import async_handler as executor
                from ..handlers.tasks.jobs import get_sqs_mock_data

                await executor(*get_sqs_mock_data(**message))

            task_results_url = aws.s3_generate_presigned_url(
                bucket=settings.JOBS_BUCKET, key=aws.key_results(task_id)
            )
            logger.info(
                f"Successfully scheduled message with id={r['MessageId']}, "
                f"body={task.model_dump_json()}, queue={settings.JOBS_QUEUE_NAME}"
            )
    except ClientError as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=400)

    return {"task_id": task_id, "task_results_url": task_results_url}


@router.get("/tasks/{task_id}/status", tags=["tasks"], response_class=ORJSONResponse)
async def handler_task_status(task_id, key: str = Depends(auth.api_key_header_scheme)):
    """
    For computation heavy jobs rely on presigned url returned as task_results_url
    - its contents are served by S3 and are gzipped which makes it more handy.
    """
    auth.check(value=key)
    obj = None

    try:
        aws = AWSServiceAdapter()
        obj = aws.s3_get_json_obj(
            bucket=settings.JOBS_BUCKET, key=aws.key_results(task_id)
        )
        logger.info(
            f"Successfully downloaded results for task_id={task_id} "
            f"from bucket={settings.JOBS_BUCKET}"
        )
    except client_s3.exceptions.NoSuchKey:
        logger.info(f"Results for task_id={task_id} are not available")
    except ClientError as e:
        logger.error(e, exc_info=True)

    return {
        "task_id": task_id,
        "bucket": settings.JOBS_BUCKET,
        "processed": obj is not None,
        "meta": {"results": None, "status": consts.TaskStatus.NOT_STARTED}
        if not obj
        else obj,
    }
