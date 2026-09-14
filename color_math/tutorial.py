"""Interactive terminal tutorial for Python Color Math."""

from __future__ import annotations

import sys
from collections.abc import Callable


# Terminal ANSI Color & Style Helpers
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

# Shell Syntax Highlighting (PowerShell convention: command=yellow, flags=gray, target=cyan)
CMD = "\033[93m"        # Bright Yellow for command names (color-math, python-color-math)
FLAG = "\033[90m"       # Gray for flags/switches (--ui, -w, -r, --undo, etc.)
ARG = "\033[36m"        # Cyan for filenames/paths (note.md, notes/)


def has_tutorial_deps() -> bool:
    """Check whether optional rich and questionary packages are installed."""
    try:
        import questionary  # noqa: F401
        import rich  # noqa: F401
        return True
    except ImportError:
        return False


def _ensure_utf8_io() -> None:
    """Ensure standard output and error support UTF-8 on Windows terminals."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _prompt_step(deep_dive: str | None = None, input_fn: Callable[[], str] = input) -> bool:
    """
    Prompt user to continue, dive deeper, or quit.
    Returns True to proceed to next step, False to exit.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        # Running in pipe or non-interactive environment; do not block
        if deep_dive:
            print(f"\n{DIM}{deep_dive}{RESET}")
        return True

    while True:
        prompt = f"\n{BOLD}{CYAN}▶ Press [Enter] to continue"
        if deep_dive:
            prompt += ", [d] for deep dive"
        prompt += f", [q] to quit: {RESET}"

        try:
            choice = input_fn(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            return False

        if choice in ("", "c", "continue", "next", "y", "yes"):
            return True
        elif choice in ("q", "quit", "exit"):
            print(f"\n{YELLOW}👋 Tutorial ended early. Run 'color-math --help' anytime!{RESET}\n")
            return False
        elif choice in ("d", "deep", "deeper") and deep_dive:
            print(f"\n{DIM}--- Deep Dive -----------------------------------------{RESET}")
            print(deep_dive)
            print(f"{DIM}-------------------------------------------------------{RESET}")
            deep_dive = None  # Show once, then allow continuing or quitting
        else:
            print(f"{DIM}Please press Enter, 'd', or 'q'.{RESET}")


def run_fallback_tutorial(input_fn: Callable[[], str] = input) -> int:
    """Run the lightweight, zero-dependency ANSI CLI tutorial."""
    _ensure_utf8_io()
    print(f"\n{BOLD}{MAGENTA}======================================================{RESET}")
    print(f"{BOLD}{CYAN}   🎨 Welcome to Python Color Math! (Interactive Tour){RESET}")
    print(f"{BOLD}{MAGENTA}======================================================{RESET}")
    print(f"{DIM}A fast 2-minute walkthrough to make your LaTeX equations beautiful and clear.{RESET}")
    print(f"{DIM}💡 Tip: Run 'pip install \"python-color-math[tutorial]\"' for arrow-key menus & rich panels.{RESET}\n")

    # Chapter 1
    print(f"{BOLD}{BLUE}Chapter 1: The Core Idea 💡{RESET}")
    print(
        "Python Color Math adds semantic colors to your LaTeX equations without\n"
        "modifying the rest of your document or requiring external CAS tools.\n"
        "It supports both display blocks ($$...$$) and inline math ($...$)!\n"
    )
    print(f"  {BOLD}Original LaTeX:{RESET}")
    print(f"    $$ \\frac{{d}}{{dx}} f(g(x)) = f'(g(x)) \\cdot g'(x) $$")
    print(f"\n  {BOLD}{GREEN}Semantic Color Output:{RESET}")
    print(
        f"    $$ \\frac{{d}}{{dx}} {CYAN}\\textcolor{{#7aa2f7}}{{f(g(x))}}{RESET} "
        f"= {MAGENTA}\\textcolor{{#bb9af7}}{{f'(g(x))}}{RESET}\\cdot "
        f"{GREEN}\\textcolor{{#9ece6a}}{{g'(x)}}{RESET} $$"
    )

    deep_1 = (
        "🔍 Why this design matters:\n"
        "1. Standard LaTeX: It inserts standard \\textcolor{...}{...} wrappers.\n"
        "2. Safe: Fenced code, inline code, TeX comments, and prose are never touched.\n"
        "3. Piecewise & Advanced: Full support for \\begin{cases}, matrices, & derivatives.\n"
        "4. Universal: Renders natively in Obsidian, KaTeX, Typora, Jupyter, & Anki."
    )
    if not _prompt_step(deep_1, input_fn):
        return 0

    # Chapter 2
    print(f"\n{BOLD}{BLUE}Chapter 2: Safe Preview vs Saving 💾{RESET}")
    print(
        "You never have to worry about accidentally overwriting your notes!\n"
        "By default, running color-math on a note only PREVIEWS the result:\n"
    )
    print(f"  {YELLOW}1. Preview mode (Safe, leaves note unchanged):{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}note.md{RESET}")
    print(f"\n  {GREEN}2. Write mode (Updates the note on disk):{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}-w{RESET}")
    print(f"     {DIM}(You can also use {FLAG}-i{DIM} or {FLAG}--in-place{DIM}){RESET}")
    print(f"\n  {MAGENTA}3. Prefer a visual window? (Interactive GUI):{RESET}")
    print(f"     {CMD}color-math{RESET} {FLAG}--ui{RESET}")
    print(f"     {DIM}(Opens the graphical pop-up window with live preview, color pickers, and settings! You can also use {FLAG}--gui{DIM}){RESET}")
    print(f"\n  {CYAN}4. Direct expression mode (No file needed):{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}\"$$\\frac{{d}}{{dx}} x^2 = 2x$$\"{RESET}")
    print(f"     {DIM}(Also handles piecewise cases: \\begin{{cases}} x^2, & x \\ge 0 \\end{{cases}}){RESET}")
    print(f"\n  {DIM}💡 Tip: Both '{CMD}color-math{RESET}{DIM}' and '{CMD}python-color-math{RESET}{DIM}' commands work identically!{RESET}")

    deep_2 = (
        "🔍 GUI Window & Atomic Safety:\n"
        f"- Graphical Window: Run '{CMD}color-math{RESET} {FLAG}--ui{RESET}' or '{CMD}color-math{RESET} {FLAG}--gui{RESET}' anytime.\n"
        "  Select notes/folders with a file browser, customize colors with visual chips,\n"
        "  and toggle advanced options (Units, Differentials, Rainbow Delimiters) interactively.\n"
        f"- When using {FLAG}-w{RESET} or {FLAG}-i{RESET}, color-math uses atomic disk writes (temp file first).\n"
        "- Preserves UTF-8 BOMs and exact original line endings (CRLF or LF).\n"
        f"- Want to see exact line changes in terminal? Use: {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}--diff{RESET}\n"
        f"- Commands: You can type '{CMD}color-math{RESET}' or '{CMD}python-color-math{RESET}' anywhere."
    )
    if not _prompt_step(deep_2, input_fn):
        return 0

    # Chapter 3
    print(f"\n{BOLD}{BLUE}Chapter 3: Fixing Mistakes & Resetting ↩️{RESET}")
    print(
        "Made a mistake or don't like the colors? You have two instant safety nets:\n"
    )
    print(f"  {YELLOW}1. Strip color wrappers from a note:{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}--undo -w{RESET}")
    print(f"     {DIM}(Restores plain LaTeX math instantaneously){RESET}")
    print(f"\n  {GREEN}2. Reset colors & settings back to default:{RESET}")
    print(f"     {CMD}color-math{RESET} {FLAG}--reset-colors{RESET}")
    print(f"     {DIM}(Restores official Tokyo Night colors without searching for hex codes!){RESET}")
    print(f"\n  {CYAN}3. View your active color palette:{RESET}")
    print(f"     {CMD}color-math{RESET} {FLAG}--show-colors{RESET}")

    deep_3 = (
        "🔍 Palette & Themes:\n"
        "- Switch between built-in curated themes:\n"
        f"    {CMD}color-math{RESET} {FLAG}--theme catppuccin{RESET} {ARG}note.md{RESET} {FLAG}-w{RESET}\n"
        f"    {CMD}color-math{RESET} {FLAG}--theme nord{RESET} {ARG}note.md{RESET} {FLAG}-w{RESET}\n"
        f"    {CMD}color-math{RESET} {FLAG}--theme default{RESET} {ARG}note.md{RESET} {FLAG}-w{RESET}\n"
        "- Export a friendly config file to customize:\n"
        f"    {CMD}color-math{RESET} {FLAG}--init-config{RESET}"
    )
    if not _prompt_step(deep_3, input_fn):
        return 0

    # Chapter 4
    print(f"\n{BOLD}{BLUE}Chapter 4: Batch Processing & Power Moves 🚀{RESET}")
    print("Process your whole Obsidian vault or verify formatting in Git:")
    print(f"\n  {YELLOW}1. Color an entire folder recursively:{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}notes/{RESET} {FLAG}-r -w{RESET}")
    print(f"\n  {GREEN}2. Check if any notes need coloring (Linter / CI mode):{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}notes/{RESET} {FLAG}-r --check{RESET}")
    print(f"     {DIM}(Returns exit code 0 if all clean, 1 if notes need formatting){RESET}")
    print(f"\n  {CYAN}3. Feature presets (all vs minimal):{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}--preset minimal -w{RESET}")
    print(f"     {DIM}(Default is 'all'; use 'minimal' for lightweight core coloring){RESET}")
    print(f"\n  {MAGENTA}4. AI Assistant Model Context Protocol (MCP) Server:{RESET}")
    print(f"     {CMD}color-math-mcp{RESET}  {DIM}(or {CMD}color-math{RESET} {FLAG}--mcp{DIM}){RESET}")
    print(f"     {DIM}(Enables Claude Desktop, Cursor, & Antigravity to format notes autonomously!){RESET}")

    deep_4 = (
        "🔍 Formats & AI MCP Integration:\n"
        "- Markdown notes (.md, .qmd), Jupyter (.ipynb), TeX (.tex), Anki (.tsv)\n"
        "- Connect to Claude Desktop, Cursor, or Antigravity via stdio JSON-RPC:\n"
        f"    Install extra: pip install \"python-color-math[mcp]\"\n"
        f"    Command: {CMD}color-math-mcp{RESET} (or {CMD}color-math{RESET} {FLAG}--mcp{RESET})\n"
        "- Exposes 6 tools: colorize_math_expression, colorize_text, uncolor_text,\n"
        "  process_file, scan_vault, and list_themes_and_config."
    )
    if not _prompt_step(deep_4, input_fn):
        return 0

    # Wrap up
    print(f"\n{BOLD}{GREEN}🎉 You're all set! Quick Reference Cheat Sheet:{RESET}")
    print(f"  {BOLD}{CYAN}Commands:{RESET}        {CMD}color-math{RESET}  {DIM}or{RESET}  {CMD}python-color-math{RESET}")
    print(f"  {BOLD}{CYAN}Visual Window:{RESET}   {CMD}color-math{RESET} {FLAG}--ui{RESET}  {DIM}(or {FLAG}--gui{DIM}){RESET}")
    print(f"  {BOLD}{CYAN}Preview:{RESET}         {CMD}color-math{RESET} {ARG}note.md{RESET}")
    print(f"  {BOLD}{CYAN}Save:{RESET}            {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}-w{RESET}")
    print(f"  {BOLD}{CYAN}Whole folder:{RESET}    {CMD}color-math{RESET} {ARG}notes/{RESET} {FLAG}-r -w{RESET}")
    print(f"  {BOLD}{CYAN}Remove colors:{RESET}   {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}--undo -w{RESET}")
    print(f"  {BOLD}{CYAN}Reset palette:{RESET}   {CMD}color-math{RESET} {FLAG}--reset-colors{RESET}")
    print(f"  {BOLD}{CYAN}Check / Linter:{RESET}  {CMD}color-math{RESET} {ARG}notes/{RESET} {FLAG}-r --check{RESET}")
    print(f"  {BOLD}{CYAN}AI MCP Server:{RESET}   {CMD}color-math-mcp{RESET}  {DIM}(or {FLAG}--mcp{DIM}){RESET}")
    print(f"\n{DIM}Run '{CMD}color-math{RESET} {FLAG}--help{RESET}{DIM}' anytime for full documentation.{RESET}\n")
    return 0


def run_rich_tutorial() -> int:
    """Run the enhanced, arrow-key interactive tutorial with Rich and Questionary."""
    _ensure_utf8_io()
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from .config import THEMES
    from .converters.block import convert_text

    console = Console()

    header = Panel.fit(
        "[bold cyan]🎨 Welcome to Python Color Math![/bold cyan]\n"
        "[dim]Interactive Walkthrough & Visual CLI Guide[/dim]",
        border_style="magenta",
        padding=(1, 2),
    )
    console.print(header)

    def show_chapter_1() -> None:
        content = (
            "[bold]Python Color Math[/bold] adds semantic colors to your LaTeX equations without "
            "modifying the rest of your document or requiring external CAS tools.\n"
            "It supports both display blocks ([cyan]$$...$$[/cyan]) and inline math ([cyan]$...$[/cyan])!\n\n"
            "[bold yellow]Original LaTeX:[/bold yellow]\n"
            "  $$ \\frac{d}{dx} f(g(x)) = f'(g(x)) \\cdot g'(x) $$\n\n"
            "[bold green]Semantic Color Output:[/bold green]\n"
            "  $$ \\frac{d}{dx} [cyan]\\textcolor{#7aa2f7}{f(g(x))}[/cyan] = "
            "[magenta]\\textcolor{#bb9af7}{f'(g(x))}[/magenta]\\cdot "
            "[green]\\textcolor{#9ece6a}{g'(x)}[/green] $$\n\n"
            "[dim]• Standard LaTeX: Uses standard \\textcolor wrappers recognized everywhere.\n"
            "• Safe: Code blocks, comments, and regular prose are untouched.\n"
            "• Universal: Works natively in Obsidian, KaTeX, Typora, Jupyter, & Anki.[/dim]"
        )
        console.print(Panel(content, title="💡 Chapter 1: The Core Idea", border_style="blue"))

    def show_chapter_2() -> None:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Command", style="yellow")
        table.add_column("Mode", style="green")
        table.add_column("Description")
        table.add_row("color-math note.md", "Preview", "Safe dry-run preview; note on disk is untouched")
        table.add_row("color-math note.md -w", "Write", "Updates note in place atomically with temp file")
        table.add_row("color-math --ui", "GUI Window", "Visual desktop window with live preview & color pickers")
        table.add_row('color-math "$$...$$"', "Direct", "Colorizes a raw LaTeX string directly in stdout")
        console.print(Panel(table, title="💾 Chapter 2: Safe Preview vs Saving & GUI", border_style="blue"))

    def show_chapter_3() -> None:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Command", style="yellow")
        table.add_column("Action")
        table.add_row("color-math note.md --undo -w", "Strip all \\textcolor wrappers from note")
        table.add_row("color-math --show-colors", "Print active color hex codes and color chips")
        table.add_row("color-math --reset-colors", "Restore official Tokyo Night default colors")
        table.add_row("color-math note.md --theme catppuccin -w", "Colorize note using Catppuccin palette")
        table.add_row("color-math note.md --theme nord -w", "Colorize note using Nord palette")
        table.add_row("color-math --init-config", "Generate a friendly JSON configuration file")
        console.print(Panel(table, title="↩️ Chapter 3: Fixing Mistakes, Themes & Palettes", border_style="blue"))

    def show_chapter_4() -> None:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Command / Tool", style="yellow")
        table.add_column("Purpose")
        table.add_row("color-math notes/ -r -w", "Recursively format an entire Obsidian vault or directory")
        table.add_row("color-math notes/ -r --check", "CI / Linter mode: returns exit 0 if clean, 1 if unformatted")
        table.add_row("color-math note.md --preset minimal -w", "Minimal mode: colors core functions/derivatives only")
        table.add_row("color-math-mcp (or --mcp)", "AI Assistant Server (Claude Desktop, Cursor, Antigravity)")
        console.print(Panel(table, title="🚀 Chapter 4: Batch Processing & AI MCP Server", border_style="blue"))

    def show_interactive_sandbox() -> None:
        console.print(
            "\n[bold cyan]🧪 Interactive LaTeX Playground[/bold cyan]\n"
            "[dim]Enter any LaTeX equation snippet to see it colorized live in your terminal.[/dim]"
        )
        try:
            sample_input = questionary.text(
                "LaTeX math expression:",
                default=r"\frac{d}{dx} f(g(x)) = f'(g(x)) \cdot g'(x)",
            ).ask()
        except (KeyboardInterrupt, EOFError):
            return

        if not sample_input or not sample_input.strip():
            return

        raw = sample_input.strip()
        test_snippet = raw if raw.startswith("$$") and raw.endswith("$$") else f"$${raw}$$"
        converted = convert_text(test_snippet)

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Input", style="dim")
        table.add_column("Colorized Output", style="bold green")
        table.add_row(test_snippet, converted)
        console.print(table)

    def show_theme_inspector() -> None:
        console.print(
            "\n[bold cyan]🎨 Live Theme Inspector[/bold cyan]\n"
            "[dim]Select a theme to preview how equations are styled in that palette.[/dim]"
        )
        themes = list(THEMES.keys())
        try:
            chosen = questionary.select(
                "Select a theme palette to preview:",
                choices=[t.capitalize() for t in themes],
            ).ask()
        except (KeyboardInterrupt, EOFError):
            return

        if not chosen:
            return

        theme_key = chosen.lower()
        palette = THEMES.get(theme_key, THEMES["default"])
        sample = "$$\\frac{d}{dx} x^2 = 2x$$"
        colored = convert_text(sample, palette=palette)

        colors_table = Table(show_header=True, header_style="bold blue")
        colors_table.add_column("Role", style="cyan")
        colors_table.add_column("Hex Code", style="yellow")
        for role, hex_code in list(palette.items())[:6]:
            colors_table.add_row(role, hex_code)

        console.print(Panel(colors_table, title=f"Theme: {chosen}", border_style="cyan"))
        console.print(f"[bold]Sample Output:[/bold]\n  {colored}\n")

    def show_cheat_sheet() -> None:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Quick Action", style="bold yellow")
        table.add_column("Command", style="green")
        table.add_row("GUI Window", "color-math --ui")
        table.add_row("Preview Note", "color-math note.md")
        table.add_row("Save Note", "color-math note.md -w")
        table.add_row("Process Vault", "color-math notes/ -r -w")
        table.add_row("Undo Colors", "color-math note.md --undo -w")
        table.add_row("Reset Palette", "color-math --reset-colors")
        table.add_row("Linter / CI Check", "color-math notes/ -r --check")
        table.add_row("AI MCP Server", "color-math-mcp")
        console.print(Panel(table, title="📋 Quick Reference Cheat Sheet", border_style="green"))

    # Interactive Navigation Loop
    while True:
        try:
            choice = questionary.select(
                "What would you like to explore?",
                choices=[
                    "1. The Core Idea & Semantic LaTeX (💡)",
                    "2. Safe Preview vs Saving & GUI Window (💾)",
                    "3. Fixing Mistakes, Themes & Palettes (↩️)",
                    "4. Batch Processing & AI MCP Server (🚀)",
                    "5. 🧪 Interactive LaTeX Playground (Try an equation live!)",
                    "6. 🎨 Live Theme Inspector (Compare color palettes)",
                    "7. 📋 Quick Reference Cheat Sheet",
                    "8. Exit Tutorial",
                ],
            ).ask()
        except (KeyboardInterrupt, EOFError):
            break

        if not choice or choice.startswith("8"):
            break
        elif choice.startswith("1"):
            show_chapter_1()
        elif choice.startswith("2"):
            show_chapter_2()
        elif choice.startswith("3"):
            show_chapter_3()
        elif choice.startswith("4"):
            show_chapter_4()
        elif choice.startswith("5"):
            show_interactive_sandbox()
        elif choice.startswith("6"):
            show_theme_inspector()
        elif choice.startswith("7"):
            show_cheat_sheet()

    console.print("\n[bold yellow]👋 Tutorial completed! Run 'color-math --help' anytime for full details.[/bold yellow]\n")
    return 0


def run_tutorial(
    input_fn: Callable[[], str] = input,
    force_fallback: bool = False,
) -> int:
    """
    Run the interactive Color Math CLI tutorial.
    Automatically uses Rich + Questionary if available and running in an interactive TTY.
    Gracefully falls back to the zero-dependency ANSI experience otherwise.
    """
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

    if force_fallback or input_fn is not input or not is_interactive or not has_tutorial_deps():
        return run_fallback_tutorial(input_fn=input_fn)

    try:
        return run_rich_tutorial()
    except (KeyboardInterrupt, EOFError):
        print("\n\nTutorial ended.")
        return 0
    except Exception:
        # Fallback to zero-dependency ANSI mode on any unexpected terminal issue
        return run_fallback_tutorial(input_fn=input_fn)
