import asyncio
import logging
import logging.config
import time
import uuid

import orjson

from ...conf import settings
from ...helpers import consts
from ...helpers.aws import AWSServiceAdapter
from ...helpers.utils import bytesto
from .runners import amadeus_preselection

loop = asyncio.get_event_loop()
logger = logging.getLogger(__name__)
logging.config.dictConfig(settings.LOG_CONFIG)


from ...core import sentry


async def run_job(task_id, task_name, task_params):
    handlers = {consts.Tasks.AMADEUS_PRESELECTION: amadeus_preselection.handler}
    return await handlers[task_name](task_id, task_params)


async def async_handler(event, context):
    service = AWSServiceAdapter()
    messages = service.sqs_get_messages(event)
    tic = time.time()
    for message in messages:
        body = message["body"]
        task_id = body["task_id"]
        task_name = body["task_name"]
        task_params = body["task_params"]
        try:
            logger.info(f"[JOB-STARTED] {task_name=}, {task_id=}, {task_params=}")
            service.s3_put_json_obj(
                bucket=settings.JOBS_BUCKET,
                key=service.key_results(task_id),
                message={"status": consts.TaskStatus.PENDING, "results": None},
            )
            results = await run_job(
                task_name=task_name, task_id=task_id, task_params=task_params
            )
        except Exception:
            total_time = f'{float("%.2f" % (time.time() - tic,))}s'
            logger.error(
                f"[JOB-ERROR] after {total_time} {task_name=}, {task_id=}, {task_params=}",
                exc_info=True,
            )
            service.s3_put_json_obj(
                bucket=settings.JOBS_BUCKET,
                key=service.key_results(task_id),
                message={"status": consts.TaskStatus.ERROR, "results": None},
            )
        else:
            total_time = f'{float("%.2f" % (time.time() - tic,))}s'
            total_size = round(bytesto(len(orjson.dumps(results)), "m"), 2)
            logger.info(
                f"[JOB-SUCCESSFUL] after {total_time}, size: {total_size}MB {task_name=}, {task_id=}, {task_params=}"
            )
            service.s3_put_json_obj(
                bucket=settings.JOBS_BUCKET,
                key=service.key_results(task_id),
                message={"status": consts.TaskStatus.READY, "results": results},
            )


def handler(event, context):
    return loop.run_until_complete(async_handler(event, context))


def get_sqs_mock_data(task_id, task_name, task_params=None):
    body = {
        "task_id": task_id,
        "task_name": task_name,
        "task_params": task_params or {},
    }
    mock_event = {
        "Records": [
            {
                "messageId": "883c7223-233e-4d14-b8e9-b4b77f7ff3a1",
                "receiptHandle": "AQEBS8qJkXb2kVD/H3xvapFNO1fmzcsNNnWoV0S2MX6/6Hei7SY3iVmmoWutnFj2rgQ3nhOwVyxBsCwTLhRaCIwMz5pKRn/Z12aulsLaHiZVUDrtQW/CDVZQ+dOt5K5Ya6JDUsUHPUrQJZbHB2WTYge49DGMBeqp1uhDbkLsHXEniNTUxwpQb3c0kjxVKL1qsT5drYaAAzJzrhJ3ceZTAJG3FpJJX/AxkXah6LYcoD8hE641N71bQScmWxoNg7MzKmaKaTr+0U4eTeHBzfKTeNz+SKt9OmPBujPyTzndLSUI8MQTS9PbRdvNVen3vRFW31s/ehhmMeHyjdqfUemO7wh3p9um3DL/yyGoZNd+GyLKJM8IQKSN4akKyO56xJxdgaLioxMupD092wTjDHM8Gfld1Q6JsXAzS93QhCik+LMc0j8=",
                "body": orjson.dumps(body).decode("utf-8"),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "AWSTraceHeader": "Root=1-65e0a2fb-6521427f4163fad0509b28b7;Parent=7e527bd640e29f6a;Sampled=0;Lineage=30bde1ac:0",
                    "SentTimestamp": "1709220606034",
                    "SenderId": "AROAWVDL5ICD6OFMBG6BW:provider-hub-api-stg-WebRouterHandler",
                    "ApproximateFirstReceiveTimestamp": "1709220606039",
                },
                "messageAttributes": {},
                "md5OfBody": "66311ebf4743c05d951ad0565edacc02",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-central-1:457640329351:ProviderHubApiJobsQueuestg",
                "awsRegion": "eu-central-1",
            }
        ]
    }
    mock_context = {}
    return mock_event, mock_context


if __name__ == "__main__":
    logging.getLogger("httpx").setLevel(logging.WARNING)
    handler(
        *get_sqs_mock_data(
            task_id=uuid.uuid4().hex,
            task_name=consts.Tasks.AMADEUS_PRESELECTION,
            task_params={
                "date_from": "2024-04-25",
                "date_to": "2024-05-05",
                "nights_in_dst_from": 7,
                "nights_in_dst_to": 11,
                "passengers_map": {"adults": 5, "children": [16, 14, 9]},
                "fly_from_airports": ["GDN", "WAW", "KRK"],
                "fly_to_airports": ["MLE", "GAN"],
                "return_from_airports": ["MLE", "GAN"],
                "return_to_airports": ["GDN", "WAW", "KRK"],
                "return_from": "2024-05-02",
                "return_to": "2024-05-12",
                "allow_opposite_route": False,
                "currency_code": "PLN",
                "multicity": False,
            },
        )
    )
