from typing import List

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def split(value: str, arg: str) -> List[str]:
    """Splits the string `value` by the delimiter `arg` and returns the resulting list"""
    # Django passes a delimiter of "\n" as "\\n", and Python doesn't like using str.replace to create "\n"
    if arg == "\\n":
        arg = "\n"
    elif arg == "\\t":
        arg = "\t"
    return value.split(arg)
