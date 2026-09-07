# parsers/__init__.py

from .math_parser import (
    ParsedMath,
    SemanticSpan,
    describe_math_blocks,
    find_semantic_spans,
    format_math_structure,
    parse_math_blocks,
    parse_math_body,
    parser_available,
)
from .markdown_scanner import MarkdownScan, MarkdownSpan, scan_markdown

from .scanner import (
    color_latex_body_with_scanner,
)

from .units import UnitSpan, find_unit_spans, collect_unit_spans
from .differentials import DifferentialSpan, find_differential_spans, collect_differential_spans
from .braket import BraKetSpan, find_braket_spans, collect_braket_delimiter_spans
from .dimensionless import DimensionlessSpan, find_dimensionless_spans, collect_dimensionless_spans
from .delimiters import DelimiterPair, find_delimiter_pairs, collect_delimiter_spans
from .taxonomy import collect_taxonomy_spans
from .variable_hash import collect_variable_spans


__all__ = [
    "ParsedMath",
    "SemanticSpan",
    "MarkdownScan",
    "MarkdownSpan",

    # math_parser.py
    "describe_math_blocks",
    "find_semantic_spans",
    "format_math_structure",
    "parse_math_blocks",
    "parse_math_body",
    "parser_available",
    "scan_markdown",

    # scanner.py
    "color_latex_body_with_scanner",

    # new parsers
    "UnitSpan",
    "find_unit_spans",
    "collect_unit_spans",
    "DifferentialSpan",
    "find_differential_spans",
    "collect_differential_spans",
    "BraKetSpan",
    "find_braket_spans",
    "collect_braket_delimiter_spans",
    "DimensionlessSpan",
    "find_dimensionless_spans",
    "collect_dimensionless_spans",
    "DelimiterPair",
    "find_delimiter_pairs",
    "collect_delimiter_spans",
    "collect_taxonomy_spans",
    "collect_variable_spans",
]
