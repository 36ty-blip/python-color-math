#!/usr/bin/env python3
"""Command-line interface for Python Color Math."""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import json
import os
import sys
import time
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


def should_color(stream: object = sys.stdout) -> bool:
    """Determine whether terminal color escape codes should be emitted."""
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    is_atty = getattr(stream, "isatty", None)
    return bool(is_atty and is_atty())


def hex_to_ansi_rgb(hex_code: str) -> str:
    """Convert a hex color (#rrggbb) or named color to an ANSI 24-bit color sequence."""
    hex_clean = hex_code.strip().lstrip("#")
    if len(hex_clean) == 6:
        try:
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass
    elif hex_clean.lower() == "white":
        return "\033[97m"
    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="color-math",
        description="Add semantic color to LaTeX math expressions in Markdown, LaTeX, and Jupyter notebooks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  color-math note.md                  Preview colored output in terminal (safe)\n"
            "  color-math note.md -w               Write colored math back to note in-place\n"
            "  color-math notes/ -r -w             Recursively color an entire directory/vault\n"
            "  color-math note.md --diff           View syntax-highlighted unified diff\n"
            "  color-math notes/ -r --check        Linter mode (returns 0 if clean, 1 if changes needed)\n"
            '  color-math "$$\\frac{d}{dx} x^2$$"   Directly color a raw LaTeX expression\n'
            "  echo '$$f(x)$$' | color-math -      Color LaTeX from standard input\n"
            "  color-math --ui                     Launch the interactive graphical window\n"
            "  color-math --tutorial               Launch the interactive terminal tutorial\n"
        ),
    )

    # Positional Inputs
    parser.add_argument(
        "inputs",
        nargs="*",
        help=(
            "Input file(s), folder(s), raw math expression, or '-' for stdin. "
            "If omitted in an interactive terminal, concise usage is displayed."
        ),
    )

    # File & Batch Targeting Group
    target_group = parser.add_argument_group("File & Batch Targeting")
    target_group.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Write converted text back to file(s).",
    )
    target_group.add_argument(
        "-w",
        "--write",
        action="store_true",
        dest="in_place",
        help="Alias for --in-place. Overwrite file(s) on disk.",
    )
    target_group.add_argument(
        "-f",
        "--file",
        action="store_true",
        help="Treat input explicitly as a file path (for backward compatibility).",
    )
    target_group.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write output to destination file instead of stdout.",
    )
    target_group.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan directories for supported notes.",
    )
    target_group.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude when scanning directories (repeatable).",
    )

    # Verification & Diagnostic Modes Group
    check_group = parser.add_argument_group("Verification & Diagnostic Modes")
    check_group.add_argument(
        "--diff",
        action="store_true",
        help="Display syntax-colored unified diff of changes without modifying disk.",
    )
    check_group.add_argument(
        "--check",
        action="store_true",
        help=(
            "Linter/CI mode: exit with 0 if files are already colored/clean, "
            "exit with 1 if any files would be changed."
        ),
    )
    check_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without modifying them.",
    )
    check_group.add_argument(
        "--json",
        action="store_true",
        help="Output results in structured machine-readable JSON format.",
    )
    check_group.add_argument(
        "--parse",
        action="store_true",
        help="Inspect nested function calls without rewriting LaTeX.",
    )
    check_group.add_argument(
        "--format",
        choices=FORMATS,
        default="auto",
        help=(
            "Input format. Auto-detects .ipynb and .tex files; use anki "
            "explicitly for text/TSV exports."
        ),
    )

    # Palettes & Theming Group
    style_group = parser.add_argument_group("Palettes & Theming")
    style_group.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        help="Select a curated theme preset (default, catppuccin, nord, light).",
    )
    style_group.add_argument(
        "-c",
        "--color",
        action="append",
        default=[],
        help="Override a color role (e.g. --color main=#7aa2f7 or -c unit=#73daca).",
    )
    style_group.add_argument(
        "--main-color",
        help="Override main function color (backward-compatible shortcut).",
    )
    style_group.add_argument(
        "--show-colors",
        "--show-palette",
        action="store_true",
        help="Print the active color palette and descriptions of each role with swatches.",
    )
    style_group.add_argument(
        "--reset-colors",
        "--reset-palette",
        action="store_true",
        help="Reset color palette and configuration back to factory defaults.",
    )
    style_group.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset local .colormath.json config file back to factory defaults.",
    )
    style_group.add_argument(
        "--init-config",
        nargs="?",
        const=".colormath.json",
        help="Generate a .colormath.json config template (optional target path).",
    )
    style_group.add_argument(
        "--config",
        type=Path,
        help="Path to custom .colormath.json configuration file.",
    )

    # Engine Features & Presets Group
    engine_group = parser.add_argument_group("Engine Features & Presets")
    engine_group.add_argument(
        "--preset",
        choices=["all", "minimal", "extended"],
        default="all",
        help=(
            "Feature preset: 'all' (default: full engine with all features enabled) "
            "or 'minimal' (basic function/derivative coloring only)."
        ),
    )
    engine_group.add_argument(
        "--taxonomy",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable semantic taxonomy coloring.",
    )
    engine_group.add_argument(
        "--rainbow-delimiters",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable rainbow delimiter depth coloring.",
    )
    engine_group.add_argument(
        "--variable-data-flow",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable deterministic variable data-flow hash coloring.",
    )
    engine_group.add_argument(
        "--units",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable physical unit disambiguation.",
    )
    engine_group.add_argument(
        "--differentials",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable differential disambiguation.",
    )
    engine_group.add_argument(
        "--braket",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable quantum bra-ket notation coloring.",
    )
    engine_group.add_argument(
        "--dimensionless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable dimensionless group recognition.",
    )
    engine_group.add_argument(
        "--undo",
        action="store_true",
        help="Remove LaTeX color wrappers instead of adding them.",
    )

    # Interactive, Help & Utilities Group
    interactive_group = parser.add_argument_group("Interactive, Help & Diagnostics")
    interactive_group.add_argument(
        "--ui",
        "--gui",
        action="store_true",
        help="Open the interactive graphical window with preview, colors, and settings.",
    )
    interactive_group.add_argument(
        "--tutorial",
        action="store_true",
        help="Launch the interactive terminal tutorial with tips and examples.",
    )
    interactive_group.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"python-color-math {VERSION}",
    )
    interactive_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress per file.",
    )
    interactive_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    interactive_group.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal tests and dependency checks.",
    )
    interactive_group.add_argument(
        "--update-generated",
        action="store_true",
        help="Refresh tests/generated while running --self-test.",
    )

    return parser


def print_color_table(palette: dict[str, str], colorize: bool | None = None) -> None:
    """Print a clean, informative table of the active palette with terminal swatches."""
    if colorize is None:
        colorize = should_color(sys.stdout)

    print("\nPython Color Math Palette:\n")
    if colorize:
        print(f"  {'Role':<14} {'Swatch':<8} {'Current':<10} {'Default':<10} {'Status':<10} Description")
        print(f"  {'-'*14} {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*45}")
    else:
        print(f"  {'Role':<14} {'Current':<10} {'Default':<10} {'Status':<10} Description")
        print(f"  {'-'*14} {'-'*10} {'-'*10} {'-'*10} {'-'*45}")

    for role, default_val in DEFAULT_COLORS.items():
        curr_val = palette.get(role, default_val)
        status = "default" if curr_val.lower() == default_val.lower() else "modified"
        desc = ROLE_DESCRIPTIONS.get(role, "")
        if colorize:
            ansi = hex_to_ansi_rgb(curr_val)
            swatch = f"{ansi}███\033[0m" if ansi else "   "
            print(f"  {role:<14} {swatch}     {curr_val:<10} {default_val:<10} {status:<10} {desc}")
        else:
            print(f"  {role:<14} {curr_val:<10} {default_val:<10} {status:<10} {desc}")
    print()


def generate_diff(original: str, converted: str, filename: str, colorize: bool | None = None) -> str:
    """Generate a unified diff representation, optionally colorized with ANSI codes."""
    if colorize is None:
        colorize = should_color(sys.stdout)

    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            converted.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    if not colorize:
        return "".join(diff_lines)

    colored: list[str] = []
    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            colored.append(f"\033[1m{line}\033[0m")
        elif line.startswith("+"):
            colored.append(f"\033[32m{line}\033[0m")
        elif line.startswith("-"):
            colored.append(f"\033[31m{line}\033[0m")
        elif line.startswith("@@"):
            colored.append(f"\033[36m{line}\033[0m")
        else:
            colored.append(line)
    return "".join(colored)


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


def _main_impl(argv: list[str] | None = None) -> int:
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
        if args.json:
            out_data = {
                "theme": args.theme or "default",
                "palette": palette,
                "descriptions": ROLE_DESCRIPTIONS,
            }
            sys.stdout.write(json.dumps(out_data, indent=2) + "\n")
            return 0
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

    is_stdin = False
    if not inputs:
        # Zero-hang stdin protection: if interactive TTY, show concise usage and exit cleanly
        if sys.stdin.isatty():
            parser.print_usage(sys.stderr)
            sys.stderr.write(
                "\nFor detailed help, run 'color-math --help' or 'color-math --tutorial'.\n"
                "To process LaTeX from standard input, pipe text or pass '-': e.g. echo '$$x$$' | color-math -\n"
            )
            return 0
        is_stdin = True
    elif len(inputs) == 1 and inputs[0] == "-":
        is_stdin = True

    is_file_mode = False
    if not is_stdin:
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
            if args.json:
                sys.stdout.write(json.dumps({"clean": True, "total_files": 0, "modified_files": 0, "files": []}, indent=2) + "\n")
                return 0
            if not args.quiet:
                sys.stderr.write("color-math: no matching files found\n")
            return 0

        files_modified = 0
        total_files = len(files)
        checked_files: list[dict[str, object]] = []
        diff_dict: dict[str, str] = {}
        files_would_modify: list[str] = []
        start_time = time.perf_counter()

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
                if args.json:
                    if diff_output:
                        diff_dict[str(path)] = diff_output
                elif diff_output:
                    sys.stdout.write(diff_output)
                continue

            # Check mode
            if args.check:
                checked_files.append({"path": str(path), "status": "needs_coloring" if is_changed else "clean"})
                if not args.json and is_changed and not args.quiet:
                    sys.stderr.write(f"needs coloring: {path}\n")
                continue

            # Dry run
            if args.dry_run:
                if is_changed:
                    files_would_modify.append(str(path))
                    if not args.json and not args.quiet:
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

        elapsed = time.perf_counter() - start_time

        # Batch summary for diff / dry-run / check in JSON
        if args.diff and args.json:
            sys.stdout.write(json.dumps({"total_files": total_files, "diffs": diff_dict}, indent=2) + "\n")
            return 0

        if args.dry_run and args.json:
            sys.stdout.write(json.dumps({"total_files": total_files, "would_modify": files_would_modify}, indent=2) + "\n")
            return 0

        # Batch summary for in-place / check
        if args.check:
            if args.json:
                result = {
                    "clean": files_modified == 0,
                    "total_files": total_files,
                    "modified_files": files_modified,
                    "elapsed_seconds": round(elapsed, 4),
                    "files": checked_files,
                }
                sys.stdout.write(json.dumps(result, indent=2) + "\n")
                return 1 if files_modified > 0 else 0

            if files_modified > 0:
                if not args.quiet:
                    sys.stderr.write(f"\n{files_modified} of {total_files} file(s) need coloring ({elapsed:.2f}s).\n")
                return 1
            if not args.quiet:
                sys.stdout.write(f"All {total_files} file(s) are cleanly formatted ({elapsed:.2f}s).\n")
            return 0

        if args.in_place and not args.quiet and total_files > 1:
            sys.stdout.write(
                f"Processed {total_files} file(s) in {elapsed:.2f}s: {files_modified} modified, {total_files - files_modified} unchanged.\n"
            )

        return 0

    # 6. Direct Input or Stdin Mode
    if is_stdin:
        text = sys.stdin.read()
        label = "stdin"
    else:
        text = inputs[0]
        label = "input"

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
        diff_output = generate_diff(text, converted, label)
        if args.json:
            sys.stdout.write(json.dumps({"diffs": {label: diff_output}}, indent=2) + "\n")
        else:
            sys.stdout.write(diff_output)
        return 0

    if args.output:
        try:
            args.output.write_text(converted, encoding="utf-8")
        except OSError as error:
            parser.exit(1, f"color-math: cannot write to {args.output}: {error}\n")
        return 0

    if args.json:
        sys.stdout.write(json.dumps({"source": label, "converted": converted}, indent=2) + "\n")
        return 0

    sys.stdout.write(converted)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Safe entry point with graceful signal handling."""
    try:
        return _main_impl(argv)
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
