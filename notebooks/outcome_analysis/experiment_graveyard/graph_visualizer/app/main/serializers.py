# app/main/serializers.py
from typing import Dict, List
import networkx as nx
from ..services import schema as S

def _label_for_node(G: nx.DiGraph, start_node: str, n: str) -> str:
    # Range keeps full id; same-sheet cells show coord; cross-sheet cells show full
    if G.nodes[n].get(S.IS_RANGE):
        return n
    sheet = G.nodes[n].get(S.SHEET) or (n.split("!", 1)[0] if "!" in n else "")
    start_sheet = start_node.split("!", 1)[0] if "!" in start_node else ""
    if "!" in n and sheet == start_sheet:
        return n.split("!", 1)[1]
    return n

def graph_to_cytoscape(G: nx.DiGraph, start_node: str, positions: Dict[str, Dict[str, float]]) -> List[dict]:
    sheets = sorted({G.nodes[n].get(S.SHEET) or (n.split("!", 1)[0] if "!" in n else "") for n in G.nodes})
    elements: List[dict] = []

    for s in sheets:
        elements.append({"data": {"id": f"sheet::{s}", "label": s}, "classes": "sheet-group"})

    for n in G.nodes:
        is_range = bool(G.nodes[n].get(S.IS_RANGE))
        is_formula = bool(G.nodes[n].get(S.IS_FORMULA))
        node_class = ("range" if is_range else ("formula" if is_formula else "value"))
        sheet = G.nodes[n].get(S.SHEET) or (n.split("!", 1)[0] if "!" in n else "")
        data = {"id": n, "label": _label_for_node(G, start_node, n), "type": node_class, "sheet": sheet, "parent": f"sheet::{sheet}"}
        el = {"data": data, "classes": node_class}
        if n in positions:
            el["position"] = positions[n]
        elements.append(el)

    for u, v, data in G.edges(data=True):
        if data.get(S.FROM_RANGE):
            cls = "range-edge"
        elif data.get(S.REP_BRIDGE):
            cls = "rep-bridge"
        else:
            cls = "edge-normal"
        elements.append({"data": {"id": f"{u}->{v}", "source": u, "target": v, "cls": cls}, "classes": cls})

    return elements
