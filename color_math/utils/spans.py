"""Apply source-preserving color wrappers to exact LaTeX ranges."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorSpan:
    """A half-open source range that should receive one color."""

    start: int
    end: int
    color: str
    priority: int = 0


import re


def _crosses(left: ColorSpan, right: ColorSpan) -> bool:
    return (
        left.start < right.start < left.end < right.end
        or right.start < left.start < right.end < left.end
    )


def is_valid_tex_span(source: str, start: int, end: int) -> bool:
    """Validate that a span does not cross alignment boundaries or fracture environments."""
    content = source[start:end]
    if content.strip() in ("&", r"\\"):
        return False

    depth = 0
    env_depth = 0
    i = 0
    while i < len(content):
        c = content[i]
        if c == "%":
            nl = content.find("\n", i)
            i = len(content) if nl < 0 else nl + 1
            continue
        if c == "\\":
            if content.startswith(r"\begin{", i):
                env_depth += 1
            elif content.startswith(r"\end{", i):
                if env_depth == 0:
                    return False
                env_depth -= 1
            elif env_depth == 0 and depth == 0:
                if re.match(r"^\\\\(?:\[[^\]]*\])?(?:\s|\r|\n|$)", content[i:]):
                    return False
            i += 1
            continue
        if c in ("{", "["):
            depth += 1
        elif c in ("}", "]"):
            depth = max(0, depth - 1)
        elif c == "&" and env_depth == 0 and depth == 0:
            return False
        i += 1

    if env_depth != 0:
        return False
    return True


def select_color_spans(source: str, spans: list[ColorSpan]) -> list[ColorSpan]:
    """Keep valid nested/disjoint spans, preferring higher-priority edits."""

    candidates: dict[tuple[int, int], ColorSpan] = {}
    for span in spans:
        if not (0 <= span.start < span.end <= len(source)):
            continue
        if not is_valid_tex_span(source, span.start, span.end):
            continue
        key = (span.start, span.end)
        previous = candidates.get(key)
        if previous is None or span.priority > previous.priority:
            candidates[key] = span

    accepted: list[ColorSpan] = []
    for span in sorted(
        candidates.values(),
        key=lambda item: (-item.priority, item.start, -(item.end - item.start)),
    ):
        if any(_crosses(span, other) for other in accepted):
            continue
        accepted.append(span)

    return sorted(accepted, key=lambda item: (item.start, -item.end))


def apply_color_spans(source: str, spans: list[ColorSpan]) -> str:
    """Insert ``\\textcolor`` wrappers without changing the source itself."""

    selected = select_color_spans(source, spans)
    if not selected:
        return source

    openings: dict[int, list[ColorSpan]] = {}
    closings: dict[int, list[ColorSpan]] = {}
    events: set[int] = set()
    for span in selected:
        openings.setdefault(span.start, []).append(span)
        closings.setdefault(span.end, []).append(span)
        events.add(span.start)
        events.add(span.end)

    pieces: list[str] = []
    last_idx = 0
    for idx in sorted(events):
        if idx > last_idx:
            pieces.append(source[last_idx:idx])
        # Close inner spans first, then open outer spans first.
        for _ in sorted(
            closings.get(idx, ()),
            key=lambda item: item.start,
            reverse=True,
        ):
            pieces.append("}")
        for span in sorted(
            openings.get(idx, ()),
            key=lambda item: item.end,
            reverse=True,
        ):
            pieces.append(rf"\textcolor{{{span.color}}}{{")
        last_idx = idx

    if last_idx < len(source):
        pieces.append(source[last_idx:])

    return "".join(pieces)
