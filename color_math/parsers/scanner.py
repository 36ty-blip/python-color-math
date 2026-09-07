"""Collect generic, source-preserving LaTeX color spans."""

from __future__ import annotations

import re

from ..config import COLORS, FUNCTION_COMMANDS, SORTED_COLOR_COMMANDS
from ..utils.coloring import command_color
from ..utils.latex_helpers import read_color_command
from ..utils.spans import ColorSpan, apply_color_spans
from .latex_spans import (
    MATRIX_ENVIRONMENTS,
    UNARY_MACROS,
    find_all_operator_spans,
    find_operand_spans,
    find_script_argument_spans,
    read_command,
    read_environment_end,
    read_group_end,
    read_operand,
    skip_ignorable,
)


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")
LAYOUT_ENVIRONMENTS = MATRIX_ENVIRONMENTS | frozenset({
    "align",
    "align*",
    "aligned",
    "cases",
    "gather",
    "gather*",
    "gathered",
    "split",
})
STRUCTURED_COMMANDS = {
    "binom": 2,
    "boxed": 1,
    "cancel": 1,
    "dfrac": 2,
    "frac": 2,
    "overbrace": 1,
    "phantom": 1,
    "tfrac": 2,
    "underbrace": 1,
}
SEMANTIC_COLOR_NAMES = ("main", "derivative", "chain")


def _argument_range(
    source: str,
    start: int,
    end: int,
) -> tuple[int, int, int] | None:
    start = skip_ignorable(source, start, end)
    if start >= end:
        return None
    if source[start] in "{([":
        group_end = read_group_end(source, start, end)
        if group_end is None:
            return None
        return start + 1, group_end - 1, group_end
    if source[start] != "\\":
        return start, start + 1, start + 1
    operand = read_operand(source, start, end)
    if operand is None:
        return start, start + 1, start + 1
    return operand.start, operand.end, operand.end


def _operand_color_spans(
    source: str,
    start: int,
    end: int,
    offset: int,
) -> list[ColorSpan]:
    spans: list[ColorSpan] = []
    semantic_index = 0
    for operand in find_operand_spans(source, start, end):
        if operand.kind == "number":
            color = COLORS["orange"]
        else:
            color = COLORS[
                SEMANTIC_COLOR_NAMES[
                    (offset + semantic_index) % len(SEMANTIC_COLOR_NAMES)
                ]
            ]
            semantic_index += 1
        spans.append(ColorSpan(operand.start, operand.end, color, priority=5))
    return spans


def _environment_content(
    source: str,
    start: int,
    end: int,
) -> tuple[str, int, int, int] | None:
    command = read_command(source, start, end)
    if command is None or command[0] != "begin":
        return None
    name_start = skip_ignorable(source, command[1], end)
    name_end = read_group_end(source, name_start, end)
    environment = read_environment_end(source, start, end)
    if name_end is None or environment is None:
        return None
    name, environment_end = environment
    content_start = name_end
    if name == "array":
        preamble_start = skip_ignorable(source, content_start, environment_end)
        preamble_end = read_group_end(source, preamble_start, environment_end)
        if preamble_end is not None:
            content_start = preamble_end
    closing_start = source.rfind(r"\end", content_start, environment_end)
    if closing_start < content_start:
        return None
    return name, content_start, closing_start, environment_end


def _layout_cells(source: str, start: int, end: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    cell_start = start
    index = start
    while index < end:
        if source[index] == "%":
            newline = source.find("\n", index + 1, end)
            index = end if newline < 0 else newline + 1
            continue
        if source[index] == "&":
            cells.append((cell_start, index))
            cell_start = index + 1
            index += 1
            continue
        if source[index] == "\\":
            command = read_command(source, index, end)
            if command is not None and command[0] == "\\":
                cells.append((cell_start, index))
                cell_start = command[1]
                index = command[1]
                continue
        operand = read_operand(source, index, end)
        if operand is not None:
            index = max(index + 1, operand.end)
            continue
        index += 1
    cells.append((cell_start, end))
    return cells


def collect_structured_spans(body: str) -> list[ColorSpan]:
    """Color operands inside structured commands and layout environments."""
    spans: list[ColorSpan] = []
    index = 0
    while index < len(body):
        if body[index] != "\\":
            index += 1
            continue
        command = read_command(body, index, len(body))
        if command is None:
            index += 1
            continue
        name, command_end = command

        if name == "begin":
            environment = _environment_content(body, index, len(body))
            if environment is not None and environment[0] in LAYOUT_ENVIRONMENTS:
                _, content_start, content_end, _ = environment
                for offset, (start, end) in enumerate(
                    _layout_cells(body, content_start, content_end)
                ):
                    spans.extend(_operand_color_spans(body, start, end, offset))

        argument_count = STRUCTURED_COMMANDS.get(name)
        if name in UNARY_MACROS:
            argument_count = 1
        if name == "sqrt":
            optional_start = skip_ignorable(body, command_end, len(body))
            if optional_start < len(body) and body[optional_start] == "[":
                optional_end = read_group_end(body, optional_start, len(body))
                if optional_end is not None:
                    spans.extend(
                        _operand_color_spans(
                            body,
                            optional_start + 1,
                            optional_end - 1,
                            1,
                        )
                    )
                    command_end = optional_end
            argument_count = 1

        argument_start = command_end
        for offset in range(argument_count or 0):
            argument = _argument_range(body, argument_start, len(body))
            if argument is None:
                break
            start, end, argument_start = argument
            spans.extend(_operand_color_spans(body, start, end, offset))
        index = command[1]
    return spans


def collect_operator_spans(
    body: str,
    start: int = 0,
    end: int | None = None,
) -> list[ColorSpan]:
    """Color complete operators, including attached limits and scripts."""
    spans: list[ColorSpan] = []
    for operator in find_all_operator_spans(body, start, end):
        command = COMMAND_RE.match(body, operator.start, operator.end)
        if command is not None:
            spans.append(
                ColorSpan(
                    operator.start,
                    operator.end,
                    command_color(command.group(0)),
                    priority=30,
                )
            )
    return spans


def collect_scanner_spans(body: str) -> list[ColorSpan]:
    """Find generic operators and script arguments without rewriting LaTeX."""
    scripts = find_script_argument_spans(body)
    operators = find_all_operator_spans(body)
    spans = [
        ColorSpan(
            item.start,
            item.end,
            COLORS["chain" if item.kind == "subscript" else "upper"],
            priority=10,
        )
        for item in scripts
    ]
    spans.extend(collect_operator_spans(body))
    spans.extend(collect_structured_spans(body))
    script_ranges = tuple((item.start, item.end) for item in scripts)
    operator_ranges = tuple((item.start, item.end) for item in operators)

    index = 0
    while index < len(body):
        if body[index] == "%":
            line_end = index + 1
            while line_end < len(body) and body[line_end] not in "\r\n":
                line_end += 1
            if (
                line_end < len(body)
                and body[line_end] == "\r"
                and line_end + 1 < len(body)
                and body[line_end + 1] == "\n"
            ):
                line_end += 2
            elif line_end < len(body):
                line_end += 1
            index = line_end
            continue

        existing = read_color_command(body, index)
        if existing is not None:
            index = existing[1]
            continue

        operand = read_operand(body, index)
        if operand is not None and operand.kind == "opaque":
            index = operand.end
            continue

        containing_operator = next(
            (
                (start, end)
                for start, end in operator_ranges
                if start <= index < end
            ),
            None,
        )
        if containing_operator is not None:
            index = containing_operator[1]
            continue

        containing_script = next(
            (
                (start, end)
                for start, end in script_ranges
                if start <= index < end
            ),
            None,
        )
        if containing_script is not None:
            index = containing_script[1]
            continue

        command_match = COMMAND_RE.match(body, index)
        if command_match is not None:
            command = command_match.group(0)
            if command in SORTED_COLOR_COMMANDS:
                spans.append(
                    ColorSpan(
                        index,
                        command_match.end(),
                        command_color(command),
                    )
                )
            elif command in FUNCTION_COMMANDS:
                spans.append(
                    ColorSpan(
                        index,
                        command_match.end(),
                        COLORS["main"],
                        priority=20,
                    )
                )
            elif command == r"\operatorname":
                argument_start = command_match.end()
                if argument_start < len(body) and body[argument_start] == "*":
                    argument_start += 1
                argument_start = skip_ignorable(body, argument_start, len(body))
                argument_end = read_group_end(body, argument_start, len(body))
                if argument_end is not None:
                    spans.append(
                        ColorSpan(index, argument_end, COLORS["main"], priority=20)
                    )
            index = command_match.end()
            if index < len(body) and body[index] == "*":
                index += 1
            continue

        command = next(
            (
                candidate
                for candidate in SORTED_COLOR_COMMANDS
                if not candidate.startswith("\\")
                and body.startswith(candidate, index)
            ),
            None,
        )
        if command is not None:
            spans.append(
                ColorSpan(index, index + len(command), command_color(command))
            )
            index += len(command)
            continue

        index += 1

    return spans


def color_latex_body_with_scanner(body: str) -> str:
    """Color generic LaTeX tokens by inserting scoped wrappers."""
    return apply_color_spans(body, collect_scanner_spans(body))
