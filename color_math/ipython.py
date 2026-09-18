"""IPython and Jupyter integration for color-math.

Enables seamless colorized math in Jupyter Notebook 7, JupyterLab, Classic
Notebook, and Google Colab via `%load_ext color_math`.
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

from .adapters import transform_document
from .config import (
    ColorMathOptions,
    THEMES,
    load_config,
    get_global_config_path,
    ensure_global_config_exists,
    open_config_folder,
    save_default_config,
)
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
    opts = options if options is not None else ColorMathOptions.extended()
    if is_fragment:
        converted = convert_math_block(f"$${text}$$", palette=active_palette, options=opts)
        return converted[2:-2]
    return convert_text(text, palette=active_palette, options=opts)


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
            palette, options, _ = load_config()
            local_or_global = Path(".colormath.json").exists() or bool(
                get_global_config_path() and get_global_config_path().exists()
            )
            self._palette = palette
            self._options = options if local_or_global else ColorMathOptions.extended()

        def _parse_magic_args(self, arg_str: str) -> tuple[str | None, ColorMathOptions, str]:
            """Parse leading flags (--theme, -v, --variables) without corrupting LaTeX backslashes."""
            theme = None
            opts = ColorMathOptions(
                enable_taxonomy=self._options.enable_taxonomy,
                rainbow_delimiters=self._options.rainbow_delimiters,
                variable_data_flow=self._options.variable_data_flow,
                color_units=self._options.color_units,
                color_differentials=self._options.color_differentials,
                color_braket=self._options.color_braket,
                color_dimensionless=self._options.color_dimensionless,
                color_alignment=self._options.color_alignment,
                color_single_constants=self._options.color_single_constants,
                normalize_braces=self._options.normalize_braces,
                extended_functions=self._options.extended_functions,
                color_quantum_operators=self._options.color_quantum_operators,
                rainbow_bare_braces=self._options.rainbow_bare_braces,
                highlight_unmatched_braces=self._options.highlight_unmatched_braces,
                field=self._options.field,
            )
            raw = arg_str.strip()
            while raw.startswith("-"):
                if raw.startswith("--theme "):
                    parts = raw.split(maxsplit=2)
                    theme = parts[1]
                    raw = parts[2].strip() if len(parts) > 2 else ""
                elif raw.startswith("--variables") or raw.startswith("-v"):
                    opts.variable_data_flow = True
                    parts = raw.split(maxsplit=1)
                    raw = parts[1].strip() if len(parts) > 1 else ""
                elif raw.startswith("--no-variables") or raw.startswith("-nv"):
                    opts.variable_data_flow = False
                    parts = raw.split(maxsplit=1)
                    raw = parts[1].strip() if len(parts) > 1 else ""
                else:
                    break

            return theme, opts, raw

        @line_magic("color_math")
        @line_magic("colormath")
        def color_math_line(self, line: str) -> Any:
            r"""Colorize and display a single LaTeX formula.

            Usage:
                %color_math \int_0^1 x^2 dx = \frac{1}{3}
                %color_math --theme catppuccin \hat{H}\psi = E\psi
                %color_math -v \hat{H}\psi = E\psi
            """
            theme, opts, raw_line = self._parse_magic_args(line)
            if not raw_line:
                display(Markdown("*Color Math: please provide a LaTeX expression.*"))
                return None

            colored = colormath(raw_line, theme=theme, options=opts, is_fragment=True)
            return Math(colored)

        @cell_magic("color_math")
        @cell_magic("colormath")
        def color_math_cell(self, line: str, cell: str) -> Any:
            r"""Colorize and display a cell containing LaTeX or Markdown math.

            Usage:
                %%color_math
                The equation is:
                $$ \hat{H}\psi = E\psi $$

                %%color_math -v
                $$ \hat{H}\psi = E\psi $$
            """
            theme, opts, _ = self._parse_magic_args(line)
            converted = colormath(cell, theme=theme, options=opts, is_fragment=False)
            display(Markdown(converted))

        @line_magic("color_math_variables")
        def color_math_variables(self, line: str) -> None:
            """Toggle variable data-flow hash coloring for Latin symbols (E, m, x, etc.).

            Usage:
                %color_math_variables on
                %color_math_variables off
            """
            cmd = line.strip().lower()
            if cmd in ("on", "enable", "1", "true"):
                self._options.variable_data_flow = True
                print("Color Math: Variable data-flow coloring enabled.")
            elif cmd in ("off", "disable", "0", "false"):
                self._options.variable_data_flow = False
                print("Color Math: Variable data-flow coloring disabled.")
            else:
                status = "ENABLED" if self._options.variable_data_flow else "DISABLED"
                print(f"Color Math: Variable data-flow coloring is currently {status}.")

        @line_magic("color_math_config")
        def color_math_config(self, line: str) -> None:
            """Inspect or initialize Color Math configuration.

            Usage:
                %color_math_config
                %color_math_config --init
                %color_math_config --reload
            """
            raw = line.strip().lower()
            if "--init" in raw:
                target = Path(".colormath.json")
                save_default_config(target)
                print(f"Color Math: Created config template at '{target.resolve()}'.")
                self._palette, self._options, _ = load_config(target)
            raw = line.strip().lower()
            if raw in ("open", "--open", "explore", "folder"):
                opened = open_config_folder()
                if opened:
                    print("Color Math: Opened configuration folder in file manager.")
                else:
                    print("Color Math: Could not open configuration folder automatically.")
                return

            if "--reload" in raw or raw == "reload":
                self._palette, self._options, _ = load_config()
                print("Color Math: Configuration reloaded.")
                return

            local_path = Path(".colormath.json")
            global_path = ensure_global_config_exists() or get_global_config_path()
            print("Color Math Configuration:")
            print(f"  Local config:  {local_path.resolve()} ({'exists' if local_path.exists() else 'not found'})")
            if global_path:
                print(f"  Global config: {global_path} ({'exists' if global_path.exists() else 'not found'})")
            print(f"  Variables:     {'ENABLED' if self._options.variable_data_flow else 'DISABLED'}")
            print(f"  Taxonomy:      {'ENABLED' if self._options.enable_taxonomy else 'DISABLED'}")
            print(f"  Delimiters:    {'ENABLED' if self._options.rainbow_delimiters else 'DISABLED'}")
            print(f"  Auto-display:  {'ENABLED' if self._auto_hook_active else 'DISABLED'}")
            print("\nTip: Run '%color_math_config open' to open the configuration folder in your file manager.")

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
else:
    class ColorMath:  # type: ignore[no-redef]
        """Fallback when IPython is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "IPython is required to use ColorMath. Install it with 'pip install ipython' or 'pip install python-color-math[jupyter]'."
            )

    class ColorMathMagics:  # type: ignore[no-redef]
        pass


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
