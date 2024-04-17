import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import helpers, models, serializers

logger = logging.getLogger(__name__)


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class ShortenLinkApiView(GenericAPIView):
    serializer_class = serializers.ShortenRequestSerializer
    signature_fail_attempts = 3

    def save_url_and_get_signature(self, url, attempt=1):
        if attempt > self.signature_fail_attempts:
            raise ValidationError({"signature": _("Cannot generate signature")})
        try:
            signature = helpers.get_random_identifier()
            models.ShortenedUrl.objects.create(url=url, signature=signature)
            logger.debug(f"Succesfully created signature {url=}, {signature=}")
            return signature
        except IntegrityError:
            logger.error("Signature already exists in database, generating another one")
            return self.save_url_and_get_signature(url, attempt=attempt + 1)

    def get_signature_link(self, signature):
        return reverse(
            "shortener:redirect", kwargs={"signature": signature}, request=self.request
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            url = serializer.data["url"]
            item = models.ShortenedUrl.objects.filter(url=url).first()
            signature = (
                item.signature if item else self.save_url_and_get_signature(url=url)
            )

            return Response({"result": self.get_signature_link(signature)})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@require_http_methods(["GET"])
def shortened_link_redirect_view(request, signature):
    item = models.ShortenedUrl.objects.filter(signature=signature).first()
    if not item:
        raise Http404

    response_class = (
        HttpResponsePermanentRedirect
        if settings.SHORTENING_REDIRECT_PERMANENT
        else HttpResponseRedirect
    )

    return response_class(redirect_to=item.url)
