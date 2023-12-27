"""
Customized version of django.core.serializers.json that provided additional logging.
"""
import json
import logging

from django.core.serializers.base import DeserializationError
from django.core.serializers.json import Serializer as JSONSerializer
from django.core.serializers.python import Deserializer as PythonDeserializer

logger = logging.getLogger(__name__)


class Serializer(JSONSerializer):
    def end_object(self, obj):
        super().end_object(obj)
        logger.info("Serialized %s" % str(obj))


def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data with added logging.
    """
    if not isinstance(stream_or_string, (bytes, str)):
        stream_or_string = stream_or_string.read()
    if isinstance(stream_or_string, bytes):
        stream_or_string = stream_or_string.decode()
    try:
        objects = json.loads(stream_or_string)
        for object in objects:
            try:
                yield from PythonDeserializer([object], **options)
            except Exception:
                logging.exception("Failed to deserialize object %s" % object)
                raise
    except (GeneratorExit, DeserializationError):
        raise
    except Exception as exc:
        raise DeserializationError() from exc
