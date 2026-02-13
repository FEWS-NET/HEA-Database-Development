from flask import render_template, request, jsonify, current_app
from . import bp
from ..services.workbook_io import list_sheets, open_workbook, get_formula_with_equals
from ..services.graph_builder import build_dependency_graph
from ..services.layout import sheet_lanes_positions
from ..main.serializers import graph_to_cytoscape
from ..services import schema as S
import os

def _bad_request(msg: str, code: int = 400):
    return jsonify({"error": msg}), code

def _default_path() -> str:
    return current_app.config.get("DEFAULT_WORKBOOK_PATH", "")

@bp.route("/")
def index():
    # Pre-fill the form with the default
    return render_template("index.html", default_path="LIAS_Senegal.xlsx")

@bp.route("/viewer")
def viewer():
    # Use ?path=... if provided; else default
    path = request.args.get("path") or _default_path()
    return render_template("viewer.html", file_path=path)

@bp.get("/api/sheets")
def api_sheets():
    path = request.args.get("path") or _default_path()
    if not path:
        return _bad_request("No workbook path provided.")
    try:
        sheets = list_sheets(path)
    except Exception as e:
        return _bad_request(f"Failed to open workbook '{path}': {e}", 500)
    return jsonify({"sheets": sheets, "path": path})

@bp.post("/api/graph")
def api_graph():
    data = request.get_json(silent=True) or {}
    path = data.get("path") or _default_path()
    sheet = data.get("sheet")
    cell = (data.get("cell") or "").strip().upper()

    if not path or not sheet or not cell:
        return _bad_request("Required JSON: { path (or default), sheet, cell }")

    import re
    if not re.match(r"^\$?[A-Z]{1,3}\$?\d{1,7}$", cell):
        return _bad_request(f"Invalid cell: {cell}")

    try:
        G, start_node = build_dependency_graph(path, sheet, cell)
    except Exception as e:
        return _bad_request(str(e), 400)

    pos = sheet_lanes_positions(G, start_node)
    elements = graph_to_cytoscape(G, start_node, pos)

    # formulas map (cells and ranges only)
    wb = open_workbook(path, read_only=True)
    formulas = {}
    for n in G.nodes:
        if G.nodes[n].get(S.IS_RANGE):
            rep = G.nodes[n].get(S.REP)
            if rep and "!" in rep:
                sh, cd = rep.split("!", 1)
                f = get_formula_with_equals(wb[sh], cd)
            else:
                f = None
            formulas[n] = {"type": "range", "rep": rep, "formula": f}
        else:
            if "!" in n:
                sh, cd = n.split("!", 1)
                f = get_formula_with_equals(wb[sh], cd)
            else:
                f = None
            formulas[n] = {"type": "cell", "rep": None, "formula": f}
    wb.close()

    meta = {
        "start_node": start_node,
        "counts": {"nodes": G.number_of_nodes(), "edges": G.number_of_edges()},
        "path": path,
    }

    return jsonify({
        "elements": elements,
        "layout": {"name": "preset", "fit": True, "padding": 30},
        "meta": meta,
        "formulas": formulas
    })
