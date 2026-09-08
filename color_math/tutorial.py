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
            prompt += f", [d] for deep dive"
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


def run_tutorial(input_fn: Callable[[], str] = input) -> int:
    """Run the interactive, friendly Python Color Math CLI tutorial."""
    print(f"\n{BOLD}{MAGENTA}======================================================{RESET}")
    print(f"{BOLD}{CYAN}   🎨 Welcome to Python Color Math! (Interactive Tour){RESET}")
    print(f"{BOLD}{MAGENTA}======================================================{RESET}")
    print(f"{DIM}A fast 2-minute walkthrough to make your LaTeX equations beautiful and clear.{RESET}\n")

    # Chapter 1
    print(f"{BOLD}{BLUE}Chapter 1: The Core Idea 💡{RESET}")
    print(
        "Python Color Math adds semantic colors to your LaTeX equations without\n"
        "modifying the rest of your document or requiring external CAS tools.\n"
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
        "3. Universal: Renders natively in Obsidian, KaTeX, Typora, Jupyter, & Anki."
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
    print(f"\n  {CYAN}3. Advanced feature presets:{RESET}")
    print(f"     {CMD}color-math{RESET} {ARG}note.md{RESET} {FLAG}--preset extended -w{RESET}")
    print(f"     {DIM}(Enables physical units, differentials, braket, & rainbow brackets){RESET}")

    deep_4 = (
        "🔍 Supported File Formats:\n"
        "- Markdown notes (.md, .qmd)\n"
        "- Jupyter notebooks (.ipynb)\n"
        "- Native LaTeX documents (.tex, .latex)\n"
        f"- Anki exports (.tsv, .txt) via '{FLAG}--format anki{RESET}'"
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
    print(f"\n{DIM}Run '{CMD}color-math{RESET} {FLAG}--help{RESET}{DIM}' anytime for full documentation.{RESET}\n")
    return 0
