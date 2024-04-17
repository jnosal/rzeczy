import pytest
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from ..factories import ShortenedUrlFactory
from ..models import ShortenedUrl


@pytest.mark.django_db
def test_shortened_link_redirect_view_raises_404_when_sig_does_not_exist(client):
    r = client.get(reverse("shortener:redirect", kwargs={"signature": "sth"}))

    assert r.status_code == status.HTTP_404_NOT_FOUND


@override_settings(SHORTENING_REDIRECT_PERMANENT=True)
@pytest.mark.django_db
def test_shortened_link_redirect_view_issues_permanent_redirect(client):
    item = ShortenedUrlFactory()
    r = client.get(reverse("shortener:redirect", kwargs={"signature": item.signature}))

    assert r.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert r.headers["Location"] == item.url


@override_settings(SHORTENING_REDIRECT_PERMANENT=False)
@pytest.mark.django_db
def test_shortened_link_redirect_view_issues_temporary_redirect(client):
    item = ShortenedUrlFactory()
    r = client.get(reverse("shortener:redirect", kwargs={"signature": item.signature}))
    assert r.status_code == status.HTTP_302_FOUND
    assert r.headers["Location"] == item.url


@override_settings(SHORTENING_REDIRECT_PERMANENT=False)
@pytest.mark.django_db
def test_shortened_link_only_allws_GET_method(client):
    item = ShortenedUrlFactory()
    r = client.head(reverse("shortener:redirect", kwargs={"signature": item.signature}))
    assert r.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_shortening_returns_bad_request_error_for_invalid_data(client):
    data = {"url": ""}
    r = client.post(reverse("shortener:shorten"), data=data)
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_returns_shortened_url(client):
    url = "https://www.google.com"
    assert ShortenedUrl.objects.count() == 0

    r = client.post(reverse("shortener:shorten"), data={"url": url})

    assert r.status_code == status.HTTP_200_OK
    assert "result" in r.data
    assert ShortenedUrl.objects.count() == 1
    assert ShortenedUrl.objects.first().signature in r.data["result"]


@pytest.mark.django_db
def test_returns_shortened_url_without_creating_record_in_db_if_unnecessary(client):
    url = "https://www.google.com"
    ShortenedUrlFactory(signature="test", url=url)

    assert ShortenedUrl.objects.count() == 1

    r = client.post(reverse("shortener:shorten"), data={"url": url})

    assert r.status_code == status.HTTP_200_OK
    assert ShortenedUrl.objects.count() == 1
    assert "test" in r.data["result"]


@pytest.mark.django_db(transaction=True)
def test_retries_process_on_integrity_error(client, mocker):
    existing_signature = "existing"
    url = "https://www.google.com"

    mocked_get_random_identifier = mocker.patch(
        "shortener.api.helpers.get_random_identifier"
    )
    mocked_get_random_identifier.side_effect = [existing_signature, "new"]

    ShortenedUrlFactory(signature=existing_signature)

    r = client.post(reverse("shortener:shorten"), data={"url": url})

    assert r.status_code == status.HTTP_200_OK
    assert ShortenedUrl.objects.count() == 2
    assert mocked_get_random_identifier.call_count == 2


@pytest.mark.django_db(transaction=True)
def test_raises_ValidationError_when_too_many_retries(client, mocker):
    url = "https://www.google.com"

    mocked_get_random_identifier = mocker.patch(
        "shortener.api.helpers.get_random_identifier"
    )
    mocked_get_random_identifier.side_effect = [
        IntegrityError,
        IntegrityError,
        IntegrityError,
        IntegrityError,
    ]

    r = client.post(reverse("shortener:shorten"), data={"url": url})

    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "signature" in r.data
