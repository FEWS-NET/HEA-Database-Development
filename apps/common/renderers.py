import csv
from io import BytesIO, TextIOWrapper

from django.templatetags.static import static
from rest_framework.renderers import BaseRenderer


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
    filename = "fdwdata.csv"

    def prepare_data(self, data, accepted_media_type=None, renderer_context=None):
        """
        Converts data into a specialized format. Override this method in
        subclasses to provide specialized formatting e.g timeseries format.
        """
        return data

    def render(self, data, accepted_media_type=None, renderer_context=None):
        csv_buffer = TextIOWrapper(BytesIO(), encoding=self.charset)
        writer = csv.writer(csv_buffer)
        for row in self.prepare_data(data, accepted_media_type, renderer_context):
            writer.writerow(row)

        # Set up response
        renderer_context["response"]["Content-Disposition"] = 'attachment; filename="%s"' % self.filename
        renderer_context["response"]["Cache-Control"] = "no-cache"
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
            '<link href="' + static("bootstrap/css/bootstrap.min.css") + '" rel="stylesheet">'
            '<link href="' + static("css/bootstrap-responsive.min.css") + '" rel="stylesheet">'
            '<link href="' + static("css/project.css") + '" rel="stylesheet"></head><body>)'
        )
        data = self.prepare_data(data, accepted_media_type, renderer_context)
        if data and len(data) > 0:
            html += '<div class="row"><div class="span-12"><table class="table table-bordered"><tbody>\n'
        for row in data:
            html += "<tr>"
            for value in row:
                value = str(value) if value else ""
                html += "<td>{0}</td>".format(value)
            html += "</tr>\n"
            html += "</tbody></table></div></div>"
        if data is None or len(data) == 0:
            html += '<div class="message-block "><span>No data found</span></div>'
        html += "</body></html>"
        return html.encode(self.charset)
