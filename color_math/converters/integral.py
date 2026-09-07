from __future__ import annotations

import re

from .generic import color_latex_body
from .semantic import parse_math_block


INTEGRAL_RE = re.compile(r"\\(?:i{1,3}nt|oint)(?![A-Za-z])")


def convert_integral_line(line: str) -> str | None:
    block = parse_math_block(line)
    if block is None or INTEGRAL_RE.search(block.body) is None:
        return None
    return block.render(color_latex_body(block.body))
