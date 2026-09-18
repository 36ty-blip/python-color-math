"""IPython and Jupyter integration for color-math.

Enables seamless colorized math in Jupyter Notebook 7, JupyterLab, Classic
Notebook, and Google Colab via `%load_ext color_math`.
"""

from __future__ import annotations

import shlex
from typing import Any

from .adapters import transform_document
from .config import ColorMathOptions, THEMES
from .converters.block import convert_math_block, convert_text

try:
    from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
    from IPython.display import Markdown, Math, display
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False
    Magics = object  # type: ignore[misc,assignment]
    def magics_class(cls: Any) -> Any: return cls
    def line_magic(func: Any) -> Any: return func
    def cell_magic(func: Any) -> Any: return func


def colormath(
    text: str,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
    theme: str | None = None,
    is_fragment: bool = False,
) -> str:
    """Convenience helper to colorize LaTeX math or Markdown math.

    If is_fragment is True, text is treated as raw math without $ delimiters.
    """
    active_palette = THEMES.get(theme) if theme else palette
    if is_fragment:
        converted = convert_math_block(f"$${text}$$", palette=active_palette, options=options)
        return converted[2:-2]
    return convert_text(text, palette=active_palette, options=options)


if HAS_IPYTHON:
    class ColorMath(Math):
        """A drop-in replacement for IPython.display.Math that renders with semantic colors."""

        def __init__(
            self,
            data: Any = None,
            palette: dict[str, str] | None = None,
            options: ColorMathOptions | None = None,
            theme: str | None = None,
            **kwargs: Any,
        ) -> None:
            raw = "" if data is None else str(data)
            colored = colormath(raw, palette=palette, options=options, theme=theme, is_fragment=True)
            super().__init__(data=colored, **kwargs)


    @magics_class
    class ColorMathMagics(Magics):
        """IPython magics for semantic LaTeX colorization."""

        def __init__(self, shell: Any) -> None:
            super().__init__(shell)
            self._auto_hook_active = False
            self._orig_math_repr = None

        @line_magic("color_math")
        @line_magic("colormath")
        def color_math_line(self, line: str) -> Any:
            """Colorize and display a single LaTeX formula.

            Usage:
                %color_math \int_0^1 x^2 dx = \frac{1}{3}
                %color_math --theme catppuccin \hat{H}\psi = E\psi
            """
            theme = None
            raw_line = line.strip()
            if raw_line.startswith("--theme "):
                parts = shlex.split(raw_line)
                if len(parts) >= 3 and parts[0] == "--theme":
                    theme = parts[1]
                    raw_line = " ".join(parts[2:])

            if not raw_line:
                display(Markdown("*Color Math: please provide a LaTeX expression.*"))
                return None

            # Render as display math
            colored = colormath(raw_line, theme=theme, is_fragment=True)
            return Math(colored)

        @cell_magic("color_math")
        @cell_magic("colormath")
        def color_math_cell(self, line: str, cell: str) -> Any:
            """Colorize and display a cell containing LaTeX or Markdown math.

            Usage:
                %%color_math
                Here is the equation:
                $$ \frac{df}{dx} = f'(x) $$
            """
            theme = None
            args = shlex.split(line.strip()) if line.strip() else []
            if len(args) >= 2 and args[0] == "--theme":
                theme = args[1]

            converted = colormath(cell, theme=theme, is_fragment=False)
            display(Markdown(converted))

        @line_magic("color_math_auto")
        def color_math_auto(self, line: str) -> None:
            """Toggle automatic semantic colorization for all IPython.display.Math outputs.

            Usage:
                %color_math_auto on
                %color_math_auto off
                %color_math_auto status
            """
            cmd = line.strip().lower()
            if cmd in ("on", "enable", "1", "true"):
                self.enable_auto_display()
                print("Color Math: Automatic display coloring enabled for IPython.display.Math.")
            elif cmd in ("off", "disable", "0", "false"):
                self.disable_auto_display()
                print("Color Math: Automatic display coloring disabled.")
            else:
                status = "ENABLED" if self._auto_hook_active else "DISABLED"
                print(f"Color Math: Automatic display coloring is currently {status}.")

        def enable_auto_display(self) -> None:
            """Patch IPython.display.Math to automatically colorize its LaTeX payload."""
            if self._auto_hook_active:
                return
            self._orig_math_repr = Math._repr_latex_

            def _colorized_repr_latex(math_self: Math) -> str:
                raw = self._orig_math_repr(math_self)  # type: ignore[misc]
                if not raw:
                    return raw
                # Raw may be surrounded by $$ or not
                if raw.startswith("$$") and raw.endswith("$$"):
                    body = raw[2:-2]
                    return f"$${colormath(body, is_fragment=True)}$$"
                if raw.startswith("$") and raw.endswith("$"):
                    body = raw[1:-1]
                    return f"${colormath(body, is_fragment=True)}$"
                return colormath(raw, is_fragment=True)

            Math._repr_latex_ = _colorized_repr_latex  # type: ignore[assignment]
            self._auto_hook_active = True

        def disable_auto_display(self) -> None:
            """Restore original IPython.display.Math behavior."""
            if not self._auto_hook_active:
                return
            if self._orig_math_repr is not None:
                Math._repr_latex_ = self._orig_math_repr  # type: ignore[assignment]
            self._auto_hook_active = False


def load_ipython_extension(ipython: Any) -> None:
    """Standard IPython extension loader."""
    if not HAS_IPYTHON:
        return
    magics = ColorMathMagics(ipython)
    ipython.register_magics(magics)
    # Store reference so it can be cleanly unloaded
    ipython.custom_exceptions = getattr(ipython, "custom_exceptions", {})
    setattr(ipython, "_color_math_magics", magics)


def unload_ipython_extension(ipython: Any) -> None:
    """Standard IPython extension unloader."""
    if not HAS_IPYTHON:
        return
    magics = getattr(ipython, "_color_math_magics", None)
    if magics is not None and hasattr(magics, "disable_auto_display"):
        magics.disable_auto_display()
