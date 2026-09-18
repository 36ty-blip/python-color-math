"""Lossless bidirectional converter between standard LaTeX math commands and Unicode math glyphs.

Only converts tokens within math blocks/inlines, protecting delimiters and non-math prose.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..unicode import (
    UNICODE_DIFFERENTIALS,
    UNICODE_CONSTANTS,
    UNICODE_VECTORS,
    UNICODE_INTEGRALS,
    UNICODE_BIG_OPERATORS,
    UNICODE_RELATIONS,
    UNICODE_ARROWS,
    UNICODE_SETS,
    UNICODE_MULTIPLICATION,
    UNICODE_ADDITIVE,
    UNICODE_GREEK_LOWER_STANDARD,
    UNICODE_GREEK_LOWER_PLANE1,
    UNICODE_GREEK_UPPER_STANDARD,
    UNICODE_GREEK_UPPER_PLANE1,
    PROTECTED_DELIMITER_MACROS,
    DELIMITER_AUTO_REPAIR,
)
from ..parsers.markdown_scanner import scan_markdown


@dataclass(frozen=True)
class UnicodeConversionOptions:
    convert_definite_integrals: bool = False  # default: False (preserves \int_a^b)
    convert_bounded_operators: bool = False   # default: False (preserves \sum_{i=1}^n)
    greek_style: Literal["plane1", "standard"] = "plane1"  # "plane1" (𝜓) vs "standard" (ψ)
    convert_prose_to_unicode: bool = False    # default: False (protects prose)
    convert_prose_to_latex: bool = False     # default: False (𝜓 in prose preserved)


DELIMITER_PREFIX_RE = re.compile(
    r"(?:\\(?:left|right|middle|bigl|bigr|Bigl|Bigr|biggl|biggr|Biggl|Biggr|bigm|Bigm))\s*$"
)


def _is_protected_delimiter(body: str, cmd_start: int) -> bool:
    prefix_text = body[:cmd_start]
    return bool(DELIMITER_PREFIX_RE.search(prefix_text))


def _has_limits(body: str, cmd_end: int) -> bool:
    idx = cmd_end
    while idx < len(body) and body[idx].isspace():
        idx += 1
    return idx < len(body) and body[idx] in ("_", "^")


def get_latex_to_unicode_map(
    options: UnicodeConversionOptions | None = None,
) -> list[tuple[str, str]]:
    opts = options or UnicodeConversionOptions()
    greek_lower = (
        UNICODE_GREEK_LOWER_STANDARD
        if opts.greek_style == "standard"
        else UNICODE_GREEK_LOWER_PLANE1
    )
    greek_upper = (
        UNICODE_GREEK_UPPER_STANDARD
        if opts.greek_style == "standard"
        else UNICODE_GREEK_UPPER_PLANE1
    )

    raw_map: dict[str, str] = {
        **UNICODE_DIFFERENTIALS,
        **UNICODE_CONSTANTS,
        **UNICODE_VECTORS,
        **UNICODE_RELATIONS,
        **UNICODE_ARROWS,
        **UNICODE_SETS,
        **UNICODE_MULTIPLICATION,
        **UNICODE_ADDITIVE,
        **greek_lower,
        **greek_upper,
    }

    # Sort keys by length descending to match longer commands first
    return sorted(raw_map.items(), key=lambda item: len(item[0]), reverse=True)


def get_unicode_to_latex_map() -> list[tuple[str, str]]:
    mapping: dict[str, str] = {}
    sources = (
        UNICODE_DIFFERENTIALS,
        UNICODE_CONSTANTS,
        UNICODE_VECTORS,
        UNICODE_INTEGRALS,
        UNICODE_BIG_OPERATORS,
        UNICODE_RELATIONS,
        UNICODE_ARROWS,
        UNICODE_SETS,
        UNICODE_MULTIPLICATION,
        UNICODE_ADDITIVE,
        UNICODE_GREEK_LOWER_PLANE1,
        UNICODE_GREEK_LOWER_STANDARD,
        UNICODE_GREEK_UPPER_PLANE1,
        UNICODE_GREEK_UPPER_STANDARD,
    )
    for src in sources:
        for tex, uni in src.items():
            if uni not in mapping:
                mapping[uni] = tex

    if "𝝍" not in mapping:
        mapping["𝝍"] = r"\psi"

    return sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)


CMD_RE = re.compile(r"^\\[A-Za-z]+")
DELIM_REPAIR_RE = re.compile(
    r"(\\(?:left|right|middle|bigl|bigr|Bigl|Bigr|biggl|biggr|Biggl|Biggr|bigm|Bigm)\s*)([⟨⟩⌈⌉⌊⌋‖⎸])"
)


def convert_latex_to_unicode(
    math_body: str,
    options: UnicodeConversionOptions | None = None,
) -> str:
    opts = options or UnicodeConversionOptions()
    mapping = get_latex_to_unicode_map(opts)
    mapping_dict = dict(mapping)
    result: list[str] = []
    idx = 0

    while idx < len(math_body):
        if math_body[idx] == "\\":
            match = CMD_RE.match(math_body[idx:])
            if match:
                cmd = match.group(0)
                cmd_name = cmd[1:]
                cmd_end = idx + len(cmd)

                # 1. Delimiter Protection: never convert delimiters attached to \left, \right, etc.
                if cmd_name in PROTECTED_DELIMITER_MACROS and _is_protected_delimiter(math_body, idx):
                    result.append(cmd)
                    idx = cmd_end
                    continue

                # 2. Integral handling: check for bounds (_ or ^)
                if cmd in UNICODE_INTEGRALS:
                    bounded = _has_limits(math_body, cmd_end)
                    if not bounded or opts.convert_definite_integrals:
                        result.append(UNICODE_INTEGRALS[cmd])
                        idx = cmd_end
                        continue
                    else:
                        result.append(cmd)
                        idx = cmd_end
                        continue

                # 3. Big operators handling: check for bounds (_ or ^)
                if cmd in UNICODE_BIG_OPERATORS:
                    bounded = _has_limits(math_body, cmd_end)
                    if not bounded or opts.convert_bounded_operators:
                        result.append(UNICODE_BIG_OPERATORS[cmd])
                        idx = cmd_end
                        continue
                    else:
                        result.append(cmd)
                        idx = cmd_end
                        continue

                # 4. General dictionary replacement
                if cmd in mapping_dict:
                    result.append(mapping_dict[cmd])
                    # For differentials like \partial, consume one delimiter space if followed by a variable (e.g. \partial t -> ∂t)
                    if cmd in UNICODE_DIFFERENTIALS and cmd_end < len(math_body) and math_body[cmd_end] == " ":
                        if cmd_end + 1 < len(math_body) and (math_body[cmd_end + 1].isalpha() or math_body[cmd_end + 1].isdigit()):
                            idx = cmd_end + 1
                            continue
                    idx = cmd_end
                    continue

                result.append(cmd)
                idx = cmd_end
                continue

        result.append(math_body[idx])
        idx += 1

    return "".join(result)


def convert_unicode_to_latex(math_body: str) -> str:
    # Step 1: Auto-repair broken delimiter syntax like \left⟨ -> \left\langle
    def _repair(m: re.Match[str]) -> str:
        prefix = m.group(1)
        delim = m.group(2)
        fixed = DELIMITER_AUTO_REPAIR.get(delim, delim)
        return f"{prefix}{fixed}"

    repaired = DELIM_REPAIR_RE.sub(_repair, math_body)

    # Step 2: Convert Unicode symbols to canonical LaTeX
    mapping = get_unicode_to_latex_map()
    result: list[str] = []
    idx = 0

    while idx < len(repaired):
        matched = False
        for uni, tex in mapping:
            if repaired.startswith(uni, idx):
                next_idx = idx + len(uni)
                next_char = repaired[next_idx] if next_idx < len(repaired) else ""
                # Spacing guard: add trailing space if followed by an ASCII letter (e.g. \psi x, not \psix)
                needs_space = bool(next_char and next_char.isalpha() and ord(next_char) < 128)
                result.append(tex + (" " if needs_space else ""))
                idx = next_idx
                matched = True
                break
        if not matched:
            result.append(repaired[idx])
            idx += 1

    return "".join(result)


def convert_document_math(
    text: str,
    direction: Literal["to-unicode", "to-latex"],
    options: UnicodeConversionOptions | None = None,
) -> str:
    opts = options or UnicodeConversionOptions()
    scan = scan_markdown(text)

    # Collect all non-prose spans: math spans and protected code spans
    spans_with_type = [
        *(("math", s) for s in scan.math_blocks),
        *(("math", s) for s in scan.math_inlines),
        *(("protected", s) for s in scan.protected),
    ]
    spans_with_type.sort(key=lambda item: item[1].start)

    result: list[str] = []
    idx = 0

    def _convert_prose(chunk: str) -> str:
        if direction == "to-unicode" and opts.convert_prose_to_unicode:
            return convert_latex_to_unicode(chunk, opts)
        if direction == "to-latex" and opts.convert_prose_to_latex:
            return convert_unicode_to_latex(chunk)
        return chunk

    for kind, span in spans_with_type:
        if span.start > idx:
            result.append(_convert_prose(text[idx:span.start]))

        if kind == "protected":
            # Code blocks and inline code spans are never touched
            result.append(text[span.start:span.end])
        elif kind == "math":
            # Leading delimiter (e.g. $$ or $)
            result.append(text[span.start:span.content_start])
            content = text[span.content_start:span.content_end]
            converted = (
                convert_latex_to_unicode(content, opts)
                if direction == "to-unicode"
                else convert_unicode_to_latex(content)
            )
            result.append(converted)
            # Trailing delimiter (e.g. $$ or $)
            result.append(text[span.content_end:span.end])

        idx = span.end

    if idx < len(text):
        result.append(_convert_prose(text[idx:]))

    return "".join(result)
