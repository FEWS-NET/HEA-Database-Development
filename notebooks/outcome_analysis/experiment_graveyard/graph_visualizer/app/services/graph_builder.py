# app/services/graph_builder.py
from typing import Dict, Optional, Set, Tuple
import networkx as nx

from .excel_parser import parse_formula
from .workbook_io import open_workbook, get_formula_text
from .collapse_rules import pick_representative_cell
from . import schema as S

def build_dependency_graph(
    path: str,
    sheet: str,
    cell: str,
    *,
    max_nodes: int = 5000
) -> Tuple[nx.DiGraph, str]:
    """
    Build a dependency graph for 'sheet!cell', lazily traversing referenced formulas.
    - Range references become labeled range nodes with a bridge from a representative cell.
    """
    wb = open_workbook(path, read_only=False)
    if sheet not in wb.sheetnames:
        wb.close()
        raise ValueError(f"Sheet '{sheet}' not found.")

    start_node = f"{sheet}!{cell.upper()}"

    # Formula cache: node_id -> formula text (without '=') or None if not a formula
    formula_cache: Dict[str, Optional[str]] = {}

    def get_formula(node_id: str) -> Optional[str]:
        if node_id in formula_cache:
            return formula_cache[node_id]
        if "!" not in node_id:
            formula_cache[node_id] = None
            return None
        sh, coord = node_id.split("!", 1)
        if sh not in wb.sheetnames:
            formula_cache[node_id] = None
            return None
        f = get_formula_text(wb[sh], coord)
        formula_cache[node_id] = f
        return f

    if get_formula(start_node) is None:
        wb.close()
        raise ValueError(f"Cell '{start_node}' does not contain a formula.")

    G = nx.DiGraph()
    G.add_node(start_node, **{
        S.IS_FORMULA: True,
        S.IS_RANGE: False,
        S.SHEET: sheet,
    })

    to_process: Set[str] = {start_node}
    processed: Set[str] = set()

    while to_process:
        current = to_process.pop()
        if current in processed:
            continue
        processed.add(current)
        if len(G) >= max_nodes:
            break

        current_formula = get_formula(current)
        if not current_formula:
            continue

        current_sheet = current.split("!", 1)[0]
        refs = parse_formula(current_formula, current_sheet=current_sheet, expand_ranges=False)

        for it in refs:
            if it["type"] == "cell":
                pred_display = f"{it['sheet']}!{it['ref']}"
                pred_for_logic = pred_display
                from_range = None
                is_range_node = False
                pred_sheet = it["sheet"]
            else:
                # range node keeps label; bridge from representative cell
                pred_display = f"{it['sheet']}!{it['ref']}"
                rep = pick_representative_cell(wb, it["sheet"], it["a"], it["b"])
                if not rep:
                    continue
                pred_for_logic = rep
                from_range = pred_display
                is_range_node = True
                pred_sheet = it["sheet"]

            pred_is_formula = get_formula(pred_for_logic) is not None

            # Ensure display node exists
            if pred_display not in G:
                G.add_node(pred_display, **{
                    S.IS_FORMULA: bool(pred_is_formula),
                    S.IS_RANGE: is_range_node,
                    S.REP: pred_for_logic if is_range_node else None,
                    S.SHEET: pred_sheet,
                })
            else:
                if pred_is_formula:
                    G.nodes[pred_display][S.IS_FORMULA] = True
                if is_range_node:
                    G.nodes[pred_display][S.IS_RANGE] = True
                    G.nodes[pred_display][S.REP] = pred_for_logic
                if S.SHEET not in G.nodes[pred_display]:
                    G.nodes[pred_display][S.SHEET] = pred_sheet

            # Current node is a formula by construction
            G.nodes[current][S.IS_FORMULA] = True

            # Add edge (with range flag if applicable)
            if from_range:
                G.add_edge(pred_display, current, **{S.FROM_RANGE: from_range})
            else:
                G.add_edge(pred_display, current)

            # If range: add representative node + bridge edge pred_for_logic -> pred_display
            if is_range_node:
                rep_sheet = pred_for_logic.split("!", 1)[0]
                if pred_for_logic not in G:
                    G.add_node(pred_for_logic, **{
                        S.IS_FORMULA: pred_is_formula,
                        S.IS_RANGE: False,
                        S.SHEET: rep_sheet,
                    })
                else:
                    if pred_is_formula:
                        G.nodes[pred_for_logic][S.IS_FORMULA] = True
                    if S.SHEET not in G.nodes[pred_for_logic]:
                        G.nodes[pred_for_logic][S.SHEET] = rep_sheet
                if not G.has_edge(pred_for_logic, pred_display):
                    G.add_edge(pred_for_logic, pred_display, **{S.REP_BRIDGE: True})

            # Recurse only into formula predecessors (via rep for ranges)
            if pred_is_formula and pred_for_logic not in processed:
                to_process.add(pred_for_logic)

    wb.close()
    return G, start_node
