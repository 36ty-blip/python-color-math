"""Physical units and metric prefixes disambiguation."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import COLORS
from ..utils.spans import ColorSpan


@dataclass
class UnitSpan:
    start: int
    end: int
    text: str


SI_UNITS = (
    r"m|s|g|Hz|N|Pa|J|W|C|V|F|T|H|mol|L|l|K|bar|atm|torr|eV|cal|rad|deg|\\Omega|dB|bps|B|Ω"
)
PREFIXES = r"k|M|G|T|c|m|n|p|f|d|da|\\mu|µ"
SAFE_MICRO_UNITS = r"m|s|g|mol|Hz|Pa|bar|rad|\\Omega|L|l"
AMBIGUOUS_MICRO_UNITS = r"N|A|V|F|H|W|J|C"


def find_unit_spans(body: str) -> list[UnitSpan]:
    """Scans LaTeX math body to identify physical unit spans."""
    spans: list[UnitSpan] = []

    def add_span(start: int, end: int, text: str) -> None:
        if start >= end:
            return
        if not any(start < s.end and end > s.start for s in spans):
            spans.append(UnitSpan(start, end, text))

    # 1a. \mu\text{...} or \mu\mathrm{...}
    micro_text_re = re.compile(
        r"\\mu\s*(?:\\(?:text|mathrm)\s*\{\s*([A-Za-z°℃%Ωμ/^0-9\s.\-]+?)\s*\})(?:\^\{?-?\d+\}?)?"
    )
    for m in micro_text_re.finditer(body):
        add_span(m.start(), m.end(), m.group(0))

    # 1b. Bare \mu with safe micro units: \mu m, \mu s, etc.
    safe_micro_re = re.compile(
        r"\\mu\s*(" + SAFE_MICRO_UNITS + r")(?![A-Za-z0-9_])(?:\^\{?-?\d+\}?)?"
    )
    for m in safe_micro_re.finditer(body):
        add_span(m.start(), m.end(), m.group(0))

    # 2. Degree units: ^\circ C, ^\circ\text{C}, ^\circ F
    deg_re = re.compile(r"\^\s*\\circ\s*(?:\\(?:text|mathrm)\s*\{[A-Za-z]+\}|[A-Za-z]+)")
    for m in deg_re.finditer(body):
        add_span(m.start(), m.end(), m.group(0))

    # 3. Units preceded by a number (Magnitude + Unit)
    num_unit_pattern = (
        r"(?:^|[^A-Za-z0-9_])(?:\d+(?:\.\d+)?|\.\d+)(?:\s*(?:\\times|\\cdot|·|\*)\s*10\^\{?[+-]?\d+\}?|\s*[eE][+-]?\d+)?(?:\s*|\,|\:|\;|\s*\\quad|\s*\\qquad|~)*"
        r"("
        r"\\(?:text|mathrm)\s*\{[^}]+\}(?:\^\{?-?\d+\}?)?"
        r"|"
        r"\\mu\s*(?:" + SAFE_MICRO_UNITS + r"|" + AMBIGUOUS_MICRO_UNITS + r")(?![A-Za-z0-9_])(?:\^\{?-?\d+\}?)?"
        r"|"
        r"(?:(?:" + PREFIXES + r")?(?:" + SI_UNITS + r"))(?:\/(?:(?:" + PREFIXES + r")?(?:" + SI_UNITS + r")))*(?:\^\{?-?\d+\}?)?(?![A-Za-z0-9_({])"
        r")"
    )
    for m in re.finditer(num_unit_pattern, body):
        full_match = m.group(0)
        unit_part = m.group(1)
        unit_offset = full_match.rfind(unit_part)
        unit_start = m.start() + unit_offset
        unit_end = unit_start + len(unit_part)
        add_span(unit_start, unit_end, unit_part)

    # 4. Standalone Text / mathrm units with \text{...} or \mathrm{...}
    text_unit_re = re.compile(
        r"\\(?:text|mathrm)\s*\{\s*([A-Za-z°℃%Ωμ/^0-9\s.\-]+?)\s*\}(?:\^\{?-?\d+\}?)?"
    )
    is_unit_re = re.compile(
        r"^(?:(?:" + PREFIXES + r")?(?:" + SI_UNITS + r"))(?:\/(?:(?:" + PREFIXES + r")?(?:" + SI_UNITS + r")))*(?:\^\{?-?\d+\}?)?$",
        re.IGNORECASE,
    )
    for m in text_unit_re.finditer(body):
        inner = m.group(1).strip()
        if is_unit_re.match(inner):
            add_span(m.start(), m.end(), m.group(0))

    return sorted(spans, key=lambda s: s.start)


def collect_unit_spans(
    body: str,
    palette: dict[str, str] | None = None,
    unit_spans: list[UnitSpan] | None = None,
) -> list[ColorSpan]:
    """Returns ColorSpans for units with unit color."""
    pal = palette or COLORS
    units = unit_spans if unit_spans is not None else find_unit_spans(body)
    unit_color = pal.get("unit", "#73daca")
    return [ColorSpan(u.start, u.end, unit_color, priority=25) for u in units]
