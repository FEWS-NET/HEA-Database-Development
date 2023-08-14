from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_doc_strings_for_model


@permission_classes((permissions.IsAuthenticated,))
class ModelDocStringsAPI(APIView):
    def get(self, request, model_name):
        try:
            doc_strings = get_doc_strings_for_model(model_name)
            return JsonResponse({"model_name": model_name, "doc_string": doc_strings})
        except Exception as e:
            return Response({"error": str(e)})
