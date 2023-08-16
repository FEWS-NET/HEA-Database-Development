import csv
import io

from django.templatetags.static import static
from rest_framework.renderers import BaseRenderer


class CSVRenderer(BaseRenderer):
    """
    A generic CSV Renderer.
    """

    media_type = "text/csv"
    format = "csv"
    # Include the UTF-8 BOM so that Microsoft Excel and LibreOffice Calc can recognize the file encoding
    charset = "utf-8-sig"
    filename = "hea-data.csv"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        csv_buffer = io.TextIOWrapper(io.BytesIO(), encoding=self.charset)
        writer = csv.writer(csv_buffer)
        first_row = True
        for row in data:
            if first_row:
                writer.writerow(row.keys())
                first_row = False
            writer.writerow(row.values())
        renderer_context["response"]["Content-Disposition"] = 'attachment; filename="%s"' % self.filename
        renderer_context["response"]["Cache-Control"] = "no-cache"
        csv_buffer.seek(0)
        return csv_buffer.buffer.read()


class HtmlTableRenderer(BaseRenderer):
    """
    Renderer which returns values as time series in a similar style to the
    HO MT Spreadsheet, output as an unstyled HTML table suitable for an
    Excel Web Query defined in a .iqy file
    """

    media_type = "text/html"
    format = "html"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        output = [
            (
                "<!DOCTYPE html><html><head>"
                '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
                '<link href="' + static("bootstrap/css/bootstrap.min.css") + '" rel="stylesheet">'
                '<link href="' + static("admin/css/base.css") + '" rel="stylesheet">'
                "</head><body>"
            )
        ]
        # Do not attempt to iterate over the rows if the response is 4xx or 5xx error
        if isinstance(data, str) or (
            "response" in renderer_context and renderer_context["response"].status_code >= 400
        ):
            output.append("<p>{}</p>".format(data))
        else:
            first_row = True
            # If paginated JSON, extract data and render pagination metadata
            pagination_suffix = ""
            if isinstance(data, dict) and set(data.keys()) == {"count", "next", "previous", "results"}:
                output.append(f"<p>Count: {data['count']}.")
                if data["previous"]:
                    output.append(f" Previous page: {data['previous']}.")
                if data["next"]:
                    output.append(f" Next page: {data['next']}.")
                output.append("</p>")
                data = data["results"]
            for row in data:
                if first_row:
                    output.append('<table class="table table-bordered" style="margin: 30px;">')
                    output.append("<thead><tr>")
                    for field in row:
                        # Duplicate columns from a dataframe will have trailing spaces
                        output.append("<th>{0}</th>".format(field.strip()))
                    output.append("</tr></thead><tbody>\n")
                    first_row = False
                output.append("<tr>")
                for value in row.values():
                    value = str(value) if value or value == 0 else ""
                    output.append("<td>{0}</td>".format(value))
                output.append("</tr>\n")
            if not first_row:
                output.append(f"</tbody></table>{pagination_suffix}")
            else:
                output.append('<div class="message-block "><span>No data found</span></div>')
        output.append("</body></html>")
        return "".join(output).encode(self.charset)
