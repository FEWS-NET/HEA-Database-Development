from typing import Dict, Tuple
from collections import defaultdict
import networkx as nx

from . import schema as S

def compute_levels(G: nx.DiGraph, start_node: str) -> Dict[str, int]:
    """
    Breadth-first "depth" levels: start at 0, predecessors increase depth (+1).
    """
    levels = {start_node: 0}
    queue = [start_node]
    while queue:
        cur = queue.pop(0)
        cur_level = levels[cur]
        for pred in G.predecessors(cur):
            if pred not in levels:
                levels[pred] = cur_level + 1
                queue.append(pred)
    return levels

def sheet_lanes_positions(G: nx.DiGraph, start_node: str) -> Dict[str, Dict[str, float]]:
    """
    Compute preset positions for a "sheet-lanes" layout:
      - y by breadth-first depth (0 at top, increasing downward)
      - x grouped by sheet (each sheet is one vertical lane)
      - small horizontal spreading per (sheet, level) group to reduce overlaps
    Returns: {node_id: {"x": float, "y": float}}
    """
    levels = compute_levels(G, start_node)

    def sheet_of(n: str) -> str:
        # Prefer explicit node attribute if present (for meta-nodes without '!')
        return G.nodes[n].get(S.SHEET) or (n.split("!", 1)[0] if "!" in n else "")

    groups = defaultdict(list)  # (level, sheet) -> [nodes]
    for n, lv in levels.items():
        groups[(lv, sheet_of(n))].append(n)

    # left-to-right order for sheets
    sheets = sorted({sheet_of(n) for n in levels.keys()})
    sheet_x_index = {s: i for i, s in enumerate(sheets)}

    # spacing constants
    X_GAP = 360.0
    X_SPREAD = 70.0
    Y_GAP = 150.0

    pos: Dict[str, Dict[str, float]] = {}
    for (lv, s), nodes in groups.items():
        nodes = sorted(nodes)
        k = len(nodes)
        base_x = sheet_x_index[s] * X_GAP
        y = lv * Y_GAP
        for i, n in enumerate(nodes):
            x = base_x + (i - (k - 1) / 2.0) * X_SPREAD
            pos[n] = {"x": x, "y": y}

    # normalize horizontally to center
    if pos:
        xs = [p["x"] for p in pos.values()]
        center = (min(xs) + max(xs)) / 2.0
        for n in pos:
            pos[n]["x"] -= center

    return pos
