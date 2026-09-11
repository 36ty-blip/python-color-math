"""Quantum Bra-Ket (Dirac) notation parser."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import COLORS
from ..utils.spans import ColorSpan


@dataclass
class BraKetSpan:
    start: int
    end: int
    kind: str  # "bracket" | "ket" | "bra"


BRAKET_RE = re.compile(
    r"\\langle\s*([^<|>]+?)\s*\|\s*([^<|>]+?)(?:\s*\|\s*([^<|>]+?))?\s*\\rangle"
)
KET_MACRO_RE = re.compile(
    r"(?:\||\\vert)\s*([^<|>]+?)\s*\\rangle|\\ket\s*\{([^}]+)\}"
)
BRA_MACRO_RE = re.compile(
    r"\\langle\s*([^<|>]+?)\s*(?:\||\\vert)|\\bra\s*\{([^}]+)\}"
)
KET_DELIM_RE = re.compile(r"(?:\||\\vert)\s*([^<|>]+?)\s*\\rangle")
BRA_DELIM_RE = re.compile(r"\\langle\s*([^<|>]+?)\s*(?:\||\\vert)")


def find_braket_spans(body: str) -> list[BraKetSpan]:
    """Scans LaTeX math body to identify Dirac bra-ket spans."""
    spans: list[BraKetSpan] = []

    def add_span(start: int, end: int, kind: str) -> None:
        if start >= end:
            return
        if not any(start < s.end and end > s.start for s in spans):
            spans.append(BraKetSpan(start, end, kind))

    # 1. Bracket / Expectation value: \langle ... | ... \rangle
    for m in BRAKET_RE.finditer(body):
        add_span(m.start(), m.end(), "bracket")

    # 2. Ket: | ... \rangle or \vert ... \rangle or \ket{...}
    for m in KET_MACRO_RE.finditer(body):
        add_span(m.start(), m.end(), "ket")

    # 3. Bra: \langle ... | or \langle ... \vert or \bra{...}
    for m in BRA_MACRO_RE.finditer(body):
        add_span(m.start(), m.end(), "bra")

    return sorted(spans, key=lambda s: s.start)


def collect_braket_delimiter_spans(
    body: str,
    palette: dict[str, str] | None = None,
    delim_color: str | None = None,
) -> list[ColorSpan]:
    r"""Returns color spans for Dirac delimiters (\langle, |, \rangle)."""
    pal = palette or COLORS
    color = delim_color or pal.get("orange", "#e0af68")
    spans: list[ColorSpan] = []

    # 1. \langle ... | ... \rangle
    for m in BRAKET_RE.finditer(body):
        full = m.group(0)
        langle_idx = m.start()
        langle_end = langle_idx + len(r"\langle")
        rangle_idx = m.start() + full.rfind(r"\rangle")
        rangle_end = rangle_idx + len(r"\rangle")

        spans.append(ColorSpan(langle_idx, langle_end, color, priority=25))
        spans.append(ColorSpan(rangle_idx, rangle_end, color, priority=25))

        bar_search = m.start()
        while True:
            bar_search = body.find("|", bar_search)
            if bar_search == -1 or bar_search >= rangle_idx:
                break
            spans.append(ColorSpan(bar_search, bar_search + 1, color, priority=25))
            bar_search += 1

    # 2. Ket: | ... \rangle or \vert ... \rangle
    for m in KET_DELIM_RE.finditer(body):
        full = m.group(0)
        bar_idx = m.start()
        bar_end = bar_idx + (5 if full.startswith(r"\vert") else 1)
        rangle_idx = m.start() + full.rfind(r"\rangle")
        rangle_end = rangle_idx + 7

        if not any(s.start == bar_idx for s in spans):
            spans.append(ColorSpan(bar_idx, bar_end, color, priority=25))
            spans.append(ColorSpan(rangle_idx, rangle_end, color, priority=25))

    # 3. Bra: \langle ... | or \langle ... \vert
    for m in BRA_DELIM_RE.finditer(body):
        full = m.group(0)
        langle_idx = m.start()
        langle_end = langle_idx + 7
        bar_idx = m.start() + max(full.rfind("|"), full.rfind(r"\vert"))
        bar_end = bar_idx + (5 if full.endswith(r"\vert") else 1)

        if not any(s.start == langle_idx for s in spans):
            spans.append(ColorSpan(langle_idx, langle_end, color, priority=25))
            spans.append(ColorSpan(bar_idx, bar_end, color, priority=25))

    return sorted(spans, key=lambda s: s.start)
