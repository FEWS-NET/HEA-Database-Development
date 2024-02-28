"""
Custom Luigi Formats
"""

import json

from luigi.format import TextWrapper, WrappedFormat


class JsonWrapper(TextWrapper):
    def read(self):
        return json.loads(super().read())

    def write(self, b):
        super().write(json.dumps(b, indent=4))


class JsonFormat(WrappedFormat):
    """
    Stores a Python object as a JSON string.
    """

    input = "object"  # noqa: A003
    output = "bytes"
    wrapper_cls = JsonWrapper


JSON = JsonFormat()
