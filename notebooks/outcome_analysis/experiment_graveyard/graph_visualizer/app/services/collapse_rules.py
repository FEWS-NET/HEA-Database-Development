import re
from typing import Dict, List, Optional, Set, Tuple

from .excel_parser import split_a1, col_to_num, iter_cells_in_range
from .workbook_io import get_formula_text
from . import schema as S

# ---- Range representative selection ----

def pick_representative_cell(wb, sheet: str, a: str, b: str) -> Optional[str]:
    """
    Prefer the first cell in the range that contains a formula; else the top-left cell.
    Returns 'Sheet!A1' or None if the sheet is missing.
    """
    if sheet not in wb.sheetnames:
        return None
    ws = wb[sheet]
    for coord in iter_cells_in_range(a, b):
        if get_formula_text(ws, coord) is not None:
            return f"{sheet}!{coord}"
    for coord in iter_cells_in_range(a, b):
        return f"{sheet}!{coord}"
    return None

# ---- Pairwise fan-in collapse (e.g., MAX(a1*b1, a2*b2, ...)) ----

FUNC_HEAD_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\(', re.I)
PAIR_ARG_RE = re.compile(
    r'^\s*'
    r'(?P<lhs>(?:\'[^\']+\'|[A-Za-z0-9_ .-]+)\!\$?[A-Za-z]{1,3}\$?\d{1,7}|\$?[A-Za-z]{1,3}\$?\d{1,7})'
    r'\s*\*\s*'
    r'(?P<rhs>(?:\'[^\']+\'|[A-Za-z0-9_ .-]+)\!\$?[A-Za-z]{1,3}\$?\d{1,7}|\$?[A-Za-z]{1,3}\$?\d{1,7})'
    r'\s*$', re.I
)

def _strip_eq(s: str) -> str:
    return s[1:] if s and s.startswith('=') else s

def _split_top_level_args(s: str) -> List[str]:
    m = FUNC_HEAD_RE.match(s)
    if not m:
        return []
    i = m.end()  # position after '('
    depth = 1
    arg = []
    args = []
    while i < len(s):
        ch = s[i]
        if ch == '(':
            depth += 1
            arg.append(ch)
        elif ch == ')':
            depth -= 1
            if depth == 0:
                a = ''.join(arg).strip()
                if a:
                    args.append(a)
                break
            arg.append(ch)
        elif ch == ',' and depth == 1:
            a = ''.join(arg).strip()
            args.append(a)
            arg = []
        else:
            arg.append(ch)
        i += 1
    return args

def _norm_ref_with_sheet(ref: str, default_sheet: str) -> Tuple[str, str]:
    """Return (sheet, A1) with sheet fallback and uppercase A1."""
    if '!' in ref:
        sheet, a1 = ref.split('!', 1)
        sheet = sheet.strip("'")
    else:
        sheet, a1 = default_sheet, ref
    return sheet, a1.upper()

def _contiguous_by_col(cells: List[str]) -> Tuple[bool, str, str, int]:
    """
    cells: list like ['GD311','GE311',...]; return (ok, col_start, col_end, row_int)
    ok=True if same row and columns increase by 1 each step.
    """
    def split(a1: str):
        col, row = split_a1(a1)
        return col.replace("$",""), int(row.replace("$",""))
    if not cells:
        return False, "", "", 0
    c0, r0 = split(cells[0])
    prev = col_to_num(c0)
    for a1 in cells[1:]:
        c, r = split(a1)
        if r != r0:
            return False, "", "", 0
        n = col_to_num(c)
        if n != prev + 1:
            return False, "", "", 0
        prev = n
    c_last, _ = split(cells[-1])
    return True, c0, c_last, r0

def detect_pairwise_fanin(formula: str, current_sheet: str) -> Dict:
    """
    If formula looks like FUNC(a1*b1, a2*b2, ...), FUNC in {MAX,SUM,MIN,AVERAGE},
    and both sequences (a's and b's) walk contiguous columns with constant rows,
    return a structure describing the collapse; else {"ok": False}.
    """
    f = _strip_eq(formula or "")
    m = FUNC_HEAD_RE.match(f)
    if not m:
        return {"ok": False}
    func = m.group(1).upper()
    if func not in {"MAX", "SUM", "MIN", "AVERAGE"}:
        return {"ok": False}
    args = _split_top_level_args(f)
    if not args or len(args) < 5:
        return {"ok": False}

    lhs_cells: List[str] = []
    rhs_cells: List[str] = []
    pairs: List[Tuple[str, str]] = []

    for a in args:
        m2 = PAIR_ARG_RE.match(a)
        if not m2:
            return {"ok": False}
        lhs = m2.group("lhs")
        rhs = m2.group("rhs")
        sh_l, a1_l = _norm_ref_with_sheet(lhs, current_sheet)
        sh_r, a1_r = _norm_ref_with_sheet(rhs, current_sheet)
        pairs.append((f"{sh_l}!{a1_l}", f"{sh_r}!{a1_r}"))
        lhs_cells.append(a1_l)
        rhs_cells.append(a1_r)

    okL, cL0, cL1, rL = _contiguous_by_col(lhs_cells)
    okR, cR0, cR1, rR = _contiguous_by_col(rhs_cells)
    if not (okL and okR):
        return {"ok": False}

    shL = pairs[0][0].split('!', 1)[0]
    shR = pairs[0][1].split('!', 1)[0]
    lhs_range = f"{shL}!({cL0}:{cL1}){rL}"
    rhs_range = f"{shR}!({cR0}:{cR1}){rR}"
    return {
        "ok": True,
        "func": func,
        "pairs": pairs,
        "lhs_range": lhs_range,
        "rhs_range": rhs_range,
        "count": len(pairs),
    }
