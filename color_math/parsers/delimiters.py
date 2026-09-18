"""Rainbow delimiters parser for balanced parentheses, brackets, and braces."""
from __future__ import annotations
from dataclasses import dataclass
import re

from ..config import RAINBOW_DELIMITER_COLORS
from ..utils.latex_helpers import (
    COMMAND_RE,
    read_color_command,
    skip_environment_head,
)
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


@dataclass
class DelimiterScanResult:
    pairs: list[DelimiterPair]
    unmatched: list[DelimiterItem]


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
    if delim in ("{", "}"):
        return "bare_brace"
    if delim in (r"\langle", r"\rangle"):
        return "angle"
    if delim in ("|", r"\|"):
        return "pipe"
    return "other"


SIZED_OPEN_RE = re.compile(
    r"^(\\(?:big|Big|bigg|Bigg)l)(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\|)"
)
SIZED_CLOSE_RE = re.compile(
    r"^(\\(?:big|Big|bigg|Bigg)r)(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\|)"
)


def find_delimiter_scan(
    text: str,
    include_bare_braces: bool = False,
) -> DelimiterScanResult:
    """
    Scans all delimiter pairs and identifies unmatched/unclosed delimiters.
    Supports parentheses (), brackets [], escaped braces \\{\\}, bare braces {},
    angle brackets \\langle \\rangle, and sized delimiters \\bigl...\\bigr.
    """
    pairs: list[DelimiterPair] = []
    unmatched: list[DelimiterItem] = []
    stack: list[tuple[DelimiterItem, int]] = []

    idx = 0
    while idx < len(text):
        if text[idx] == "%":
            idx = skip_comment(text, idx)
            continue

        # Skip environment declarations like \begin{matrix}, \begin{array}{cc|c}, \end{matrix}
        if text.startswith(r"\begin", idx) or text.startswith(r"\end", idx):
            is_begin = text.startswith(r"\begin", idx)
            cmd_name = r"\begin" if is_begin else r"\end"
            cmd_end = idx + len(cmd_name)
            env_head_end = skip_environment_head(text, cmd_name, cmd_end)
            if env_head_end is not None:
                idx = env_head_end
                continue

        # Skip existing color commands like \textcolor{...}{...} so inner braces are not counted as bare delimiters
        color_cmd = read_color_command(text, idx)
        if color_cmd is not None:
            idx = color_cmd[1]
            continue

        # Check \left / \right
        if text.startswith(r"\left", idx):
            after_left = skip_whitespace(text, idx + 5)
            m = re.match(
                r"^(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\||\.)",
                text[after_left:],
            )
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
            m = re.match(
                r"^(\(|\)|\[|\]|\\\{|\\\}|\\langle|\\rangle|\||\\\||\.)",
                text[after_right:],
            )
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
                else:
                    unmatched.append(DelimiterItem(dtype, idx, delim_end, is_left_right=True))
                idx = delim_end
                continue

        # Sized delimiters: \bigl, \Bigl, \biggl, \Biggl and closing \bigr, \Bigr, etc.
        m_sized_open = SIZED_OPEN_RE.match(text[idx:])
        if m_sized_open:
            full_str = m_sized_open.group(0)
            delim_str = m_sized_open.group(2)
            dtype = get_delimiter_type(delim_str)
            depth = len(stack)
            item = DelimiterItem(dtype, idx, idx + len(full_str), is_left_right=False)
            stack.append((item, depth))
            idx += len(full_str)
            continue

        m_sized_close = SIZED_CLOSE_RE.match(text[idx:])
        if m_sized_close:
            full_str = m_sized_close.group(0)
            delim_str = m_sized_close.group(2)
            dtype = get_delimiter_type(delim_str)

            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == dtype:
                    match_idx = i
                    break

            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem(dtype, idx, idx + len(full_str), is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            else:
                unmatched.append(DelimiterItem(dtype, idx, idx + len(full_str), is_left_right=False))
            idx += len(full_str)
            continue

        # Escaped set braces \{ and \}
        if text.startswith(r"\{", idx):
            depth = len(stack)
            item = DelimiterItem("brace", idx, idx + 2, is_left_right=False)
            stack.append((item, depth))
            idx += 2
            continue

        if text.startswith(r"\}", idx):
            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == "brace":
                    match_idx = i
                    break
            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem("brace", idx, idx + 2, is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            else:
                unmatched.append(DelimiterItem("brace", idx, idx + 2, is_left_right=False))
            idx += 2
            continue

        # Bare angle brackets \langle and \rangle
        if text.startswith(r"\langle", idx):
            depth = len(stack)
            item = DelimiterItem("angle", idx, idx + 7, is_left_right=False)
            stack.append((item, depth))
            idx += 7
            continue

        if text.startswith(r"\rangle", idx):
            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == "angle":
                    match_idx = i
                    break
            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem("angle", idx, idx + 7, is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            else:
                unmatched.append(DelimiterItem("angle", idx, idx + 7, is_left_right=False))
            idx += 7
            continue

        # Standard brackets ( ... ) and [ ... ]
        ch = text[idx]
        if ch in ("(", "["):
            dtype = "paren" if ch == "(" else "bracket"
            depth = len(stack)
            item = DelimiterItem(dtype, idx, idx + 1, is_left_right=False)
            stack.append((item, depth))
            idx += 1
            continue

        if ch in (")", "]"):
            dtype = "paren" if ch == ")" else "bracket"
            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == dtype:
                    match_idx = i
                    break
            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem(dtype, idx, idx + 1, is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            else:
                unmatched.append(DelimiterItem(dtype, idx, idx + 1, is_left_right=False))
            idx += 1
            continue

        # Bare grouping braces { ... }
        if include_bare_braces and ch == "{":
            depth = len(stack)
            item = DelimiterItem("bare_brace", idx, idx + 1, is_left_right=False)
            stack.append((item, depth))
            idx += 1
            continue

        if include_bare_braces and ch == "}":
            match_idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if not stack[i][0].is_left_right and stack[i][0].delim_type == "bare_brace":
                    match_idx = i
                    break
            if match_idx != -1:
                matched, matched_depth = stack.pop(match_idx)
                close_item = DelimiterItem("bare_brace", idx, idx + 1, is_left_right=False)
                pairs.append(DelimiterPair(matched, close_item, matched_depth))
            else:
                unmatched.append(DelimiterItem("bare_brace", idx, idx + 1, is_left_right=False))
            idx += 1
            continue

        # Skip generic LaTeX commands like \frac, \sqrt, etc.
        if ch == "\\":
            cmd_match = COMMAND_RE.match(text, idx)
            if cmd_match:
                idx += len(cmd_match.group(0))
                continue

        idx += 1

    # Remaining items on stack were never closed!
    for remaining, _ in stack:
        unmatched.append(remaining)

    return DelimiterScanResult(pairs=pairs, unmatched=unmatched)


def find_delimiter_pairs(
    text: str,
    include_bare_braces: bool = False,
) -> list[DelimiterPair]:
    """Parses all balanced delimiter pairs in a LaTeX string."""
    return find_delimiter_scan(text, include_bare_braces=include_bare_braces).pairs


def collect_delimiter_spans(
    body: str,
    palette: list[str] | None = None,
    for_latex_wrap: bool = False,
    include_bare_braces: bool = False,
    highlight_unmatched: bool = False,
    only_unmatched: bool = False,
    error_color: str = "#f7768e",
) -> list[ColorSpan]:
    """
    Returns color spans for rainbow delimiters colored by nesting depth.

    SAFETY GUARD: If for_latex_wrap is True (LaTeX baking), we NEVER include bare braces!
    """
    effective_bare = False if for_latex_wrap else include_bare_braces
    scan = find_delimiter_scan(body, include_bare_braces=include_bare_braces)
    colors = palette or RAINBOW_DELIMITER_COLORS
    spans: list[ColorSpan] = []

    if not only_unmatched:
        for pair in scan.pairs:
            # SAFETY GUARD: Never emit bare braces into LaTeX string output
            if for_latex_wrap and pair.open_item.delim_type == "bare_brace":
                continue
            if pair.open_item.delim_type == "bare_brace" and not effective_bare:
                continue

            color = colors[pair.depth % len(colors)]
            if for_latex_wrap and pair.open_item.is_left_right:
                # Wrap entire \left...\right expression so KaTeX/MathJax does not fail group boundaries
                spans.append(ColorSpan(pair.open_item.start, pair.close_item.end, color, priority=24))
            else:
                spans.append(ColorSpan(pair.open_item.start, pair.open_item.end, color, priority=25))
                spans.append(ColorSpan(pair.close_item.start, pair.close_item.end, color, priority=25))

    # Highlight unmatched delimiters (unclosed opening or stray closing)
    if highlight_unmatched:
        for item in scan.unmatched:
            # SAFETY GUARD: Never emit bare braces into LaTeX string output
            if for_latex_wrap and item.delim_type == "bare_brace":
                continue
            if item.delim_type == "bare_brace" and not include_bare_braces and not only_unmatched:
                continue
            spans.append(ColorSpan(item.start, item.end, error_color, priority=99))

    return sorted(spans, key=lambda s: s.start)
