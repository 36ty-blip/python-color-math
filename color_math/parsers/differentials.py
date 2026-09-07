"""Calculus differentials and derivative operators disambiguation."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import COLORS
from ..utils.spans import ColorSpan


@dataclass
class DifferentialSpan:
    start: int
    end: int
    text: str
    kind: str  # "differential" | "derivative_fraction"


GREEK_LETTERS = (
    r"alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|"
    r"lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|"
    r"Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega"
)
DIFF_VAR = r"(?:\\(?:" + GREEK_LETTERS + r")|[a-zA-Z])"


def find_differential_spans(body: str) -> list[DifferentialSpan]:
    """Scans LaTeX math body to identify infinitesimal differentials and derivative operators."""
    spans: list[DifferentialSpan] = []

    def add_span(start: int, end: int, text: str, kind: str) -> None:
        if start >= end:
            return
        if not any(start < s.end and end > s.start for s in spans):
            spans.append(DifferentialSpan(start, end, text, kind))

    # 1. Derivative fractions: \frac{d}{dx}, \frac{df}{dx}, \frac{\partial \psi}{\partial t}, \frac{d^2 y}{dx^2}
    deriv_frac_re = re.compile(
        r"\\frac\s*\{\s*(?:d|\\partial|\\mathrm\{d\})(?:\^\{?\d+\}?)?\s*(?:" + DIFF_VAR + r")?\s*\}\s*\{\s*(?:d|\\partial|\\mathrm\{d\})\s*" + DIFF_VAR + r"(?:\^\{?\d+\}?)?(?:\s*(?:d|\\partial|\\mathrm\{d\})\s*" + DIFF_VAR + r")*\s*\}"
    )
    for m in deriv_frac_re.finditer(body):
        add_span(m.start(), m.end(), m.group(0), "derivative_fraction")

    # 2. Infinitesimal differentials: dx, dt, dy, dz, dr, d\theta, d\phi, \partial x, \partial t
    diff_re = re.compile(
        r"(?:^|[\s+\-=*({]|\[|\\,|\\:|\\;|\\quad|\\qquad|~)(\s*(?:d|\\partial|\\mathrm\{d\}|\\delta)\s*" + DIFF_VAR + r"(?![a-zA-Z0-9_({])(?:\^\{?\d+\}?)?)"
    )
    for m in diff_re.finditer(body):
        full_match = m.group(0)
        diff_group = m.group(1)
        diff_start = m.start() + (len(full_match) - len(diff_group))
        d_match = re.search(r"(?:d|\\partial|\\mathrm\{d\}|\\delta)", diff_group)
        if d_match:
            d_offset = d_match.start()
            actual_start = diff_start + d_offset
            diff_text = diff_group[d_offset:]
            diff_end = actual_start + len(diff_text)
            add_span(actual_start, diff_end, diff_text, "differential")

    return sorted(spans, key=lambda s: s.start)


def collect_differential_spans(
    body: str,
    palette: dict[str, str] | None = None,
    diff_spans: list[DifferentialSpan] | None = None,
) -> list[ColorSpan]:
    """Returns color spans for differentials and derivative operators using palette.derivative."""
    pal = palette or COLORS
    diffs = diff_spans if diff_spans is not None else find_differential_spans(body)
    deriv_color = pal.get("derivative", "#bb9af7")
    return [ColorSpan(d.start, d.end, deriv_color, priority=24) for d in diffs]
