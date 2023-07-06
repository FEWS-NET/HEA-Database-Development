from django import template

register = template.Library()


@register.filter(is_safe=True)
def docstring(value) -> str:
    """Return the docstring for the object"""
    return value.__doc__
