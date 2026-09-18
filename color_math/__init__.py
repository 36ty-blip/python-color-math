"""Public helpers for converting Obsidian LaTeX color markup."""

from .adapters import detect_format, transform_document
from .config import ColorMathOptions
from .converters.block import convert_text
from .undo import uncolor_text

from .ipython import ColorMath, colormath, load_ipython_extension, unload_ipython_extension

__version__ = "0.2.17"

__all__ = [
    "__version__",
    "ColorMath",
    "ColorMathOptions",
    "colormath",
    "convert_text",
    "detect_format",
    "load_ipython_extension",
    "transform_document",
    "uncolor_text",
    "unload_ipython_extension",
]
