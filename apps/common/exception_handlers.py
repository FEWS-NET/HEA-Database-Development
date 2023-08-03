import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def drf_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=exc.message_dict)
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Error creating reponse:")
        return Response({"detail": str(exc)}, 500, content_type="text/html")
    else:
        return response
