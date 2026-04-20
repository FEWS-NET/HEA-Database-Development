import re
from typing import Dict, Iterable, List, Optional, Tuple

# ---- A1 reference regex with optional quoted sheet names ----
A1_REF_RE = re.compile(
    r"(?:(?P<sheet>'[^']+'|[A-Za-z0-9_ .-]+)\!)?"
    r"(?P<ref>\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?)"
)

def col_to_num(col: str) -> int:
    col = col.replace("$", "").upper()
    n = 0
    for ch in col:
        if "A" <= ch <= "Z":
            n = n * 26 + (ord(ch) - 64)
    return n

def num_to_col(n: int) -> str:
    s = []
    while n:
        n, r = divmod(n - 1, 26)
        s.append(chr(r + 65))
    return "".join(reversed(s))

def split_a1(cell: str) -> Tuple[str, str]:
    """Return (column_part, row_part) preserving $ signs (e.g., '$AB', '$12')."""
    cell = cell.upper()
    i = 0
    while i < len(cell) and (cell[i] == "$" or cell[i].isalpha()):
        i += 1
    return cell[:i], cell[i:]

def expand_range(a: str, b: str) -> List[str]:
    """Expand an A1 range 'A1'..'C3' into individual refs, preserving absolute markers on first cell."""
    col_a, row_a = split_a1(a)
    col_b, row_b = split_a1(b)
    col_a_num = col_to_num(col_a)
    col_b_num = col_to_num(col_b)
    row_a_num = int(row_a.replace("$", ""))
    row_b_num = int(row_b.replace("$", ""))
    cols = range(min(col_a_num, col_b_num), max(col_a_num, col_b_num) + 1)
    rows = range(min(row_a_num, row_b_num), max(row_a_num, row_b_num) + 1)
    col_abs = "$" if col_a.startswith("$") else ""
    row_abs = "$" if row_a.startswith("$") else ""
    return [f"{col_abs}{num_to_col(c)}{row_abs}{r}" for c in cols for r in rows]

def iter_cells_in_range(a: str, b: str) -> Iterable[str]:
    """Yield cells (no $) top-left → bottom-right."""
    col_a, row_a = split_a1(a)
    col_b, row_b = split_a1(b)
    c1, c2 = col_to_num(col_a), col_to_num(col_b)
    r1, r2 = int(row_a.replace("$", "")), int(row_b.replace("$", ""))
    for c in range(min(c1, c2), max(c1, c2) + 1):
        for r in range(min(r1, r2), max(r1, r2) + 1):
            yield f"{num_to_col(c)}{r}"

def parse_formula(formula: str, current_sheet: Optional[str] = None, *, expand_ranges: bool = True
                  ) -> List[Dict[str, str]]:
    """
    Parse an Excel formula into references.

    Returns list of dicts with either:
      - {"type":"cell","sheet":"S","ref":"$A$1"}
      - {"type":"range","sheet":"S","ref":"U29:U40","a":"U29","b":"U40"}  (if expand_ranges=False)
    If expand_ranges=True, ranges are expanded into individual cell entries.
    """
    items: List[Dict[str, str]] = []
    if not formula:
        return items
    for m in A1_REF_RE.finditer(formula):
        sheet = m.group("sheet")
        ref = m.group("ref").upper()
        if sheet:
            sheet = sheet.strip("'")
            if sheet.endswith("!"):
                sheet = sheet[:-1]
        else:
            sheet = current_sheet
        if ":" in ref:
            a, b = ref.split(":")
            if expand_ranges:
                for cell in expand_range(a, b):
                    items.append({"type": "cell", "sheet": sheet, "ref": cell})
            else:
                items.append({"type": "range", "sheet": sheet, "ref": ref, "a": a, "b": b})
        else:
            items.append({"type": "cell", "sheet": sheet, "ref": ref})
    return items
