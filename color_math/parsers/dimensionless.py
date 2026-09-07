"""Physical & engineering dimensionless numbers disambiguation."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import COLORS
from ..utils.spans import ColorSpan


@dataclass
class DimensionlessSpan:
    start: int
    end: int
    text: str


COMMON_DIMENSIONLESS_NUMBERS = [
    "Re",  # Reynolds
    "Ma",  # Mach
    "Pr",  # Prandtl
    "Nu",  # Nusselt
    "Kn",  # Knudsen
    "Sc",  # Schmidt
    "Pe",  # Péclet
    "Gr",  # Grashof
    "Ra",  # Rayleigh
    "We",  # Weber
    "Fr",  # Froude
    "St",  # Strouhal
    "Bi",  # Biot
    "Fo",  # Fourier
]


def find_dimensionless_spans(body: str) -> list[DimensionlessSpan]:
    """Scans LaTeX math body to identify physical & engineering dimensionless numbers."""
    spans: list[DimensionlessSpan] = []

    def add_span(start: int, end: int, text: str) -> None:
        if start >= end:
            return
        if not any(start < s.end and end > s.start for s in spans):
            spans.append(DimensionlessSpan(start, end, text))

    num_list = "|".join(COMMON_DIMENSIONLESS_NUMBERS)

    # 1. Text or mathrm wrapped: \text{Re}, \mathrm{Ma}, etc.
    text_re = re.compile(r"\\(?:text|mathrm)\s*\{\s*(" + num_list + r")\s*\}")
    for m in text_re.finditer(body):
        add_span(m.start(), m.end(), m.group(0))

    # 2. Contiguous bare symbols: Re, Ma, Pr, etc.
    # Must NOT be preceded by backslash (e.g. \Re) or any letter.
    # Must NOT be followed by any letter.
    bare_re = re.compile(r"(?:^|[^\\a-zA-Z])(" + num_list + r")(?![a-zA-Z])")
    for m in bare_re.finditer(body):
        symbol = m.group(1)
        sym_start = m.start() + (len(m.group(0)) - len(symbol))
        sym_end = sym_start + len(symbol)
        add_span(sym_start, sym_end, symbol)

    return sorted(spans, key=lambda s: s.start)


def collect_dimensionless_spans(
    body: str,
    palette: dict[str, str] | None = None,
    dim_spans: list[DimensionlessSpan] | None = None,
) -> list[ColorSpan]:
    """Returns color spans for dimensionless numbers with main / cyan color."""
    pal = palette or COLORS
    dims = dim_spans if dim_spans is not None else find_dimensionless_spans(body)
    color = pal.get("main", "#7aa2f7")
    return [ColorSpan(d.start, d.end, color, priority=24) for d in dims]
