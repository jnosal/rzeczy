import pytest
from botocore.exceptions import ClientError
from httpx import AsyncClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from ...conf import settings
from ...helpers import consts
from ..helpers import get_auth_headers


@pytest.mark.asyncio
async def test_schedule_task_returns_validation_error_for_empty_body(
    async_client: AsyncClient,
):
    async with async_client:
        r = await async_client.post("/api/tasks/schedule", headers=get_auth_headers())
        missing = [i["loc"] for i in r.json()["detail"]]

        assert r.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert ["body"] in missing


@pytest.mark.asyncio
async def test_schedule_task_returns_validation_error_for_invalid_data(
    async_client: AsyncClient,
):
    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json={}, headers=get_auth_headers()
        )
        missing = [i["loc"] for i in r.json()["detail"]]

        assert ["body", "task_name"] in missing
        assert ["body", "task_params"] in missing


@pytest.mark.asyncio
async def test_schedule_returns_400_error_when_clientError_occurrs(
    async_client: AsyncClient, mocker
):
    mocked_get_queue_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_get_queue_url"
    )
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_check_key_exists", return_value=False
    )
    mocked_get_queue_url.side_effect = ClientError(
        error_response={}, operation_name="name"
    )
    data = {"task_name": "task", "task_params": {}}
    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json=data, headers=get_auth_headers()
        )
        assert r.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_schedule_returns_200_and_schedules_task(
    async_client: AsyncClient, mocker
):
    queue_url = "test-url"
    task_name = "task"
    task_params = {"asd": 2}
    task_results_url = "https://www.google.com"
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_check_key_exists", return_value=False
    )
    mocked_get_queue_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_get_queue_url"
    )
    mocked_get_queue_url.return_value = queue_url
    mocker.patch("src.endpoints.tasks.AWSServiceAdapter.sqs_send_json_message")
    mocker.patch("src.endpoints.tasks.AWSServiceAdapter.s3_put_json_obj")
    mocked_s3_generate_presigned_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_generate_presigned_url"
    )
    mocked_s3_generate_presigned_url.return_value = task_results_url

    data = {"task_name": task_name, "task_params": task_params}

    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json=data, headers=get_auth_headers()
        )
        response_data = r.json()

        assert r.status_code == HTTP_200_OK
        assert "task_id" in response_data
        assert len(response_data["task_id"]) == 32  # hex length
        assert "task_results_url" in response_data
        assert response_data["task_results_url"] == task_results_url


@pytest.mark.asyncio
async def test_schedule_properly_calls_aws_services_and_put_message_in_queue(
    async_client: AsyncClient, mocker
):
    queue_url = "test-url"
    task_name = "task"
    task_params = {"asd": 2}
    task_results_url = "https://www.google.com"
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_check_key_exists", return_value=False
    )
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_get_queue_url",
        lambda *x, **y: queue_url,
    )
    mocked_sqs_send_json_message = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_send_json_message"
    )
    mocked_s3_put_json_obj = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_put_json_obj"
    )
    mocked_s3_generate_presigned_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_generate_presigned_url"
    )
    mocked_s3_generate_presigned_url.return_value = task_results_url

    data = {"task_name": task_name, "task_params": task_params}

    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json=data, headers=get_auth_headers()
        )
        response_data = r.json()

        assert mocked_sqs_send_json_message.called is True
        assert "queue_url" in mocked_sqs_send_json_message.call_args.kwargs
        assert mocked_sqs_send_json_message.call_args.kwargs["queue_url"] == queue_url

        assert "message" in mocked_sqs_send_json_message.call_args.kwargs
        assert (
            mocked_sqs_send_json_message.call_args.kwargs["message"]["task_name"]
            == task_name
        )
        assert (
            mocked_sqs_send_json_message.call_args.kwargs["message"]["task_params"]
            == task_params
        )
        assert "task_id" in mocked_sqs_send_json_message.call_args.kwargs["message"]
        assert (
            mocked_sqs_send_json_message.call_args.kwargs["message"]["task_id"]
            == response_data["task_id"]
        )

        mocked_s3_generate_presigned_url.assert_called_with(
            bucket=settings.JOBS_BUCKET, key=f"{response_data['task_id']}-results"
        )
        assert mocked_s3_put_json_obj.called is True


@pytest.mark.asyncio
async def test_schedule_serves_results_from_cache_and_does_not_schedule_message(
    async_client: AsyncClient, mocker
):
    queue_url = "test-url"
    task_name = "task"
    task_params = {"asd": 2}
    task_results_url = "https://www.google.com"
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_check_key_exists", return_value=True
    )
    mocked_get_queue_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_get_queue_url"
    )
    mocked_get_queue_url.return_value = queue_url
    mocked_sqs_send_json_message = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_send_json_message"
    )
    mocked_s3_put_json_obj = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_put_json_obj"
    )
    mocked_s3_generate_presigned_url = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_generate_presigned_url"
    )
    mocked_s3_generate_presigned_url.return_value = task_results_url

    data = {"task_name": task_name, "task_params": task_params}

    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json=data, headers=get_auth_headers()
        )
        response_data = r.json()

        assert r.status_code == HTTP_200_OK
        assert mocked_sqs_send_json_message.called is False

        assert "task_id" in response_data
        assert len(response_data["task_id"]) == 32  # hex length
        assert "task_results_url" in response_data
        assert response_data["task_results_url"] == task_results_url
        assert mocked_s3_put_json_obj.called is False


@pytest.mark.asyncio
async def test_schedule_does_not_serve_results_from_cache_when_skip_cache_param_sent(
    async_client: AsyncClient, mocker
):
    queue_url = "test-url"
    task_name = "task"
    task_params = {"asd": 2}
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_check_key_exists", return_value=True
    )
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_get_queue_url",
        lambda *x, **y: queue_url,
    )
    mocked_sqs_send_json_message = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.sqs_send_json_message"
    )
    mocked_s3_put_json_obj = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_put_json_obj"
    )
    mocker.patch("src.endpoints.tasks.AWSServiceAdapter.s3_generate_presigned_url")

    data = {"task_name": task_name, "task_params": task_params, "task_skip_cache": True}

    async with async_client:
        r = await async_client.post(
            "/api/tasks/schedule", json=data, headers=get_auth_headers()
        )

        assert r.status_code == HTTP_200_OK
        assert mocked_sqs_send_json_message.called is True
        assert mocked_s3_put_json_obj.called is True


@pytest.mark.asyncio
async def test_task_status_returns_200_response_even_when_error_occurs(
    async_client: AsyncClient, mocker
):
    mocked_s3_get_json_obj = mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_get_json_obj"
    )
    mocked_s3_get_json_obj.side_effect = ClientError(
        error_response={}, operation_name="name"
    )

    async with async_client:
        r = await async_client.get("/api/tasks/123/status", headers=get_auth_headers())
        assert r.status_code == HTTP_200_OK
        assert r.json() == {
            "bucket": settings.JOBS_BUCKET,
            "meta": {"results": None, "status": consts.TaskStatus.NOT_STARTED},
            "processed": False,
            "task_id": "123",
        }


@pytest.mark.asyncio
async def test_task_status_returns_200_response_for_not_scheduled_job(
    async_client: AsyncClient, mocker
):
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_get_json_obj", return_value=None
    )

    async with async_client:
        r = await async_client.get("/api/tasks/123/status", headers=get_auth_headers())
        assert r.status_code == HTTP_200_OK
        assert r.json() == {
            "bucket": settings.JOBS_BUCKET,
            "meta": {"results": None, "status": consts.TaskStatus.NOT_STARTED},
            "processed": False,
            "task_id": "123",
        }


@pytest.mark.asyncio
async def test_task_status_returns_200_response_and_results_for_scheduled_job(
    async_client: AsyncClient, mocker
):
    mocker.patch(
        "src.endpoints.tasks.AWSServiceAdapter.s3_get_json_obj",
        return_value={"results": "sth", "status": consts.TaskStatus.READY},
    )

    async with async_client:
        r = await async_client.get("/api/tasks/123/status", headers=get_auth_headers())
        assert r.status_code == HTTP_200_OK
        assert r.json() == {
            "bucket": settings.JOBS_BUCKET,
            "meta": {"results": "sth", "status": consts.TaskStatus.READY},
            "processed": True,
            "task_id": "123",
        }
