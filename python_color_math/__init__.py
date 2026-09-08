"""Wrapper module to allow importing and running as python_color_math."""

from color_math import (
    ColorMathOptions,
    convert_text,
    detect_format,
    transform_document,
    uncolor_text,
)

__all__ = [
    "ColorMathOptions",
    "convert_text",
    "detect_format",
    "transform_document",
    "uncolor_text",
]
