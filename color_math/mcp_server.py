"""Model Context Protocol (MCP) server for Python Color Math.

Enables any MCP-compliant AI client (Claude Desktop, Cursor, Antigravity, etc.)
to semantically format, colorize, clean, inspect, and batch-process LaTeX math
equations across Markdown, LaTeX, and Jupyter documents.
"""

from __future__ import annotations

import difflib
import fnmatch
from pathlib import Path
from typing import Any

from .adapters import FORMATS, detect_format, transform_document
from .config import (
    DEFAULT_COLORS,
    ROLE_DESCRIPTIONS,
    THEMES,
    ColorMathOptions,
    get_theme,
)
from .converters.block import convert_math_block
from .io import encode_utf8, read_utf8, replace_bytes
from .parsers.markdown_scanner import scan_markdown
from .undo import uncolor_fragment, uncolor_text

# Import MCPServer with support for both mcp 2.x and mcp 1.x (FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore[no-redef]
    except ImportError as exc:
        raise ImportError(
            "The 'mcp' package is required to use the Color Math MCP server. "
            "Install it with: pip install \"python-color-math[mcp]\" or pip install \"mcp>=1.0.0\""
        ) from exc


SUPPORTED_EXTENSIONS = {".md", ".markdown", ".qmd", ".ipynb", ".tex", ".latex"}
DEFAULT_EXCLUDES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".obsidian",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
    ".pytest_cache",
}


def _resolve_palette(
    theme: str = "default",
    custom_palette: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve color palette from theme name or custom overrides."""
    pal = dict(DEFAULT_COLORS)
    if theme in THEMES:
        pal.update(THEMES[theme])
    elif theme and theme != "default":
        # Normalize and match aliases (e.g. 'tokyo-night' -> 'default', 'catppuccin-mocha' -> 'catppuccin')
        norm = theme.lower().replace("-", "").replace("_", "")
        if "tokyo" in norm:
            pal.update(THEMES.get("default", {}))
        elif "catppuccin" in norm:
            pal.update(THEMES.get("catppuccin", {}))
        elif "nord" in norm:
            pal.update(THEMES.get("nord", {}))
        elif "light" in norm:
            pal.update(THEMES.get("light", {}))
        else:
            try:
                pal.update(get_theme(theme))
            except ValueError:
                pass
    if custom_palette:
        pal.update(custom_palette)
    return pal


def _build_options(
    enable_taxonomy: bool = True,
    rainbow_delimiters: bool = True,
    variable_data_flow: bool = False,
    color_units: bool = True,
    color_differentials: bool = True,
    color_braket: bool = True,
    color_dimensionless: bool = True,
    normalize_braces: bool = False,
    extended_functions: bool = True,
) -> ColorMathOptions:
    """Build ColorMathOptions from individual flag settings."""
    return ColorMathOptions(
        enable_taxonomy=enable_taxonomy,
        rainbow_delimiters=rainbow_delimiters,
        variable_data_flow=variable_data_flow,
        color_units=color_units,
        color_differentials=color_differentials,
        color_braket=color_braket,
        color_dimensionless=color_dimensionless,
        normalize_braces=normalize_braces,
        extended_functions=extended_functions,
    )


def create_mcp_server() -> MCPServer:
    """Construct and configure the Color Math MCP server instance."""
    server = MCPServer(
        name="python-color-math",
        instructions=(
            "Color Math MCP server provides semantic syntax highlighting for LaTeX equations "
            "in Markdown (Obsidian), LaTeX documents, Quarto, and Jupyter notebooks."
        ),
    )

    @server.tool(
        name="colorize_math_expression",
        description=(
            "Colorize a single LaTeX math expression or equation string "
            "(e.g. '\\frac{d}{dx}f(x) = f'(x)'). Applies semantic colors based on mathematical roles."
        ),
    )
    def colorize_math_expression(
        expression: str,
        theme: str = "default",
        enable_taxonomy: bool = True,
        rainbow_delimiters: bool = True,
        variable_data_flow: bool = False,
        color_units: bool = True,
        color_differentials: bool = True,
        color_braket: bool = True,
        color_dimensionless: bool = True,
        normalize_braces: bool = False,
        custom_palette: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        pal = _resolve_palette(theme, custom_palette)
        opts = _build_options(
            enable_taxonomy=enable_taxonomy,
            rainbow_delimiters=rainbow_delimiters,
            variable_data_flow=variable_data_flow,
            color_units=color_units,
            color_differentials=color_differentials,
            color_braket=color_braket,
            color_dimensionless=color_dimensionless,
            normalize_braces=normalize_braces,
        )

        try:
            clean_expr = expression.strip()
            had_delimiters = clean_expr.startswith("$$") and clean_expr.endswith("$$")
            block_text = clean_expr if had_delimiters else f"$${clean_expr}$$"

            colored = convert_math_block(block_text, pal, opts)
            if not had_delimiters and colored.startswith("$$") and colored.endswith("$$"):
                colored_output = colored[2:-2]
            else:
                colored_output = colored

            return {
                "original": expression,
                "colorized": colored_output,
                "changed": colored_output != expression,
                "theme": theme,
            }
        except Exception as err:
            return {
                "original": expression,
                "error": str(err),
                "changed": False,
                "theme": theme,
            }

    @server.tool(
        name="colorize_text",
        description=(
            "Process and apply semantic math colors to all LaTeX equations ($...$ or $$...$$) "
            "inside a given text block (Markdown, LaTeX, or Quarto)."
        ),
    )
    def colorize_text(
        text: str,
        format_name: str = "markdown",
        theme: str = "default",
        enable_taxonomy: bool = True,
        rainbow_delimiters: bool = True,
        variable_data_flow: bool = False,
        color_units: bool = True,
        color_differentials: bool = True,
        color_braket: bool = True,
        color_dimensionless: bool = True,
        normalize_braces: bool = False,
        custom_palette: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        pal = _resolve_palette(theme, custom_palette)
        opts = _build_options(
            enable_taxonomy=enable_taxonomy,
            rainbow_delimiters=rainbow_delimiters,
            variable_data_flow=variable_data_flow,
            color_units=color_units,
            color_differentials=color_differentials,
            color_braket=color_braket,
            color_dimensionless=color_dimensionless,
            normalize_braces=normalize_braces,
        )

        try:
            fmt = format_name if format_name in FORMATS else "markdown"
            result = transform_document(text, fmt, undo=False, palette=pal, options=opts)
            return {
                "format": fmt,
                "theme": theme,
                "original_length": len(text),
                "colorized_length": len(result),
                "changed": result != text,
                "result": result,
            }
        except Exception as err:
            return {
                "format": format_name,
                "theme": theme,
                "error": str(err),
                "changed": False,
                "result": text,
            }

    @server.tool(
        name="uncolor_text",
        description=(
            "Strip baked color formatting (\\textcolor{...}, \\color{...}, etc.) from math expressions "
            "within the provided text, restoring standard LaTeX."
        ),
    )
    def uncolor_text_tool(
        text: str,
        format_name: str = "markdown",
    ) -> dict[str, Any]:
        try:
            fmt = format_name if format_name in FORMATS else "markdown"
            result = transform_document(text, fmt, undo=True)
            return {
                "format": fmt,
                "original_length": len(text),
                "cleaned_length": len(result),
                "changed": result != text,
                "result": result,
            }
        except Exception as err:
            return {
                "format": format_name,
                "error": str(err),
                "changed": False,
                "result": text,
            }

    @server.tool(
        name="process_file",
        description=(
            "Process an individual file on disk (.md, .tex, .ipynb, .qmd). By default, performs "
            "a non-destructive dry-run returning a unified diff. Set in_place=True to write changes to disk."
        ),
    )
    def process_file(
        file_path: str,
        in_place: bool = False,
        undo: bool = False,
        theme: str = "default",
        enable_taxonomy: bool = True,
        rainbow_delimiters: bool = True,
        variable_data_flow: bool = False,
        color_units: bool = True,
        color_differentials: bool = True,
        color_braket: bool = True,
        color_dimensionless: bool = True,
        normalize_braces: bool = False,
    ) -> dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.is_file():
            return {
                "error": f"File not found: {file_path}",
                "changed": False,
            }

        pal = _resolve_palette(theme)
        opts = _build_options(
            enable_taxonomy=enable_taxonomy,
            rainbow_delimiters=rainbow_delimiters,
            variable_data_flow=variable_data_flow,
            color_units=color_units,
            color_differentials=color_differentials,
            color_braket=color_braket,
            color_dimensionless=color_dimensionless,
            normalize_braces=normalize_braces,
        )

        try:
            fmt = detect_format(path)
            original_text, raw_bytes = read_utf8(path)
            transformed = transform_document(
                original_text, fmt, undo=undo, palette=pal, options=opts
            )

            changed = transformed != original_text
            diff_output = ""
            if changed:
                diff_lines = list(
                    difflib.unified_diff(
                        original_text.splitlines(keepends=True),
                        transformed.splitlines(keepends=True),
                        fromfile=str(path),
                        tofile=str(path),
                    )
                )
                diff_output = "".join(diff_lines[:100])  # limit diff length

            written = False
            if changed and in_place:
                new_bytes = encode_utf8(transformed, raw_bytes)
                written = replace_bytes(path, new_bytes, raw_bytes)

            return {
                "file_path": str(path),
                "format": fmt,
                "action": "undo" if undo else "colorize",
                "changed": changed,
                "written_to_disk": written,
                "diff": diff_output if changed else None,
                "message": (
                    f"File successfully updated on disk: {path.name}"
                    if written
                    else (
                        f"Dry run complete: changes detected in {path.name}"
                        if changed
                        else f"No changes needed: {path.name} is already up to date."
                    )
                ),
            }
        except Exception as err:
            return {
                "file_path": str(path),
                "error": str(err),
                "changed": False,
                "written_to_disk": False,
                "message": f"Error processing {path.name}: {err}",
            }

    @server.tool(
        name="scan_vault",
        description=(
            "Scan an entire directory or Obsidian vault for supported notes and documents. "
            "Reports math blocks found and can optionally batch colorize or clean files."
        ),
    )
    def scan_vault(
        directory_path: str,
        recursive: bool = True,
        in_place: bool = False,
        undo: bool = False,
        theme: str = "default",
    ) -> dict[str, Any]:
        root = Path(directory_path).resolve()
        if not root.is_dir():
            return {
                "error": f"Directory not found: {directory_path}",
                "files_scanned": 0,
            }

        pal = _resolve_palette(theme)
        opts = _build_options()

        scanned = 0
        with_math = 0
        changed_count = 0
        file_reports = []

        walker = root.rglob("*") if recursive else root.glob("*")
        for p in walker:
            if not p.is_file():
                continue
            if any(part in DEFAULT_EXCLUDES for part in p.parts):
                continue
            if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            scanned += 1
            try:
                text, raw_bytes = read_utf8(p)
                fmt = detect_format(p)
                scan = scan_markdown(text)
                math_count = len(scan.math_blocks)
                if math_count > 0:
                    with_math += 1

                transformed = transform_document(
                    text, fmt, undo=undo, palette=pal, options=opts
                )
                file_changed = transformed != text
                if file_changed:
                    changed_count += 1
                    if in_place:
                        new_bytes = encode_utf8(transformed, raw_bytes)
                        replace_bytes(p, new_bytes, raw_bytes)

                    file_reports.append({
                        "path": str(p.relative_to(root)),
                        "format": fmt,
                        "math_blocks": math_count,
                        "status": "updated" if in_place else "changes_pending",
                    })
            except Exception as err:
                file_reports.append({
                    "path": str(p.relative_to(root)),
                    "error": str(err),
                })

        return {
            "directory": str(root),
            "files_scanned": scanned,
            "files_with_math": with_math,
            "files_changed": changed_count,
            "in_place": in_place,
            "action": "undo" if undo else "colorize",
            "modified_files": file_reports[:50],
        }

    @server.tool(
        name="list_themes_and_config",
        description=(
            "Discover all built-in color themes (Tokyo Night, Nord, Gruvbox, etc.), "
            "semantic math role descriptions, and the active hex color palette."
        ),
    )
    def list_themes_and_config(theme: str | None = None) -> dict[str, Any]:
        active_theme = theme or "default"
        pal = _resolve_palette(active_theme)
        return {
            "available_themes": sorted(THEMES.keys()),
            "selected_theme": active_theme,
            "palette": pal,
            "role_descriptions": ROLE_DESCRIPTIONS,
        }

    return server


def run_mcp_server(transport: str = "stdio", **kwargs: Any) -> None:
    """Launch the Color Math MCP server."""
    server = create_mcp_server()
    if transport == "stdio":
        server.run(transport="stdio", **kwargs)
    elif transport == "sse":
        server.run(transport="sse", **kwargs)
    elif transport == "streamable-http":
        server.run(transport="streamable-http", **kwargs)
    else:
        raise ValueError(f"Unsupported transport: {transport}. Expected 'stdio', 'sse', or 'streamable-http'.")


if __name__ == "__main__":
    run_mcp_server()

