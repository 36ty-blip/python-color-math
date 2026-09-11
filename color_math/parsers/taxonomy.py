"""Mathematical taxonomy and semantic role coloring."""
from __future__ import annotations
import re

from ..config import (
    COLORS,
    MATH_CONSTANTS,
    MATH_PARAMETERS,
    MATH_FUNCTIONS,
    BARE_FUNCTIONS,
    MATH_ACCENTS,
    FONT_STYLE_MACROS,
)
from ..utils.spans import ColorSpan
from ..utils.latex_helpers import read_color_command, read_braced
from .units import find_unit_spans, UnitSpan
from .differentials import find_differential_spans, DifferentialSpan
from .dimensionless import find_dimensionless_spans, DimensionlessSpan


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


INDEX_RE = re.compile(
    r"(\\(?:sum|prod|coprod|bigcup|bigcap|lim|inf|sup))_\{?\s*([A-Za-z])\s*(?:=|\\to)"
)


def collect_taxonomy_spans(
    body: str,
    palette: dict[str, str] | None = None,
    unit_spans: list[UnitSpan] | None = None,
    diff_spans: list[DifferentialSpan] | None = None,
    dim_spans: list[DimensionlessSpan] | None = None,
) -> list[ColorSpan]:
    """Collects semantic spans for constants, parameters, and bound indices."""
    pal = palette or COLORS
    units = unit_spans if unit_spans is not None else find_unit_spans(body)
    diffs = diff_spans if diff_spans is not None else find_differential_spans(body)
    dims = dim_spans if dim_spans is not None else find_dimensionless_spans(body)
    spans: list[ColorSpan] = []

    # 1. Bound iteration indices in \sum, \prod, \lim
    for m in INDEX_RE.finditer(body):
        var_name = m.group(2)
        var_start = m.start() + m.group(0).rfind(var_name)
        spans.append(ColorSpan(var_start, var_start + len(var_name), pal.get("chain", "#9ece6a"), priority=23))

    # 2. Token-level scan for constants, functions, parameters, and dot derivatives
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

        # Bare math functions (sin, cos, tan, ln, exp, etc.)
        bare_m = re.match(r"^([A-Za-z]+)(?![A-Za-z])", body[idx:])
        if bare_m and bare_m.group(1).lower() in BARE_FUNCTIONS:
            fn_name = bare_m.group(1)
            spans.append(
                ColorSpan(
                    idx,
                    idx + len(fn_name),
                    pal.get("main", "#7aa2f7"),
                    priority=22,
                )
            )
            idx += len(fn_name)
            continue

        if body[idx] == "\\":
            m = re.match(r"^(\\[A-Za-z]+|\\.)", body[idx:])
            if m:
                cmd_name = m.group(1)
                cmd_end = idx + len(cmd_name)

                # Skip environment arguments: \begin{bmatrix}, \end{cases}
                if cmd_name in (r"\begin", r"\end"):
                    after_cmd = cmd_end
                    while after_cmd < len(body) and body[after_cmd].isspace():
                        after_cmd += 1
                    if after_cmd < len(body) and body[after_cmd] == "{":
                        braced = read_braced(body, after_cmd)
                        if braced is not None:
                            idx = braced[1]
                            continue
                    idx = cmd_end
                    continue

                # Color custom operators as functions: \operatorname{rank}, \operatorname*{argmin}
                if cmd_name == r"\operatorname":
                    after_cmd = cmd_end
                    if after_cmd < len(body) and body[after_cmd] == "*":
                        after_cmd += 1
                    while after_cmd < len(body) and body[after_cmd].isspace():
                        after_cmd += 1
                    if after_cmd < len(body) and body[after_cmd] == "{":
                        braced = read_braced(body, after_cmd)
                        if braced is not None:
                            spans.append(ColorSpan(idx, braced[1], pal.get("main", "#7aa2f7"), priority=22))
                            idx = braced[1]
                            continue
                    idx = cmd_end
                    continue

                macro_key = cmd_name[1:]
                if macro_key in OPAQUE_MACROS:
                    after_cmd = cmd_end
                    while after_cmd < len(body) and body[after_cmd].isspace():
                        after_cmd += 1
                    if after_cmd < len(body) and body[after_cmd] == "{":
                        braced = read_braced(body, after_cmd)
                        if braced is not None:
                            idx = braced[1]
                            continue

                if cmd_name in MATH_ACCENTS:
                    target_start = cmd_end
                    while target_start < len(body) and body[target_start].isspace():
                        target_start += 1
                    if target_start < len(body):
                        target_end = target_start + 1
                        if body[target_start] == "{":
                            braced = read_braced(body, target_start)
                            if braced is not None:
                                target_end = braced[1]
                        else:
                            let_m = re.match(r"^[a-zA-Z]('*)*", body[target_start:])
                            if let_m:
                                target_end = target_start + len(let_m.group(0))
                        is_dot = cmd_name in (r"\dot", r"\ddot", r"\dddot", r"\ddddot")
                        color = pal.get("derivative", "#bb9af7") if is_dot else pal.get("parameter", pal.get("main", "#7aa2f7"))
                        spans.append(ColorSpan(idx, target_end, color, priority=22))
                        idx = target_end
                        continue

                if cmd_name in MATH_CONSTANTS:
                    spans.append(ColorSpan(idx, cmd_end, pal.get("orange", "#e0af68"), priority=22))
                    idx = cmd_end
                    continue

                if cmd_name in MATH_FUNCTIONS:
                    spans.append(ColorSpan(idx, cmd_end, pal.get("main", "#7aa2f7"), priority=22))
                    idx = cmd_end
                    continue

                if cmd_name in MATH_PARAMETERS:
                    spans.append(ColorSpan(idx, cmd_end, pal.get("parameter", pal.get("derivative", "#bb9af7")), priority=20))
                    idx = cmd_end
                    continue

                if cmd_name in FONT_STYLE_MACROS:
                    target_start = cmd_end
                    while target_start < len(body) and body[target_start].isspace():
                        target_start += 1
                    if target_start < len(body):
                        target_end = target_start + 1
                        if body[target_start] == "{":
                            braced = read_braced(body, target_start)
                            if braced is not None:
                                target_end = braced[1]
                        else:
                            let_m = re.match(r"^[a-zA-Z]('*)*", body[target_start:])
                            if let_m:
                                target_end = target_start + len(let_m.group(0))
                        spans.append(ColorSpan(idx, target_end, pal.get("main", "#7aa2f7"), priority=20))
                        idx = target_end
                        continue

                idx = cmd_end
                continue

        idx += 1

    return sorted(spans, key=lambda s: s.start)
