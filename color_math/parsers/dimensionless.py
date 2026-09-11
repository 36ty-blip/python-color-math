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


NUM_LIST = "|".join(COMMON_DIMENSIONLESS_NUMBERS)
TEXT_RE = re.compile(r"\\(?:text|mathrm)\s*\{\s*(" + NUM_LIST + r")\s*\}")
BARE_RE = re.compile(r"(?:^|[^\\a-zA-Z])(" + NUM_LIST + r")(?![a-zA-Z])")


def find_dimensionless_spans(body: str) -> list[DimensionlessSpan]:
    """Scans LaTeX math body to identify physical & engineering dimensionless numbers."""
    spans: list[DimensionlessSpan] = []

    def add_span(start: int, end: int, text: str) -> None:
        if start >= end:
            return
        if not any(start < s.end and end > s.start for s in spans):
            spans.append(DimensionlessSpan(start, end, text))

    # 1. Text or mathrm wrapped: \text{Re}, \mathrm{Ma}, etc.
    for m in TEXT_RE.finditer(body):
        add_span(m.start(), m.end(), m.group(0))

    # 2. Contiguous bare symbols: Re, Ma, Pr, etc.
    for m in BARE_RE.finditer(body):
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
