from __future__ import annotations

import re

from .generic import color_latex_body
from .semantic import parse_math_block


ALIGN_ENV_RE = re.compile(
    r"\\begin\s*\{\s*(?:align\*?|aligned|gather\*?|gathered|split)\s*\}"
)


def convert_align_block(block: str) -> str | None:
    parsed = parse_math_block(block)
    if parsed is None or ALIGN_ENV_RE.search(parsed.body) is None:
        return None
    return parsed.render(color_latex_body(parsed.body))
