from __future__ import annotations

from .parsers.markdown_scanner import scan_markdown
from .utils.latex_helpers import (
    COMMAND_RE,
    read_color_wrapper,
    read_comment_end,
    read_verb_end,
)


def uncolor_fragment(text: str) -> str:
    r"""Remove nested ``\textcolor`` and legacy ``\color`` wrappers."""
    output: list[str] = []
    index = 0

    while index < len(text):
        if text[index] == "%":
            end = read_comment_end(text, index)
            output.append(text[index:end])
            index = end
            continue

        if text[index] == "\\":
            wrapper = read_color_wrapper(text, index)
            if wrapper is not None:
                value, next_index = wrapper
                if value:
                    output.append(uncolor_fragment(value))
                index = next_index
                if not value and index < len(text) and text[index] == " ":
                    index += 1
                continue

            verb = read_verb_end(text, index)
            if verb is not None:
                end, _ = verb
                output.append(text[index:end])
                index = end
                continue

            command = COMMAND_RE.match(text, index)
            if command is not None:
                output.append(command.group(0))
                index = command.end()
                continue

        output.append(text[index])
        index += 1

    return "".join(output)


def uncolor_text(text: str) -> str:
    r"""Remove wrappers in display and inline math; leave all other Markdown untouched."""
    scan = scan_markdown(text)
    all_spans = sorted(
        [*scan.math_blocks, *scan.math_inlines],
        key=lambda s: s.start,
    )
    if not all_spans:
        return uncolor_fragment(text)

    output: list[str] = []
    index = 0
    for span in all_spans:
        output.append(text[index:span.start])
        output.append(uncolor_fragment(text[span.start:span.end]))
        index = span.end
    output.append(text[index:])
    return "".join(output)
