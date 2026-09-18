"""Quantum operator span collector for python-color-math."""

from __future__ import annotations

import re
from ..config import ColorMathOptions
from ..utils.spans import ColorSpan

ENERGY_OPERATOR_REGEX = re.compile(
    r"(?:\\mathrm\{i\}|i)\s*(?:\\hbar|\\hslash|ℏ)\s*(?:\\(?:d|t)?frac\{\s*(?:\\partial|∂)\s*\}\{\s*(?:\\partial|∂)\s*t\s*\}|\\partial_\{?t\}?|∂_\{?t\}?)"
)

MOMENTUM_OPERATOR_REGEX = re.compile(
    r"-\s*(?:\\mathrm\{i\}|i)\s*(?:\\hbar|\\hslash|ℏ)\s*(?:\\(?:d|t)?frac\{\s*(?:\\partial|∂)\s*\}\{\s*(?:\\partial|∂)\s*[xyz]\s*\}|\\partial_\{?[xyz]\}?|∂_\{?[xyz]\}?|\\nabla|\\vec\{\\nabla\}|∇)"
)

KINETIC_OPERATOR_REGEX = re.compile(
    r"-\s*\\(?:d|t)?frac\{\s*(?:\\hbar|\\hslash|ℏ)\^\{?2\}?\s*\}\{\s*2\s*m\s*\}\s*(?:\\nabla\^\{?2\}?|∇\^\{?2\}?|\\Delta|\\(?:d|t)?frac\{\s*(?:\\partial|∂)\^\{?2\}?\s*\}\{\s*(?:\\partial|∂)\s*[xyz]\^\{?2\}?\s*\})"
)

LADDER_OPERATOR_REGEX = re.compile(
    r"(?:\\hat\{a\}|a)\s*\^\s*\{?\\dagger\}?"
)


def collect_quantum_operator_spans(
    body: str,
    palette: dict[str, str],
    options: ColorMathOptions | None = None,
) -> list[ColorSpan]:
    spans: list[ColorSpan] = []
    color = palette.get("energy_operator", "#2ac3de")
    priority = 45

    for regex in (ENERGY_OPERATOR_REGEX, MOMENTUM_OPERATOR_REGEX, KINETIC_OPERATOR_REGEX, LADDER_OPERATOR_REGEX):
        for match in regex.finditer(body):
            spans.append(ColorSpan(
                start=match.start(),
                end=match.end(),
                color=color,
                priority=priority,
            ))

    return spans
