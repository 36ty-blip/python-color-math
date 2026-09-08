"""Public helpers for converting Obsidian LaTeX color markup."""

from .adapters import detect_format, transform_document
from .config import ColorMathOptions
from .converters.block import convert_text
from .undo import uncolor_text

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "ColorMathOptions",
    "convert_text",
    "detect_format",
    "transform_document",
    "uncolor_text",
]
