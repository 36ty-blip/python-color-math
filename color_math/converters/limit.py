from __future__ import annotations

import re

from .generic import color_latex_body
from .semantic import parse_math_block


LIMIT_RE = re.compile(r"\\(?:lim|liminf|limsup|inf|sup|max|min)(?![A-Za-z])")


def convert_limit_line(line: str) -> str | None:
    block = parse_math_block(line)
    if block is None or LIMIT_RE.search(block.body) is None:
        return None
    return block.render(color_latex_body(block.body))
