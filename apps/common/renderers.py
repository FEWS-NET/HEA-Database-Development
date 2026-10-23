import csv
from collections.abc import Iterable, Mapping
from io import BytesIO, TextIOWrapper

from rest_framework.renderers import BaseRenderer, JSONRenderer


def get_serializer_fieldnames(renderer_context: Mapping | None) -> list[str]:
    """
    Return the names of the readable fields of the serializer for the view, in declaration order.

    Returns an empty list if there is no view or serializer, e.g. for an APIView, or
    if the response is an error, because then the data doesn't come from the serializer.
    """
    renderer_context = renderer_context or {}
    view = renderer_context.get("view")
    response = renderer_context.get("response")
    if view is None or not hasattr(view, "get_serializer") or (response is not None and response.status_code >= 400):
        return []
    try:
        serializer = view.get_serializer()
    except Exception:  # The view may not have a serializer_class, or may be unable to create one for this request
        return []
    return [name for name, field in serializer.fields.items() if not field.write_only]


def get_fieldnames(data: Iterable[Mapping], renderer_context: Mapping | None = None) -> list[str]:
    """
    Return the column names for data, using the serializer fields followed by any other keys in the rows.

    Serializers omit a key from a row when the field is read-only and its dotted
    source can't be resolved for that instance, e.g. `livelihood_strategy.season.pk`
    for a LivelihoodActivity without a Season. Therefore, the keys of the first row
    are not necessarily the columns required for the whole dataset.

    Using the serializer fields means that the columns are the same for every request
    to an endpoint, even if none of the rows contain a field, or there are no rows.
    The keys from all the rows are appended so that fields added in `to_representation`,
    such as the aggregates from an AggregatingSerializer, are included.

    If the rows don't contain any of the serializer fields, e.g. for a paginated
    response or a custom action that returns other data, then only the keys from
    the rows are used.
    """
    data_fieldnames = list(dict.fromkeys(key for row in data for key in row.keys()))
    serializer_fieldnames = get_serializer_fieldnames(renderer_context)
    if data_fieldnames and not set(serializer_fieldnames).intersection(data_fieldnames):
        return data_fieldnames
    return list(dict.fromkeys(serializer_fieldnames + data_fieldnames))


class FormattedCSVRenderer(BaseRenderer):
    """
    A generic CSV Renderer which allows specialized formatting of data in
    renderers subclassing it.
    """

    media_type = "text/csv"
    format = "csv"
    # Include the UTF-8 BOM so that Microsoft Excel and LibreOffice Calc can recognize the file encoding
    charset = "utf-8-sig"

    # Override the following fields in subclasses
    filename = "headata.csv"

    def prepare_data(self, data, accepted_media_type=None, renderer_context=None):
        """
        Converts data into a specialized format. Override this method in
        subclasses to provide specialized formatting e.g timeseries format.
        """
        return data

    def render(self, data, accepted_media_type=None, renderer_context=None):
        data = self.prepare_data(data, accepted_media_type, renderer_context)
        data = data if isinstance(data, (list, tuple)) else [data]
        csv_buffer = TextIOWrapper(BytesIO(), encoding=self.charset)
        # Use the same columns for every row, and fill missing values, so that the columns line up
        fieldnames = get_fieldnames(data, renderer_context)
        if fieldnames:
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, restval="")
            writer.writeheader()
            writer.writerows(data)
        renderer_context["response"]["Content-Disposition"] = 'attachment; filename="%s"' % self.filename
        renderer_context["response"]["Cache-Control"] = "no-cache"
        csv_buffer.seek(0)
        return csv_buffer.buffer.getvalue()


class HtmlTableRenderer(BaseRenderer):
    """
    Renderer which returns values as time series in a similar style to the
    HO MT Spreadsheet, output as an unstyled HTML table suitable for an
    Excel Web Query defined in a .iqy file
    """

    media_type = "text/html"
    format = "html"
    charset = "utf-8"

    def prepare_data(self, data, accepted_media_type=None, renderer_context=None):
        """
        Converts data into a specialized format. Override this method in
        subclasses to provide specialized formatting e.g timeseries format.
        """
        return data

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the data, creating the table header inside the first iteration
        of the loop in case data is a generator
        """
        html = (
            "<!DOCTYPE html><html><head>"
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
            "</head><body>"
        )
        data = self.prepare_data(data, accepted_media_type, renderer_context)
        data = data if isinstance(data, (list, tuple)) else [data]
        if data and len(data) > 0:
            html += '<div class="row"><div class="span-12"><table class="table table-bordered"><tbody>\n'
        # Use the same columns for every row, and fill missing values, so that the columns line up
        fieldnames = get_fieldnames(data, renderer_context)
        first_row = True
        for row in data:
            if first_row:
                html += '<table class="table table-bordered" style="margin: 30px;">'
                html += "<thead><tr>"
                for field in fieldnames:
                    # Duplicate columns from a dataframe will have trailing spaces
                    html += "<th>{0}</th>".format(field.strip())
                html += "</tr></thead><tbody>\n"
                first_row = False
            html += "<tr>"
            for field in fieldnames:
                value = row.get(field)
                value = str(value) if value else ""
                html += "<td>{0}</td>".format(value)
            html += "</tr>\n"
        if data is None or len(data) == 0:
            html += '<div class="message-block "><span>No data found</span></div>'
        else:
            html += "</tbody></table></div></div>"
        html += "</body></html>"
        return html.encode(self.charset)


class GeoJSONRenderer(JSONRenderer):
    media_type = "application/geo+json"  # GeoJSON-specific media type
    format = "geojson"
