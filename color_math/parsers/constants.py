# color_math/parsers/constants.py

from __future__ import annotations

from ..config import COLORS
from ..utils.spans import ColorSpan


def _is_part_of_command(body: str, index: int) -> bool:
    b = index
    while b >= 0 and body[b].isalpha():
        b -= 1
    return b >= 0 and body[b] == "\\"


def is_euler_constant(body: str, index: int) -> bool:
    """Determines whether character 'e' at index is Euler's constant (e^x, e^{-t}, e^{i\\pi})."""
    if body[index] != "e":
        return False
    if _is_part_of_command(body, index):
        return False
    # Must not be preceded by letter
    if index > 0 and body[index - 1].isalpha():
        return False
    # Must not be followed by letter
    if index + 1 < len(body) and body[index + 1].isalpha():
        return False

    next_idx = index + 1
    while next_idx < len(body) and body[next_idx].isspace():
        next_idx += 1
    # Subscript e_1, e_x is basis vector or indexed variable
    if next_idx < len(body) and body[next_idx] == "_":
        return False
    # Followed by exponent e^x, e^{-t}, e^{...}
    if next_idx < len(body) and body[next_idx] == "^":
        return True

    return False


def is_imaginary_unit(body: str, index: int) -> bool:
    """Determines whether character 'i' or 'j' at index is the imaginary unit (sqrt(-1))."""
    ch = body[index]
    if ch not in ("i", "j"):
        return False
    if _is_part_of_command(body, index):
        return False

    # If preceded by multiple letters, it's part of a word like 'sin', 'dim', 'min'
    if index > 0 and body[index - 1].isalpha():
        if index > 1 and body[index - 2].isalpha():
            return False

    # If preceded by backslash, it's a command
    if index > 0 and body[index - 1] == "\\":
        return False

    next_idx = index + 1
    # If part of longer word: e.g. 'in', 'if', 'int'
    if next_idx < len(body) and body[next_idx].isalpha():
        if next_idx + 1 < len(body) and body[next_idx + 1].isalpha():
            return False

    while next_idx < len(body) and body[next_idx].isspace():
        next_idx += 1

    # Subscript is an index, not imaginary unit (e.g. x_i, A_{ij})
    if next_idx < len(body) and body[next_idx] == "_":
        return False

    # Preceded by digit: 2i, 3j, 0.5i
    if index > 0 and body[index - 1].isdigit():
        return True

    # Followed by ^2 or ^{2}: i^2 = -1
    rem = body[next_idx:]
    if rem.startswith("^2") or rem.startswith("^{2}"):
        return True

    # Followed by constant or greek: \pi, \theta, \omega, \hbar
    import re
    if re.match(r"^\\(?:pi|theta|omega|hbar|phi|psi)", rem):
        return True

    # Followed by variable like y in x + iy, or in exponent
    if next_idx < len(body) and (body[next_idx] in "xyz" or body[next_idx] == "\\"):
        p = index - 1
        while p >= 0 and body[p].isspace():
            p -= 1
        if p >= 0 and body[p] in "+-={(":
            return True

    # Inside exponent: look back for ^
    back = index - 1
    depth = 0
    while back >= 0:
        if body[back] == "}":
            depth += 1
        elif body[back] == "{":
            depth -= 1
            if depth < 0:
                b2 = back - 1
                while b2 >= 0 and body[b2].isspace():
                    b2 -= 1
                if b2 >= 0 and body[b2] == "^":
                    return True
                if b2 >= 0 and body[b2] == "_":
                    return False
                break
        elif depth == 0 and body[back] in "=+-":
            break
        back -= 1

    return False


def collect_single_constant_spans(
    body: str,
    palette: dict[str, str] | None = None,
) -> list[ColorSpan]:
    """Collects spans for single-character constants 'e' and 'i'/'j'."""
    pal = palette or COLORS
    spans: list[ColorSpan] = []
    for i in range(len(body)):
        if is_euler_constant(body, i) or is_imaginary_unit(body, i):
            spans.append(
                ColorSpan(i, i + 1, pal["orange"], priority=22)
            )
    return spans
