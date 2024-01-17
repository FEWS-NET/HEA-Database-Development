from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _


class LanguageMiddleware(MiddlewareMixin):
    """
    This middleware adds a language parameter that can override the Django locale.
    This is needed so that translations are available for users accessing the API from a browser or Excel,
    where the Accept-Language HTTP header is hard to override, it is not possible to set the
    language cookie, and i18n URL paths are not supported, because they are not compliant with REST standards.

    This middleware does not permit a user to override a language URL path. Pages routed via Django's i18n
    routing must offer the user the ability to change the language. /en/somepage?language=ar is not supported
    and will raise a validation error.
    """

    def process_request(self, request):

        language_from_parameter = request.POST.get("language", request.GET.get("language", False))
        language_from_path = translation.get_language_from_path(request.path_info)

        if language_from_path:
            if language_from_parameter:
                # Enforce this strictly, because this touches core Django infrastructure, and because we need
                # to know the language parameter is being ignored.
                raise ValidationError(
                    _(
                        "Remove the language URL parameter. It is not supported for language-specific paths. "
                        f"{language_from_path} is specified in the path, and "
                        f"{language_from_parameter} is specified in the parameter."
                    )
                )
            return

        if not language_from_parameter:
            return

        if language_from_parameter not in (code for code, name in settings.LANGUAGES):
            # We need to know the language parameter is being ignored.
            supported_codes = ", ".join(code for code, name in settings.LANGUAGES)
            raise ValidationError(
                _(
                    "The language URL parameter requests language %(lang_code)s. Supported language code"
                    "s are %(lang_codes)s." % {"lang_code": language_from_parameter, "lang_codes": supported_codes}
                )
            )

        translation.activate(language_from_parameter)
        request.LANGUAGE_CODE = translation.get_language()
