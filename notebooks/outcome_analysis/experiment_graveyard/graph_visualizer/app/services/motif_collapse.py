from __future__ import annotations
from typing import Dict, List, Tuple, Iterable, Optional
import re
import hashlib
import networkx as nx

from . import schema as S
from .workbook_io import open_workbook, get_formula_text
from .excel_parser import A1_REF_RE

# Replace A1 refs with REF; optionally replace numeric literals with N
NUM_RE = re.compile(r'(?<![A-Za-z_])(?<!")\b\d+(\.\d+)?([eE][+-]?\d+)?\b')

def formula_signature(formula: Optional[str], *, normalize_numbers: bool = True) -> str:
    """
    Canonicalize a formula to a 'signature':
      - strip leading "="
      - uppercase
      - replace all cell/range refs with "REF"
      - optionally replace numeric literals with "N"
      - collapse whitespace
    """
    if not formula:
        return ""
    f = formula[1:] if formula.startswith("=") else formula
    f = A1_REF_RE.sub("REF", f)
    if normalize_numbers:
        f = NUM_RE.sub("N", f)
    f = re.sub(r"\s+", "", f).upper()
    return f

def _func_head(sig: str) -> str:
    """Return leading function token if present, else ''."""
    m = re.match(r'^([A-Z_][A-Z0-9_.]*)\(', sig)
    return m.group(1) if m else ""

def _stable_id(prefix: str, sheet: str, sig: str) -> str:
    h = hashlib.sha1(sig.encode("utf-8")).hexdigest()[:10]
    base = f"{prefix}|{sheet}|{h}"
    return base

def collapse_by_motif(
    G: nx.DiGraph,
    *,
    workbook_path: str,
    start_node: str,
    scope: str = "sheet",       # "sheet" or "global"
    min_group_size: int = 3,
    normalize_numbers: bool = True
) -> Tuple[nx.DiGraph, Dict[str, str], Dict[str, dict]]:
    """
    Collapse groups of cell formula nodes that share the same signature.
    Returns:
      H: collapsed graph
      node_map: original_node_id -> motif_node_id (only for collapsed members)
      motif_info: motif_node_id -> {sig, count, members, func_head}
    """
    # 1) Build grouping key per cell formula node
    wb = open_workbook(workbook_path, read_only=True)
    try:
        groups: Dict[Tuple[str, str], List[str]] = {}  # key -> [node ids]
        sig_cache: Dict[str, str] = {}

        def node_sheet(n: str) -> str:
            return G.nodes[n].get(S.SHEET) or (n.split("!",1)[0] if "!" in n else "")

        for n, d in G.nodes(data=True):
            # Only collapse real formula cells (not ranges, not meta)
            if not d.get(S.IS_FORMULA):
                continue
            if d.get(S.IS_RANGE) or d.get(S.IS_MOTIF):
                continue
            if "!" not in n:
                continue
            sh, cd = n.split("!", 1)
            f = get_formula_text(wb[sh], cd)
            if f is None:
                continue
            sig = formula_signature("=" + f, normalize_numbers=normalize_numbers)
            sig_cache[n] = sig
            key_sheet = node_sheet(n) if scope == "sheet" else "__GLOBAL__"
            groups.setdefault((key_sheet, sig), []).append(n)

        # Filter small groups
        groups = {k: v for k, v in groups.items() if len(v) >= min_group_size}
        if not groups:
            return G.copy(), {}, {}

        # 2) Create collapsed graph H
        H = nx.DiGraph()
        # Copy over all non-collapsed nodes; collapsed nodes become motif nodes
        collapsed_members: Dict[str, str] = {}  # member -> motif_id
        motif_info: Dict[str, dict] = {}

        # Pre-copy every node (we'll redirect ids for collapsed members later)
        for n, d in G.nodes(data=True):
            H.add_node(n, **d)

        # Build motif nodes + remove members
        for (key_sheet, sig), members in groups.items():
            func = _func_head(sig) or "FORMULA"
            count = len(members)
            motif_id = _stable_id("MOTIF", key_sheet, sig)
            label = f"{func} × {count}"

            # Decide which "sheet lane" to place the motif in
            if scope == "global":
                # choose majority sheet among members
                by_sheet: Dict[str, int] = {}
                for m in members:
                    s = node_sheet(m)
                    by_sheet[s] = by_sheet.get(s, 0) + 1
                sheet_for_lane = max(by_sheet, key=by_sheet.get) if by_sheet else key_sheet
            else:
                sheet_for_lane = key_sheet

            H.add_node(motif_id, **{
                S.IS_MOTIF: True,
                S.MOTIF_SIG: sig,
                S.MOTIF_COUNT: count,
                S.MOTIF_MEMBERS: members,
                S.DISPLAY_LABEL: label,
                S.SHEET: sheet_for_lane,
                S.IS_FORMULA: True,   # treat as formula-type for styling/layout
                S.IS_RANGE: False,
            })
            motif_info[motif_id] = {
                "sig": sig,
                "count": count,
                "members": members,
                "func_head": func,
            }
            for m in members:
                collapsed_members[m] = motif_id
                if H.has_node(m):
                    H.remove_node(m)

        # 3) Rebuild edges: map members -> motif ids
        for u, v, ed in G.edges(data=True):
            u2 = collapsed_members.get(u, u)
            v2 = collapsed_members.get(v, v)
            if u2 == v2:
                continue
            # Merge edge attributes lightly (range edges stay dashed)
            data = {}
            if ed.get(S.FROM_RANGE):
                data[S.FROM_RANGE] = ed[S.FROM_RANGE]
            if ed.get(S.REP_BRIDGE):
                data[S.REP_BRIDGE] = True
            if not H.has_node(u2):
                H.add_node(u2, **G.nodes[u])  # safety
            if not H.has_node(v2):
                H.add_node(v2, **G.nodes[v])
            H.add_edge(u2, v2, **data)

        return H, collapsed_members, motif_info
    finally:
        wb.close()
