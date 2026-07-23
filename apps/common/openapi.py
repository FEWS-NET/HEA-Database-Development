from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import get_view_model


class CustomDrfSpectacularSchema(AutoSchema):
    def get_tags(self):
        # Override to use verbose name on Model class, where discoverable
        model = get_view_model(self.view, emit_warnings=False)
        if not model:
            serializer = self.get_response_serializers()

            if isinstance(serializer, dict) and serializer:
                # extract likely main serializer from @extend_schema override
                serializer = {str(code): s for code, s in serializer.items()}
                serializer = serializer[min(serializer)]

            if hasattr(serializer, "Meta") and hasattr(serializer.Meta, "model"):
                model = serializer.Meta.model

        if model:
            return [
                model._meta.verbose_name.title() if model._meta.verbose_name.islower() else model._meta.verbose_name
            ]
        else:
            # Fall back to default, which is first non-parameter string in endpoint URL path after SCHEMA_PATH_PREFIX
            return super().get_tags()


endpoint_index_of_path = 0


def preprocessing_filter_spec(endpoints):
    return (endpoint for endpoint in endpoints if endpoint[endpoint_index_of_path].startswith("/api/"))
