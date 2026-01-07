# app/services/schema.py
"""
Centralized keys and flags for node/edge attributes used across the app.
"""

# --- Motif (formula-pattern) collapse ---
IS_MOTIF     = "is_motif"        # bool: node is a motif meta-node
MOTIF_SIG    = "motif_sig"       # str: canonical signature of the formula
MOTIF_COUNT  = "motif_count"     # int: number of member cells collapsed
MOTIF_MEMBERS = "motif_members"  # list[str]: original node ids
DISPLAY_LABEL = "display_label"  # str: preferred label for meta-nodes (e.g., motif)

# ---- Node attribute keys ----
IS_FORMULA = "is_formula"       # bool: node is a formula cell
IS_RANGE = "is_range"           # bool: node label represents a collapsed range
REP = "rep"                     # optional: representative cell id "Sheet!A1" (for ranges)
SHEET = "sheet"                 # string: sheet name this node should be grouped under

# ---- Edge attribute keys ----
FROM_RANGE = "from_range"       # string: "Sheet!U29:U40" if edge is from collapsed range node
REP_BRIDGE = "rep_bridge"       # bool: representative cell -> range node

# ---- Helpers ----
def sheet_of(node_id: str) -> str:
    return node_id.split("!", 1)[0] if "!" in node_id else ""
