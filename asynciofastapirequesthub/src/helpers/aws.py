import gzip
import io
import json
import logging

import boto3
import orjson
from botocore.client import Config
from botocore.exceptions import ClientError

from ..conf import settings
from ..helpers.utils import bytesto

logger = logging.getLogger(__name__)


if settings.use_localstack:
    client_s3 = boto3.client(
        "s3",
        region_name=settings.DEFAULT_AWS_REGION,
        endpoint_url=settings.DEFAULT_LOCALSTACK_URL,
    )
    client_sqs = boto3.client(
        "sqs",
        region_name=settings.DEFAULT_AWS_REGION,
        endpoint_url=settings.DEFAULT_LOCALSTACK_URL,
    )
else:
    client_s3 = boto3.client(
        "s3",
        region_name=settings.DEFAULT_AWS_REGION,
        endpoint_url=f"https://s3.{settings.DEFAULT_AWS_REGION}.amazonaws.com",
    )
    client_sqs = boto3.client("sqs", region_name=settings.DEFAULT_AWS_REGION)


class AWSServiceAdapter:
    def key_results(self, task_id):
        return f"{task_id}-results"

    def sqs_get_messages(self, event):
        return [
            {
                "attributes": record["attributes"],
                "id": record["messageId"],
                "body": orjson.loads(record["body"]),
            }
            for record in event["Records"]
        ]

    def sqs_get_queue_url(self, name: str):
        r = client_sqs.get_queue_url(QueueName=name)
        return r["QueueUrl"]

    def sqs_send_json_message(self, queue_url, message):
        return client_sqs.send_message(
            QueueUrl=queue_url, MessageBody=orjson.dumps(message).decode("utf-8")
        )

    def s3_get_obj(self, bucket, key):
        return client_s3.get_object(Bucket=bucket, Key=key)

    def s3_get_json_obj(self, bucket, key, gzipped=True):
        r = client_s3.get_object(Bucket=bucket, Key=key)

        if not gzipped:
            content = r["Body"]
            return orjson.loads(content.read())

        buff = io.BytesIO(r["Body"].read())
        with gzip.GzipFile(fileobj=buff, mode="rb") as fh:
            return json.load(fh)

    def s3_put_json_obj(self, bucket, key, message, gzipped=True):
        if not gzipped:
            return client_s3.put_object(
                Body=orjson.dumps(message), Bucket=bucket, Key=key
            )

        total_size_before = round(bytesto(len(orjson.dumps(message)), "m"), 2)

        buff = io.BytesIO()
        with gzip.GzipFile(fileobj=buff, mode="wb") as f:
            with io.TextIOWrapper(f, encoding="utf-8") as wrapper:
                wrapper.write(orjson.dumps(message).decode("utf-8"))
        buff.seek(0)

        total_size_after = round(bytesto(buff.getbuffer().nbytes, "m"), 2)

        logger.info(
            f"[S3] stored {total_size_before}MB json as {total_size_after}MB gzip"
        )

        return client_s3.put_object(Body=buff, Bucket=bucket, Key=key)

    def s3_generate_presigned_url(
        self, bucket, key, expiration=settings.JOBS_RESULTS_EXPIRE
    ):
        return client_s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )

    def s3_check_key_exists(self, bucket, key):
        try:
            client_s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def s3_get_obj_iterator(self, bucket):
        paginator = client_s3.get_paginator("list_objects")
        return paginator.paginate(
            Bucket=bucket,
            Delimiter="/",
            PaginationConfig={"PageSize": None},
        )

    def s3_delete_objects(self, bucket, items):
        return client_s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": i} for i in items], "Quiet": False},
        )
