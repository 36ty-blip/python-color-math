"""LaTeX syntax, token integrity, and KaTeX compatibility validator for tests."""

from __future__ import annotations

import re

# Regex to match LaTeX comments
COMMENT_RE = re.compile(r"(?<!\\)%.*$")

# Regex to find \textcolor commands: \textcolor{color}{content} or \textcolor[model]{color}{content}
TEXTCOLOR_RE = re.compile(
    r"\\textcolor(?:\s*\[(?P<model>[^\]]+)\])?\s*\{(?P<color>[^{}]+)\}"
)


class LaTeXValidationError(AssertionError):
    """Raised when LaTeX output violates syntactic or rendering invariants."""


def strip_latex_comments(text: str) -> str:
    """Remove comments while preserving line breaks and escaped percent signs."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        cleaned.append(COMMENT_RE.sub("", line))
    return "\n".join(cleaned)


def validate_brace_balance(latex: str) -> None:
    """Ensure all curly braces outside comments are strictly balanced."""
    stripped = strip_latex_comments(latex)
    depth = 0
    in_escape = False
    for i, char in enumerate(stripped):
        if in_escape:
            in_escape = False
            continue
        if char == "\\":
            in_escape = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                snippet = stripped[max(0, i - 20) : min(len(stripped), i + 20)]
                raise LaTeXValidationError(
                    f"Unmatched closing brace '}}' at index {i} near:\n...{snippet}..."
                )
    if depth != 0:
        raise LaTeXValidationError(
            f"Unbalanced braces: {depth} unclosed '{{' remaining in:\n{latex[:100]}..."
        )


def validate_textcolor_invariants(latex: str) -> None:
    """Verify that \\textcolor wrappers are structurally valid and render-safe."""
    # Alignment delimiters & and \\ must never be enclosed directly in \textcolor
    stripped = strip_latex_comments(latex)
    pos = 0
    while True:
        match = TEXTCOLOR_RE.search(stripped, pos)
        if not match:
            break

        content_start = match.end()
        while content_start < len(stripped) and stripped[content_start].isspace():
            content_start += 1

        if content_start >= len(stripped) or stripped[content_start] != "{":
            pos = match.end()
            continue

        # Find matching closing brace for the content
        depth = 0
        end_pos = -1
        in_escape = False
        for i in range(content_start, len(stripped)):
            char = stripped[i]
            if in_escape:
                in_escape = False
                continue
            if char == "\\":
                in_escape = True
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break

        if end_pos == -1:
            raise LaTeXValidationError(
                f"Unclosed \\textcolor content argument at {content_start}."
            )

        content = stripped[content_start + 1 : end_pos]

        # Invariant: Alignment '&' must not be inside \textcolor
        unescaped_amp = re.search(r"(?<!\\)&", content)
        if unescaped_amp:
            raise LaTeXValidationError(
                f"Alignment '&' illegally wrapped in \\textcolor:\n"
                f"{stripped[match.start():end_pos + 1]}"
            )

        # Invariant: Linebreak '\\' must not be inside \textcolor
        if re.search(r"(?<!\\)\\\\(?:\[[^\]]*\])?(?:\s|\r|\n|$)", content):
            raise LaTeXValidationError(
                f"Linebreak '\\\\' illegally wrapped in \\textcolor:\n"
                f"{stripped[match.start():end_pos + 1]}"
            )

        # Invariant: Environment boundaries \begin or \end must not be inside \textcolor
        if r"\begin{" in content or r"\end{" in content:
            raise LaTeXValidationError(
                f"Environment delimiter illegally wrapped in \\textcolor:\n"
                f"{stripped[match.start():end_pos + 1]}"
            )

        # Invariant: Redundant identical wrapping \textcolor{c1}{\textcolor{c1}{content}}
        stripped_content = content.strip()
        inner_match = TEXTCOLOR_RE.match(stripped_content)
        if inner_match and inner_match.group("color") == match.group("color"):
            inner_content_start = inner_match.end()
            if inner_content_start < len(stripped_content) and stripped_content[inner_content_start] == "{":
                d = 0
                inner_end = -1
                for ci, cc in enumerate(stripped_content[inner_content_start:]):
                    if cc == "{":
                        d += 1
                    elif cc == "}":
                        d -= 1
                        if d == 0:
                            inner_end = inner_content_start + ci
                            break
                if inner_end == len(stripped_content) - 1:
                    raise LaTeXValidationError(
                        f"Redundant nested \\textcolor with identical color:\n"
                        f"{stripped[match.start():end_pos + 1]}"
                    )

        pos = end_pos + 1


def validate_latex_output(latex: str) -> None:
    """Run full validation suite on generated/colored LaTeX."""
    validate_brace_balance(latex)
    validate_textcolor_invariants(latex)
