"""Public helpers for converting Obsidian LaTeX color markup."""

from .adapters import detect_format, transform_document
from .config import (
    ColorMathOptions,
    find_config_path,
    get_venv_config_path,
    init_config,
    open_config_folder,
)
from .converters.block import convert_text
from .undo import uncolor_text

from .ipython import ColorMath, colormath, load_ipython_extension, unload_ipython_extension

__version__ = "0.2.21"

__all__ = [
    "__version__",
    "ColorMath",
    "ColorMathOptions",
    "colormath",
    "convert_text",
    "detect_format",
    "find_config_path",
    "get_venv_config_path",
    "init_config",
    "load_ipython_extension",
    "open_config_folder",
    "transform_document",
    "uncolor_text",
    "unload_ipython_extension",
]
