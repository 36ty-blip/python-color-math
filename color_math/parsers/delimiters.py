"""Rainbow delimiters parser for balanced parentheses, brackets, and braces."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import RAINBOW_DELIMITER_COLORS
from ..utils.spans import ColorSpan


@dataclass
class DelimiterItem:
    delim_type: str
    start: int
    end: int
    is_left_right: bool


@dataclass
class DelimiterPair:
    open_item: DelimiterItem
    close_item: DelimiterItem
    depth: int


def skip_whitespace(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def skip_comment(text: str, start: int) -> int:
    idx = start + 1
    while idx < len(text) and text[idx] not in ("\r", "\n"):
        idx += 1
    if idx < len(text) and text[idx] == "\r" and idx + 1 < len(text) and text[idx + 1] == "\n":
        return idx + 2
    return min(idx + 1, len(text))


def get_delimiter_type(delim: str) -> str:
    if delim in ("(", ")"):
        return "paren"
    if delim in ("[", "]"):
        return "bracket"
    if delim in (r"\{", r"\}"):
        return "brace"
    if delim in (r"\langle", r"\rangle"):
        return "angle"
    if delim in ("|", r"\|"):
        return "pipe"
    return "other"


def find_delimiter_pairs(text: str) -> list[DelimiterPair]:
    """Parses all balanced delimiter pairs in a LaTeX string."""
    pairs: list[DelimiterPair] = []
    stack: list[tuple[DelimiterItem, int]] = []

    idx = 0
    while idx < len(text):
        if text[idx] == "%":
            idx = skip_comment(text, idx)
            continue

        # Check \left / \right
        if text.startswith(r"\left", idx):
            after_left = skip_whitespace(text, idx + 5)
            m = re.match(r"^(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\||\.)", text[after_left:])
            if m:
                delim_str = m.group(1)
                delim_end = after_left + len(delim_str)
                dtype = get_delimiter_type(delim_str)
                depth = len(stack)
                item = DelimiterItem(dtype, idx, delim_end, is_left_right=True)
                stack.append((item, depth))
                idx = delim_end
                continue

        if text.startswith(r"\right", idx):
            after_right = skip_whitespace(text, idx + 6)
            m = re.match(r"^(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\||\.)", text[after_right:])
            if m:
                delim_str = m.group(1)
                delim_end = after_right + len(delim_str)
                dtype = get_delimiter_type(delim_str)

                match_idx = -1
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0].is_left_right:
                        match_idx = i
                        break

                if match_idx != -1:
                    matched, matched_depth = stack.pop(match_idx)
                    close_item = DelimiterItem(dtype, idx, delim_end, is_left_right=True)
                    pairs.append(DelimiterPair(matched, close_item, matched_depth))
                idx = delim_end
                continue

        # Regular bare delimiters
        ch = text[idx]
        if ch in ("(", "[") or text.startswith(r"\{", idx):
            is_brace = text.startswith(r"\{", idx)
            delim_str = r"\{" if is_brace else ch
            delim_end = idx + (2 if is_brace else 1)
            dtype = get_delimiter_type(delim_str)
            depth = len(stack)
            item = DelimiterItem(dtype, idx, delim_end, is_left_right=False)
            stack.append((item, depth))
            idx = delim_end
            continue

        if ch in (")", "]") or text.startswith(r"\}", idx):
            is_brace = text.startswith(r"\}", idx)
            delim_str = r"\}" if is_brace else ch
            delim_end = idx + (2 if is_brace else 1)
            dtype = get_delimiter_type(delim_str)

            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == dtype:
                    match_idx = i
                    break

            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem(dtype, idx, delim_end, is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            idx = delim_end
            continue

        idx += 1

    return pairs


def collect_delimiter_spans(
    body: str,
    palette: list[str] | None = None,
) -> list[ColorSpan]:
    """Returns color spans for rainbow delimiters colored by nesting depth."""
    colors = palette or RAINBOW_DELIMITER_COLORS
    pairs = find_delimiter_pairs(body)
    spans: list[ColorSpan] = []

    for pair in pairs:
        color = colors[pair.depth % len(colors)]
        spans.append(ColorSpan(pair.open_item.start, pair.open_item.end, color, priority=22))
        spans.append(ColorSpan(pair.close_item.start, pair.close_item.end, color, priority=22))

    return spans
