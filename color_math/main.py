#!/usr/bin/env python3
"""Command-line interface for Python Color Math."""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from .adapters import AdapterError, FORMATS, detect_format, transform_document
from .config import (
    COLORS,
    DEFAULT_COLORS,
    ROLE_DESCRIPTIONS,
    THEMES,
    ColorMathOptions,
    get_theme,
    load_config,
    reset_colors,
    reset_config_file,
    save_default_config,
)
from .io import encode_utf8, read_utf8, replace_bytes
from .parsers.math_parser import describe_math_blocks
from .self_test import run_self_test
from .tutorial import run_tutorial

VERSION = "0.1.0"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="color-math",
        description="Add semantic color to LaTeX math expressions in Markdown documents.",
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        help=(
            "Input file(s), folder(s), or raw math expression. "
            "Reads from stdin if omitted."
        ),
    )

    # File Writing & Mode
    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Write converted text back to file(s).",
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        dest="in_place",
        help="Alias for --in-place. Overwrite file(s) on disk.",
    )
    parser.add_argument(
        "-f",
        "--file",
        action="store_true",
        help="Treat input explicitly as a file path (for backward compatibility).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write output to destination file instead of stdout.",
    )

    # Batch Traversal
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan directories for supported notes.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude when scanning directories (repeatable).",
    )

    # Linter, Diff & Preview Modes
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Display unified diff of changes without modifying disk.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Linter/CI mode: exit with 0 if files are already colored/clean, "
            "exit with 1 if any files would be changed."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without modifying them.",
    )

    # Learning & Beginner Ergonomics
    parser.add_argument(
        "--tutorial",
        action="store_true",
        help="Launch the interactive terminal tutorial with tips and examples.",
    )
    parser.add_argument(
        "--ui",
        "--gui",
        action="store_true",
        help="Open the interactive graphical window with preview, colors, and settings.",
    )

    # Settings & Palette Reset / Customization
    parser.add_argument(
        "--reset-colors",
        "--reset-palette",
        action="store_true",
        help="Reset color palette and configuration back to factory defaults.",
    )
    parser.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset local .colormath.json config file back to factory defaults.",
    )
    parser.add_argument(
        "--show-colors",
        "--show-palette",
        action="store_true",
        help="Print the active color palette and descriptions of each role.",
    )
    parser.add_argument(
        "--init-config",
        nargs="?",
        const=".colormath.json",
        help="Generate a .colormath.json config template (optional target path).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom .colormath.json configuration file.",
    )
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        help="Select a curated theme preset (default, catppuccin, nord, light).",
    )
    parser.add_argument(
        "--color",
        action="append",
        default=[],
        help="Override a color role (e.g. --color main=#7aa2f7 or -c unit=#73daca).",
    )
    parser.add_argument(
        "--main-color",
        help="Override main function color (backward-compatible shortcut).",
    )

    # Engine Feature Presets & Flags (ColorMathOptions)
    parser.add_argument(
        "--preset",
        choices=["minimal", "extended", "all"],
        help=(
            "Feature preset: 'minimal' (default), 'extended' (Obsidian plugin standard: "
            "taxonomy, delimiters, units, differentials, braket, dimensionless), "
            "or 'all' (extended + variable data-flow hashing)."
        ),
    )
    parser.add_argument(
        "--taxonomy",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable semantic taxonomy coloring.",
    )
    parser.add_argument(
        "--rainbow-delimiters",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable rainbow delimiter depth coloring.",
    )
    parser.add_argument(
        "--variable-data-flow",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable deterministic variable data-flow hash coloring.",
    )
    parser.add_argument(
        "--units",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable physical unit disambiguation.",
    )
    parser.add_argument(
        "--differentials",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable differential disambiguation.",
    )
    parser.add_argument(
        "--braket",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable quantum bra-ket notation coloring.",
    )
    parser.add_argument(
        "--dimensionless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable dimensionless group recognition.",
    )

    # Core Options
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Remove LaTeX color wrappers instead of adding them.",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Inspect nested function calls without rewriting LaTeX.",
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="auto",
        help=(
            "Input format. Auto-detects .ipynb and .tex files; use anki "
            "explicitly for text/TSV exports."
        ),
    )

    # Diagnostic & Logging
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"python-color-math {VERSION}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress per file.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal tests and dependency checks.",
    )
    parser.add_argument(
        "--update-generated",
        action="store_true",
        help="Refresh tests/generated while running --self-test.",
    )

    return parser


def print_color_table(palette: dict[str, str]) -> None:
    """Print a clean, informative table of the active palette."""
    print("\nPython Color Math Palette:\n")
    print(f"  {'Role':<14} {'Current':<10} {'Default':<10} {'Status':<10} Description")
    print(f"  {'-'*14} {'-'*10} {'-'*10} {'-'*10} {'-'*45}")
    for role, default_val in DEFAULT_COLORS.items():
        curr_val = palette.get(role, default_val)
        status = "default" if curr_val.lower() == default_val.lower() else "modified"
        desc = ROLE_DESCRIPTIONS.get(role, "")
        print(f"  {role:<14} {curr_val:<10} {default_val:<10} {status:<10} {desc}")
    print()


def generate_diff(original: str, converted: str, filename: str) -> str:
    """Generate a unified diff representation."""
    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            converted.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    return "".join(diff_lines)


def is_path_target(candidate: str, force_file: bool) -> bool:
    """Determine whether a positional argument refers to a file/directory path."""
    if force_file:
        return True
    path = Path(candidate)
    if path.exists():
        return True
    # If candidate has a supported extension and no raw math tokens, treat as missing file
    if path.suffix.lower() in SUPPORTED_EXTENSIONS and "$$" not in candidate and "\n" not in candidate:
        return True
    return False


def collect_target_files(
    targets: Sequence[str],
    recursive: bool,
    excludes: Sequence[str],
    force_file: bool = False,
) -> list[Path]:
    """Collect all matching file paths from explicit targets and directories."""
    collected: list[Path] = []
    seen: set[Path] = set()

    all_excludes = set(DEFAULT_EXCLUDES)
    user_excludes = list(excludes)

    def is_excluded(p: Path) -> bool:
        for part in p.parts:
            if part in all_excludes:
                return True
        name = p.name
        rel_str = str(p)
        for pat in user_excludes:
            if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_str, pat):
                return True
        return False

    for target_str in targets:
        path = Path(target_str)
        if not path.exists():
            if force_file or path.suffix.lower() in SUPPORTED_EXTENSIONS:
                raise FileNotFoundError(f"color-math: cannot find target '{target_str}'")
            continue

        if path.is_file():
            res = path.resolve()
            if res not in seen and not is_excluded(path):
                seen.add(res)
                collected.append(path)
        elif path.is_dir():
            if recursive:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in all_excludes and not any(fnmatch.fnmatch(d, pat) for pat in user_excludes)]
                    for file in sorted(files):
                        file_path = Path(root) / file
                        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS and not is_excluded(file_path):
                            res = file_path.resolve()
                            if res not in seen:
                                seen.add(res)
                                collected.append(file_path)
            else:
                for item in sorted(path.iterdir()):
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS and not is_excluded(item):
                        res = item.resolve()
                        if res not in seen:
                            seen.add(res)
                            collected.append(item)

    return collected


def resolve_options(args: argparse.Namespace, config_options: ColorMathOptions) -> ColorMathOptions:
    """Combine base config options, CLI preset, and granular overrides."""
    if args.preset == "extended":
        opts = ColorMathOptions.extended()
    elif args.preset == "all":
        opts = ColorMathOptions.all_enabled()
    elif args.preset == "minimal":
        opts = ColorMathOptions()
    else:
        opts = config_options

    if args.taxonomy is not None:
        opts.enable_taxonomy = args.taxonomy
    if args.rainbow_delimiters is not None:
        opts.rainbow_delimiters = args.rainbow_delimiters
    if args.variable_data_flow is not None:
        opts.variable_data_flow = args.variable_data_flow
    if args.units is not None:
        opts.color_units = args.units
    if args.differentials is not None:
        opts.color_differentials = args.differentials
    if args.braket is not None:
        opts.color_braket = args.braket
    if args.dimensionless is not None:
        opts.color_dimensionless = args.dimensionless

    return opts


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Self-test & tutorial
    if args.update_generated and not args.self_test:
        parser.error("--update-generated requires --self-test")
    if args.self_test:
        return run_self_test(update_generated=args.update_generated)
    if args.tutorial:
        return run_tutorial()

    # 2. Config & Palette Reset / Inspection
    if args.reset_colors or args.reset_config:
        reset_colors()
        local_cfg = Path(".colormath.json")
        if local_cfg.exists():
            reset_config_file(local_cfg)
            sys.stdout.write(f"Reset {local_cfg} and color palette to factory defaults.\n")
        else:
            sys.stdout.write("Reset runtime color palette to factory defaults (Tokyo Night).\n")
        return 0

    if args.init_config:
        cfg_path = Path(args.init_config)
        save_default_config(cfg_path)
        sys.stdout.write(f"Created configuration file: {cfg_path}\n")
        return 0

    # 3. Load base configuration & theme
    palette, config_options = load_config(args.config)
    if args.theme:
        palette.update(get_theme(args.theme))

    # Apply individual --color overrides
    for color_spec in args.color:
        if "=" not in color_spec:
            parser.error(f"--color requires 'role=hex' format (got '{color_spec}')")
        role, val = color_spec.split("=", 1)
        role = role.strip()
        val = val.strip()
        if role not in DEFAULT_COLORS:
            valid_roles = ", ".join(DEFAULT_COLORS.keys())
            parser.error(f"unknown color role '{role}'. Valid roles: {valid_roles}")
        palette[role] = val

    if args.main_color:
        palette["main"] = args.main_color

    # Update global runtime COLORS dictionary
    COLORS.clear()
    COLORS.update(palette)

    if args.show_colors:
        print_color_table(palette)
        return 0

    # Resolve options
    options = resolve_options(args, config_options)

    # Launch Graphical User Interface
    if args.ui:
        from .gui import launch_gui
        initial_path = args.inputs[0] if args.inputs else None
        return launch_gui(
            initial_path=initial_path,
            initial_write=args.in_place,
            palette=palette,
            options=options,
        )

    # 4. Determine input mode
    inputs = args.inputs
    is_explicit_file = args.file

    # Check if inputs are file/directory targets
    is_file_mode = False
    if is_explicit_file:
        is_file_mode = True
        if not inputs:
            parser.error("--file requires at least one path")
    elif len(inputs) == 1:
        if is_path_target(inputs[0], force_file=False):
            is_file_mode = True
    elif len(inputs) > 1:
        is_file_mode = True

    # Check flags consistency
    if args.in_place and not is_file_mode:
        parser.error("--in-place / --write requires file input")
    if args.check and not is_file_mode:
        parser.error("--check requires file input")
    if args.dry_run and not is_file_mode:
        parser.error("--dry-run requires file input")

    # 5. Process Files
    if is_file_mode:
        try:
            files = collect_target_files(
                inputs,
                recursive=args.recursive,
                excludes=args.exclude,
                force_file=is_explicit_file,
            )
        except FileNotFoundError as err:
            parser.exit(1, f"{err}\n")

        if not files:
            if not args.quiet:
                sys.stderr.write("color-math: no matching files found\n")
            return 0

        files_modified = 0
        total_files = len(files)

        for path in files:
            try:
                text, source = read_utf8(path)
            except UnicodeDecodeError as error:
                parser.exit(1, f"color-math: {path} is not valid UTF-8 (byte {error.start})\n")
            except OSError as error:
                parser.exit(1, f"color-math: cannot read {path}: {error}\n")

            format_name = detect_format(path, args.format)

            if args.parse:
                if format_name != "markdown":
                    parser.error("--parse currently supports Markdown input only")
                sys.stdout.write(describe_math_blocks(text))
                return 0

            try:
                converted = transform_document(
                    text,
                    format_name,
                    undo=args.undo,
                    palette=palette,
                    options=options,
                )
            except AdapterError as error:
                parser.exit(1, f"color-math: {path}: {error}\n")

            is_changed = converted != text
            if is_changed:
                files_modified += 1

            # Diff mode
            if args.diff:
                diff_output = generate_diff(text, converted, str(path))
                if diff_output:
                    sys.stdout.write(diff_output)
                continue

            # Check mode
            if args.check:
                if is_changed and not args.quiet:
                    sys.stderr.write(f"needs coloring: {path}\n")
                continue

            # Dry run
            if args.dry_run:
                if is_changed and not args.quiet:
                    sys.stdout.write(f"would modify: {path}\n")
                continue

            # Output to single destination file
            if args.output:
                if total_files > 1:
                    parser.error("-o / --output cannot be used with multiple files")
                encoded = encode_utf8(converted, source)
                try:
                    args.output.write_bytes(encoded)
                except OSError as error:
                    parser.exit(1, f"color-math: cannot write to {args.output}: {error}\n")
                return 0

            # In place
            if args.in_place:
                if is_changed:
                    output = encode_utf8(converted, source)
                    try:
                        replace_bytes(path, output, source)
                    except OSError as error:
                        parser.exit(1, f"color-math: cannot replace {path}: {error}\n")
                    if args.verbose and not args.quiet:
                        sys.stdout.write(f"modified: {path}\n")
                elif args.verbose and not args.quiet:
                    sys.stdout.write(f"unchanged: {path}\n")
                continue

            # Standard single-file stdout preview
            if total_files == 1:
                output = encode_utf8(converted, source)
                if hasattr(sys.stdout, "buffer"):
                    sys.stdout.buffer.write(output)
                else:
                    sys.stdout.write(converted)
                return 0

        # Batch summary for in-place / check
        if args.check:
            if files_modified > 0:
                if not args.quiet:
                    sys.stderr.write(f"\n{files_modified} of {total_files} file(s) need coloring.\n")
                return 1
            if not args.quiet:
                sys.stdout.write(f"All {total_files} file(s) are cleanly formatted.\n")
            return 0

        if args.in_place and not args.quiet and total_files > 1:
            sys.stdout.write(f"Processed {total_files} file(s): {files_modified} modified, {total_files - files_modified} unchanged.\n")

        return 0

    # 6. Direct Input or Stdin Mode
    text = inputs[0] if inputs else sys.stdin.read()

    format_name = detect_format(None, args.format)
    if args.parse:
        if format_name != "markdown":
            parser.error("--parse currently supports Markdown input only")
        sys.stdout.write(describe_math_blocks(text))
        return 0

    try:
        converted = transform_document(
            text,
            format_name,
            undo=args.undo,
            palette=palette,
            options=options,
        )
    except AdapterError as error:
        parser.exit(1, f"color-math: {error}\n")

    if args.diff:
        sys.stdout.write(generate_diff(text, converted, "input"))
        return 0

    if args.output:
        try:
            args.output.write_text(converted, encoding="utf-8")
        except OSError as error:
            parser.exit(1, f"color-math: cannot write to {args.output}: {error}\n")
        return 0

    sys.stdout.write(converted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
