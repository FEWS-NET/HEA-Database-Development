from django.conf import settings

"""
Context processor for injecting Theme variable from the enviroment variable THEME
"""


def theme_context(request):
    # Retrieve the theme from settings (environment variable) or default to 'hea_default'
    theme = getattr(settings, "THEME", "hea_default")
    # Return the theme as a dictionary to be included in the template context
    return {"theme": theme}


def selected_settings(request):
    return {"APP_VERSION": settings.APP_VERSION}
