# color_math/parsers/alignment.py

from __future__ import annotations

from dataclasses import dataclass

from ..config import COLORS
from ..utils.spans import ColorSpan


@dataclass(frozen=True)
class AlignmentSpan:
    start: int
    end: int
    text: str


def find_alignment_spans(body: str) -> list[AlignmentSpan]:
    """Finds spans of matrix & alignment delimiters (& and \\\\)."""
    spans: list[AlignmentSpan] = []
    index = 0
    while index < len(body):
        if body[index] == "%":
            line_end = index + 1
            while line_end < len(body) and body[line_end] not in "\r\n":
                line_end += 1
            index = line_end
            continue

        if body[index] == "&":
            spans.append(AlignmentSpan(index, index + 1, "&"))
            index += 1
            continue

        if body.startswith(r"\\", index):
            spans.append(AlignmentSpan(index, index + 2, r"\\"))
            index += 2
            continue

        index += 1

    return spans


def collect_alignment_spans(
    body: str,
    palette: dict[str, str] | None = None,
) -> list[ColorSpan]:
    """Scans LaTeX text for matrix & alignment delimiters (& and \\\\)."""
    pal = palette or COLORS
    color = pal.get("arrow", "#f7768e")
    spans: list[ColorSpan] = []
    index = 0
    while index < len(body):
        if body[index] == "%":
            line_end = index + 1
            while line_end < len(body) and body[line_end] not in "\r\n":
                line_end += 1
            index = line_end
            continue

        if body[index] == "&":
            spans.append(ColorSpan(index, index + 1, color, priority=25))
            index += 1
            continue

        if body.startswith(r"\\", index):
            spans.append(ColorSpan(index, index + 2, color, priority=25))
            index += 2
            continue

        index += 1

    return spans
