import json
import logging

from django.core.management.commands import loaddata

logger = logging.getLogger(__name__)


class Command(loaddata.Command):
    """
    Django loaddata management command with additional logging.
    """

    def save_obj(self, obj):
        try:
            return super().save_obj(obj)
        except Exception as e:
            # @TODO handle unserializable objects
            logger.exception(e, extra={"object": json.dumps(obj.object.__dict__)})
            raise
