"""Generic source-preserving LaTeX coloring."""

from __future__ import annotations

import re

from ..config import COLORS, ColorMathOptions
from ..parsers.constants import collect_single_constant_spans
from ..parsers.math_parser import find_semantic_spans
from ..parsers.scanner import collect_scanner_spans
from ..parsers.units import find_unit_spans, collect_unit_spans
from ..parsers.differentials import find_differential_spans, collect_differential_spans
from ..parsers.braket import collect_braket_delimiter_spans
from ..parsers.dimensionless import find_dimensionless_spans, collect_dimensionless_spans
from ..parsers.delimiters import collect_delimiter_spans
from ..parsers.taxonomy import collect_taxonomy_spans
from ..parsers.variable_hash import collect_variable_spans
from ..utils.latex_helpers import contains_color_wrapper, normalize_latex_braces
from ..utils.spans import ColorSpan, apply_color_spans


MATH_LINE_RE = re.compile(
    r"^(?P<prefix>\s*\#+\s*)?\$\$(?P<body>.*)\$\$(?P<suffix>\s*)$"
)
FUNCTION_COLOR_NAMES = ("main", "derivative", "chain")


def collect_function_spans(body: str, palette: dict[str, str] | None = None) -> list[ColorSpan]:
    """Color nested call names and recognize literal constants."""
    pal = palette or COLORS
    semantic, _ = find_semantic_spans(body)
    spans: list[ColorSpan] = []
    for item in semantic:
        if item.kind == "function":
            color_name = FUNCTION_COLOR_NAMES[min(item.depth, 2)]
        elif item.kind == "constant":
            color_name = "orange"
        else:
            continue
        spans.append(
            ColorSpan(item.start, item.end, pal[color_name], priority=20)
        )
    return spans


def color_latex_body(
    body: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    """Insert scoped colors while preserving every original source character."""
    if contains_color_wrapper(body):
        return body

    pal = palette or COLORS
    opts = options or ColorMathOptions()

    normalized = normalize_latex_braces(body)

    unit_spans = find_unit_spans(normalized)
    diff_spans = find_differential_spans(normalized)
    dim_spans = find_dimensionless_spans(normalized)

    spans: list[ColorSpan] = [
        *collect_function_spans(normalized, pal),
        *collect_scanner_spans(normalized),
    ]

    if opts.color_units:
        spans.extend(collect_unit_spans(normalized, pal, unit_spans))

    if opts.color_differentials:
        spans.extend(collect_differential_spans(normalized, pal, diff_spans))

    if opts.color_dimensionless:
        spans.extend(collect_dimensionless_spans(normalized, pal, dim_spans))

    if opts.color_braket:
        spans.extend(collect_braket_delimiter_spans(normalized, pal))

    if opts.color_single_constants:
        spans.extend(collect_single_constant_spans(normalized, pal))

    if opts.rainbow_delimiters:
        spans.extend(collect_delimiter_spans(normalized))

    if opts.enable_taxonomy:
        spans.extend(collect_taxonomy_spans(normalized, pal, unit_spans, diff_spans, dim_spans))

    if opts.variable_data_flow:
        spans.extend(collect_variable_spans(normalized, None, unit_spans, diff_spans, dim_spans))

    return apply_color_spans(normalized, spans)


def color_generic_math_line(
    line: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    """Convert a single-line ``$$...$$`` math block."""
    match = MATH_LINE_RE.match(line)
    if match is None:
        return line
    prefix = match.group("prefix") or ""
    suffix = match.group("suffix")
    return f"{prefix}$${color_latex_body(match.group('body'), palette, options)}$${suffix}"
