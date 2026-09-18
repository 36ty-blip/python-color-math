# converters/block.py

from __future__ import annotations
import re
from collections.abc import Callable

from ..config import ColorMathOptions
from ..parsers.markdown_scanner import scan_markdown
from .align import convert_align_block
from .derivative import convert_derivative_line
from .equation import convert_equation_line
from .generic import color_latex_body, color_generic_math_line
from .integral import convert_integral_line
from .limit import convert_limit_line
from .matrix import convert_matrix_block


MATH_BLOCK_RE = re.compile(
    r"^(?P<prefix>\s*\#+\s*)?\$\$(?P<body>.*)\$\$(?P<suffix>\s*)$",
    re.DOTALL,
)
Converter = Callable[[str], str | None]

LINE_CONVERTERS: tuple[Converter, ...] = (
    convert_derivative_line,
    convert_integral_line,
    convert_limit_line,
    convert_equation_line,
)

BLOCK_CONVERTERS: tuple[Converter, ...] = (
    convert_matrix_block,
    convert_align_block,
)


def try_converters(text: str, converters: tuple[Converter, ...]) -> str | None:
    for converter in converters:
        converted = converter(text)

        if converted is not None:
            return converted

    return None


def _has_semantic_options(options: ColorMathOptions | None) -> bool:
    return bool(
        options
        and (
            options.enable_taxonomy
            or options.variable_data_flow
            or options.rainbow_delimiters
            or options.color_units
            or options.color_differentials
            or options.color_braket
            or options.color_dimensionless
            or options.color_quantum_operators
            or options.field in ("quantum", "physics")
        )
    )


def convert_math_block(
    block: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    """
    Convert a multiline math block.

    Specialized converters insert wrappers into the original source. Generic
    coloring is used only when no semantic formatter recognizes the block.
    """

    match = MATH_BLOCK_RE.match(block)

    if not match:
        return block

    prefix = match.group("prefix") or ""
    body = match.group("body")
    suffix = match.group("suffix")

    if _has_semantic_options(options):
        return f"{prefix}$${color_latex_body(body, palette, options)}$${suffix}"

    line_match = try_converters(block, LINE_CONVERTERS)

    if line_match is not None:
        return line_match

    block_match = try_converters(block, BLOCK_CONVERTERS)

    if block_match is not None:
        return block_match

    # fallback to generic coloring
    return f"{prefix}$${color_latex_body(body, palette, options)}$${suffix}"


def convert_line(
    line: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    """
    Convert a single line.

    Checks specialized converters first,
    otherwise generic math coloring.
    """

    if _has_semantic_options(options):
        return color_generic_math_line(line, palette, options)

    converted = try_converters(line, LINE_CONVERTERS)

    if converted is not None:
        return converted

    return color_generic_math_line(line, palette, options)


def convert_text(
    text: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    """
    Convert an entire document.

    Handles:
      - single-line and multiline $$ ... $$ math blocks
      - inline $ ... $ math expressions
      - normal text passthrough
    """
    if "$" not in text:
        return text

    scan = scan_markdown(text)
    all_spans = sorted(
        [*scan.math_blocks, *scan.math_inlines],
        key=lambda s: s.start,
    )
    if not all_spans:
        return text

    converted: list[str] = []
    index = 0
    for span in all_spans:
        converted.append(text[index:span.start])
        if span.kind == "math_inline":
            raw = text[span.content_start:span.content_end]
            converted.append(f"${color_latex_body(raw, palette, options)}$")
        else:
            converted.append(
                convert_math_block(text[span.start:span.end], palette, options)
            )
        index = span.end
    converted.append(text[index:])
    return "".join(converted)
