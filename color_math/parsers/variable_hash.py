"""Variable data-flow hashing parser."""
from __future__ import annotations
import re

from ..config import (
    VARIABLE_HASH_PALETTE,
    hash_string_to_color,
    MATH_ACCENTS,
    FONT_STYLE_MACROS,
    BARE_FUNCTIONS,
)
from ..utils.spans import ColorSpan
from ..utils.latex_helpers import read_color_command, read_braced
from .units import find_unit_spans, UnitSpan
from .differentials import find_differential_spans, DifferentialSpan
from .dimensionless import find_dimensionless_spans, DimensionlessSpan
from .constants import is_euler_constant, is_imaginary_unit


OPAQUE_MACROS = frozenset({
    "text", "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "mathcal",
    "mathbb", "boldsymbol", "operatorname", "textbf", "textit", "textrm", "texttt"
})


def _skip_comment(text: str, start: int) -> int:
    idx = start + 1
    while idx < len(text) and text[idx] not in ("\r", "\n"):
        idx += 1
    if idx < len(text) and text[idx] == "\r" and idx + 1 < len(text) and text[idx + 1] == "\n":
        return idx + 2
    return min(idx + 1, len(text))


def collect_variable_spans(
    body: str,
    palette: list[str] | None = None,
    unit_spans: list[UnitSpan] | None = None,
    diff_spans: list[DifferentialSpan] | None = None,
    dim_spans: list[DimensionlessSpan] | None = None,
) -> list[ColorSpan]:
    """Assigns deterministic colors to distinct identifiers across an expression."""
    pal = palette or VARIABLE_HASH_PALETTE
    units = unit_spans if unit_spans is not None else find_unit_spans(body)
    diffs = diff_spans if diff_spans is not None else find_differential_spans(body)
    dims = dim_spans if dim_spans is not None else find_dimensionless_spans(body)
    spans: list[ColorSpan] = []

    idx = 0
    while idx < len(body):
        if body[idx] == "%":
            idx = _skip_comment(body, idx)
            continue

        existing = read_color_command(body, idx)
        if existing is not None:
            idx = existing[1]
            continue

        if any(u.start <= idx < u.end for u in units):
            idx = next(u.end for u in units if u.start <= idx < u.end)
            continue
        if any(d.start <= idx < d.end for d in diffs):
            idx = next(d.end for d in diffs if d.start <= idx < d.end)
            continue
        if any(d.start <= idx < d.end for d in dims):
            idx = next(d.end for d in dims if d.start <= idx < d.end)
            continue

        # Backslash commands
        if body[idx] == "\\":
            m = re.match(r"^(\\[A-Za-z]+|\\.)", body[idx:])
            if m:
                cmd_name = m.group(1)
                cmd_end = idx + len(cmd_name)

                # Accents like \dot, \ddot, \vec, \hat, \bar, \tilde
                if cmd_name in MATH_ACCENTS:
                    target_start = cmd_end
                    while target_start < len(body) and body[target_start].isspace():
                        target_start += 1
                    if target_start < len(body):
                        if body[target_start] == "{":
                            braced = read_braced(body, target_start)
                            if braced is not None:
                                inner = body[braced[0]:braced[1]]
                                base_m = re.search(r"[a-zA-Z]", inner)
                                base_letter = base_m.group(0) if base_m else "x"
                                color = hash_string_to_color(base_letter, pal)
                                spans.append(ColorSpan(idx, braced[1], color, priority=15))
                                idx = braced[1]
                                continue
                        else:
                            let_m = re.match(r"^[a-zA-Z]('*)*", body[target_start:])
                            if let_m:
                                full_var = let_m.group(0)
                                base_letter = full_var.replace("'", "")
                                color = hash_string_to_color(base_letter, pal)
                                spans.append(ColorSpan(idx, target_start + len(full_var), color, priority=15))
                                idx = target_start + len(full_var)
                                continue

                if cmd_name in FONT_STYLE_MACROS:
                    target_start = cmd_end
                    while target_start < len(body) and body[target_start].isspace():
                        target_start += 1
                    if target_start < len(body):
                        target_end = target_start + 1
                        base_letter = "R"
                        if body[target_start] == "{":
                            braced = read_braced(body, target_start)
                            if braced is not None:
                                target_end = braced[1]
                                bm = re.search(r"[a-zA-Z]", body[braced[0]:braced[1]])
                                if bm:
                                    base_letter = bm.group(0)
                        else:
                            let_m = re.match(r"^[a-zA-Z]('*)*", body[target_start:])
                            if let_m:
                                target_end = target_start + len(let_m.group(0))
                                base_letter = let_m.group(0).replace("'", "")
                        color = hash_string_to_color(base_letter, pal)
                        spans.append(ColorSpan(idx, target_end, color, priority=15))
                        idx = target_end
                        continue

                macro_key = cmd_name[1:]
                if macro_key in OPAQUE_MACROS:
                    braced = read_braced(body, cmd_end)
                    if braced is not None:
                        idx = braced[1]
                        continue

                idx = cmd_end
                continue

        # Check bare math functions (sin, cos, tan, ln, exp, etc.) so they are NOT shredded into single-letter variables
        bare_m = re.match(r"^([A-Za-z]+)(?![A-Za-z])", body[idx:])
        if bare_m and bare_m.group(1).lower() in BARE_FUNCTIONS:
            idx += len(bare_m.group(1))
            continue

        # Single-character constants 'e' and 'i'/'j'
        if is_euler_constant(body, idx) or is_imaginary_unit(body, idx):
            spans.append(ColorSpan(idx, idx + 1, "#e0af68", priority=22))
            idx += 1
            continue

        # Single letter variables (optionally with prime): x, y, z, t, x', y''
        var_m = re.match(r"^[a-zA-Z]('*)*", body[idx:])
        if var_m:
            full_var = var_m.group(0)
            base_letter = full_var.replace("'", "")
            var_end = idx + len(full_var)

            # Check if followed by ( or \left( -> function call like f(x)
            after_var = body[var_end:].lstrip()
            is_function = after_var.startswith("(") or after_var.startswith(r"\left(")

            if not is_function:
                color = hash_string_to_color(base_letter, pal)
                spans.append(ColorSpan(idx, var_end, color, priority=15))

            idx = var_end
            continue

        idx += 1

    return sorted(spans, key=lambda s: s.start)
