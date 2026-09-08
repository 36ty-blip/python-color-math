"""Thin document adapters around the existing Markdown math converter."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import ColorMathOptions
from .converters.block import convert_math_block, convert_text
from .undo import uncolor_fragment, uncolor_text
from .utils.latex_helpers import read_comment_end, read_verb_end


FORMATS = ("auto", "markdown", "jupyter", "anki", "tex")
ANKI_DELIMITERS = (
    (r"\[", r"\]"),
    (r"\(", r"\)"),
    ("[$$]", "[/$$]"),
    ("[$]", "[/$]"),
)
MATH_ENVIRONMENTS = {
    "align", "align*", "alignat", "alignat*", "displaymath",
    "equation", "equation*", "eqnarray", "eqnarray*", "flalign",
    "flalign*", "gather", "gather*", "math", "multline", "multline*",
}
VERBATIM_ENVIRONMENTS = {"Verbatim", "lstlisting", "minted", "verbatim", "verbatim*"}
BEGIN_RE = re.compile(r"\\begin\{([^{}]+)\}")
HEX_COLOR_RE = re.compile(r"\\textcolor\{#([0-9A-Fa-f]{6})\}")
NATIVE_COLOR_RE = re.compile(r"\\textcolor\{colormath([0-9A-Fa-f]{6})\}")
NATIVE_BEGIN = "% color-math: begin generated xcolor support"
NATIVE_END = "% color-math: end generated xcolor support"
NATIVE_BLOCK_RE = re.compile(
    rf"(?m)^{re.escape(NATIVE_BEGIN)}(?:\r?\n).*?^{re.escape(NATIVE_END)}(?:\r?\n)?",
    re.DOTALL,
)


class AdapterError(ValueError):
    """A document cannot be safely handled by its selected adapter."""


def detect_format(path: Path | None, requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    if path is not None and path.suffix.lower() == ".ipynb":
        return "jupyter"
    if path is not None and path.suffix.lower() in {".tex", ".latex"}:
        return "tex"
    return "markdown"


def transform_document(
    text: str,
    format_name: str,
    undo: bool = False,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    if format_name == "markdown":
        return uncolor_text(text) if undo else convert_text(text, palette=palette, options=options)
    if format_name == "jupyter":
        return _transform_notebook(text, undo, palette=palette, options=options)
    if format_name == "anki":
        return _transform_delimited(text, ANKI_DELIMITERS, undo, palette=palette, options=options)
    if format_name == "tex":
        return _transform_tex(text, undo, palette=palette, options=options)
    raise AdapterError(f"unsupported format: {format_name}")


def _transform_fragment(
    text: str,
    undo: bool,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    if undo:
        return uncolor_fragment(text)
    converted = convert_math_block(f"$${text}$$", palette=palette, options=options)
    return converted[2:-2]


def _transform_notebook(
    text: str,
    undo: bool,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    try:
        notebook = json.loads(text)
    except json.JSONDecodeError as error:
        raise AdapterError(f"invalid Jupyter JSON at line {error.lineno}: {error.msg}") from error

    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise AdapterError("Jupyter notebook must contain a cells list")

    changed = False
    for index, cell in enumerate(notebook["cells"]):
        if not isinstance(cell, dict) or cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        if isinstance(source, str):
            joined = source
        elif isinstance(source, list) and all(isinstance(part, str) for part in source):
            joined = "".join(source)
        else:
            raise AdapterError(f"markdown cell {index + 1} has an invalid source")

        converted = uncolor_text(joined) if undo else convert_text(joined, palette=palette, options=options)
        if converted == joined:
            continue
        cell["source"] = (
            converted
            if isinstance(source, str)
            else converted.splitlines(keepends=True) or ([""] if source else [])
        )
        changed = True

    if not changed:
        return text

    indentation = re.search(r"\n([ \t]+)\"", text)
    if indentation is None:
        output = json.dumps(notebook, ensure_ascii=False, separators=(",", ":"))
    else:
        output = json.dumps(notebook, ensure_ascii=False, indent=indentation.group(1))
    ending = "\r\n" if text.endswith("\r\n") else "\n" if text.endswith("\n") else ""
    return output + ending


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _next_delimiter(
    text: str,
    start: int,
    delimiters: tuple[tuple[str, str], ...],
) -> tuple[int, str, str] | None:
    matches = [
        (position, opening, closing)
        for opening, closing in delimiters
        if (position := _find_unescaped(text, opening, start)) >= 0
    ]
    return min(matches, default=None, key=lambda match: match[0])


def _find_unescaped(text: str, token: str, start: int) -> int:
    while (position := text.find(token, start)) >= 0:
        if not _is_escaped(text, position):
            return position
        start = position + len(token)
    return -1


def _transform_delimited(
    text: str,
    delimiters: tuple[tuple[str, str], ...],
    undo: bool,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    output: list[str] = []
    index = 0
    while match := _next_delimiter(text, index, delimiters):
        start, opening, closing = match
        end = _find_unescaped(text, closing, start + len(opening))
        if end < 0:
            break
        output.append(text[index:start + len(opening)])
        output.append(_transform_fragment(text[start + len(opening):end], undo, palette=palette, options=options))
        output.append(closing)
        index = end + len(closing)
    output.append(text[index:])
    return "".join(output)


def _find_active(text: str, token: str, start: int) -> int:
    index = start
    while index < len(text):
        if text[index] == "%" and not _is_escaped(text, index):
            index = read_comment_end(text, index)
            continue
        if text[index] == "\\":
            verb = read_verb_end(text, index)
            if verb is not None:
                index = verb[0]
                continue
        if text.startswith(token, index) and not _is_escaped(text, index):
            return index
        index += 1
    return -1


def _find_dollar(text: str, start: int, width: int) -> int:
    token = "$" * width
    index = start
    while (index := _find_active(text, token, index)) >= 0:
        before = index > 0 and text[index - 1] == "$"
        after = index + width < len(text) and text[index + width] == "$"
        if not before and not after:
            return index
        index += width
    return -1


def _transform_tex_math(
    text: str,
    undo: bool,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        if text[index] == "%" and not _is_escaped(text, index):
            end = read_comment_end(text, index)
            output.append(text[index:end])
            index = end
            continue

        if text[index] == "\\":
            verb = read_verb_end(text, index)
            if verb is not None:
                end = verb[0]
                output.append(text[index:end])
                index = end
                continue

            environment = BEGIN_RE.match(text, index)
            if environment is not None:
                name = environment.group(1)
                closing = rf"\end{{{name}}}"
                end_start = _find_active(text, closing, environment.end())
                if end_start >= 0 and name in VERBATIM_ENVIRONMENTS:
                    end = end_start + len(closing)
                    output.append(text[index:end])
                    index = end
                    continue
                if end_start >= 0 and name in MATH_ENVIRONMENTS:
                    end = end_start + len(closing)
                    output.append(_transform_fragment(text[index:end], undo, palette=palette, options=options))
                    index = end
                    continue

            pair = next(
                ((opening, closing) for opening, closing in ((r"\[", r"\]"), (r"\(", r"\)")) if text.startswith(opening, index)),
                None,
            )
            if pair is not None:
                opening, closing = pair
                end_start = _find_active(text, closing, index + len(opening))
                if end_start >= 0:
                    output.append(opening)
                    output.append(_transform_fragment(text[index + len(opening):end_start], undo, palette=palette, options=options))
                    output.append(closing)
                    index = end_start + len(closing)
                    continue

        if text[index] == "$" and not _is_escaped(text, index):
            width = 2 if text.startswith("$$", index) else 1
            end_start = _find_dollar(text, index + width, width)
            if end_start >= 0:
                delimiter = "$" * width
                output.append(delimiter)
                output.append(_transform_fragment(text[index + width:end_start], undo, palette=palette, options=options))
                output.append(delimiter)
                index = end_start + width
                continue

        output.append(text[index])
        index += 1
    return "".join(output)


def _native_support(text: str) -> str:
    translated = HEX_COLOR_RE.sub(
        lambda match: rf"\textcolor{{colormath{match.group(1).lower()}}}",
        text,
    )
    colors = sorted({match.lower() for match in NATIVE_COLOR_RE.findall(translated)})
    if not colors:
        return translated

    newline = "\r\n" if "\r\n" in translated else "\n"
    lines = [NATIVE_BEGIN]
    user_document = NATIVE_BLOCK_RE.sub("", translated)
    if not re.search(r"\\usepackage(?:\[[^]]*\])?\{[^}]*\bxcolor\b[^}]*\}", user_document):
        lines.append(r"\usepackage{xcolor}")
    lines.extend(
        rf"\definecolor{{colormath{color}}}{{HTML}}{{{color.upper()}}}"
        for color in colors
    )
    lines.append(NATIVE_END)
    block = newline.join(lines) + newline

    if NATIVE_BLOCK_RE.search(translated):
        return NATIVE_BLOCK_RE.sub(lambda _: block, translated, count=1)
    document_class = re.search(r"(?m)^\\documentclass[^\r\n]*(?:\r?\n|$)", translated)
    insertion = document_class.end() if document_class else 0
    return translated[:insertion] + block + translated[insertion:]


def _transform_tex(
    text: str,
    undo: bool,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> str:
    if undo:
        return _transform_tex_math(NATIVE_BLOCK_RE.sub("", text), True, palette=palette, options=options)
    return _native_support(_transform_tex_math(text, False, palette=palette, options=options))
