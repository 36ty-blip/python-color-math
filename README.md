# 🎨 Python Color Math

> Semantic color for LaTeX equations in Markdown, Jupyter notebooks, and native TeX documents — without handing your notation to a computer algebra system.

`python-color-math` parses mathematical expressions and inserts MathJax/KaTeX-compatible `\textcolor{...}{...}` wrappers. It operates completely locally, preserves existing LaTeX structure, and leaves prose, fenced code, TeX comments, and `\verb` payloads untouched.

---

## 🌈 Before & After

**Input:**
```latex
$$ \frac{d}{dx} f(g(y)) = f'(g(y)) \cdot g'(y)y' $$
```

**Output:**
```latex
$$ \frac{d}{dx}\textcolor{#7aa2f7}{f(g(y))} \textcolor{white}{=} \textcolor{#bb9af7}{f'(g(y))}\textcolor{white}{\cdot} \textcolor{#9ece6a}{g'(y)}\textcolor{#9ece6a}{y'} $$
```

---

## 🚀 Quick Start

### Installation

```bash
pip install python-color-math

# Or with interactive arrow-key tutorial & rich panels:
pip install "python-color-math[tutorial]"

# Or with native AI Model Context Protocol (MCP) server support:
pip install "python-color-math[mcp]"

# Or everything:
pip install "python-color-math[all]"
```

*(Or locally from cloned source: `pip install -e .` or `pip install -e ".[tutorial]"`, `pip install -e ".[all]"`)*

> [!TIP]
> **Commands & PATH**:
> - Registers **`color-math`**, **`python-color-math`**, and the dedicated MCP server binary **`color-math-mcp`**.
> - If Python's `Scripts/` folder is not on your `PATH`, run directly via Python without touching environment variables:
>   `python -m color_math [options]` *(or `python -m color_math.mcp`)*.
> - *Linux users*: Python's standard GUI library is available via `sudo apt install python3-tk`.

---

## ⚡ Four Ways to Use

### 1. 🎓 Interactive Terminal Tutorial
New to Color Math? Take the 2-minute paced CLI tour with live examples:
```bash
color-math --tutorial
```
*(Runs out of the box with zero dependencies. Install `python-color-math[tutorial]` to unlock arrow-key menus, Rich panels, an interactive LaTeX sandbox, and live theme inspection!)*

### 2. 🖥️ Graphical Pop-up Window (GUI)
Prefer visual controls? Launch the native High-DPI pop-up window:
```bash
color-math --ui
# or:
color-math --gui
```
- **Preview vs Write Toggle**: Inspect diffs safely or write directly to disk.
- **Visual Color Picker**: Click color chips to select custom hex values.
- **Theme & Preset Selectors**: Switch curated palettes and engine toggles in 1 click.
- **1-Click Reset**: Restore factory Tokyo Night defaults anytime.

### 3. ⌨️ Fast Terminal Commands
```bash
# Safe preview in terminal (leaves notes unchanged)
color-math note.md

# Save changes directly back to the note
color-math note.md -w

# Process an entire folder recursively
color-math notes/ -r -w

# Color a raw LaTeX string directly
color-math "$$\frac{d}{dx} x^2 = 2x$$"

# Read and color from standard input pipeline
cat note.md | color-math -

# Inspect syntax-colored unified diff without touching disk
color-math note.md --diff
```

### 4. 🤖 AI Agent Model Context Protocol (MCP)
Empower local AI assistants (Claude Desktop, Cursor, Antigravity) to semantically format and inspect LaTeX equations:
```bash
# Run stdio MCP server directly:
color-math-mcp
# or:
color-math --mcp
```

---

## 📋 Cheat Sheet (Command Reference)

| Task | Command | Description |
| :--- | :--- | :--- |
| **Visual Window** | `color-math --ui` *(or `--gui`)* | Open interactive High-DPI GUI |
| **Interactive Tour** | `color-math --tutorial` | 2-minute interactive terminal guide |
| **Preview** | `color-math note.md` | Safe preview (leaves disk untouched) |
| **Save / Write** | `color-math note.md -w` *(or `-i`)* | Write changes in-place |
| **Batch Folder** | `color-math notes/ -r -w` | Recursively color directory |
| **Unified Diff** | `color-math note.md --diff` | Inspect exact line changes (colorized) |
| **Linter / CI Mode** | `color-math notes/ -r --check` | Exit `0` if clean, `1` if notes need coloring |
| **Machine JSON** | `color-math notes/ -r --check --json` | Structured JSON output for CI and pipelines |
| **Stdin Pipeline** | `cat note.md \| color-math -` | Read and color math from standard input |
| **Curated Themes** | `color-math note.md --theme catppuccin -w` | Select `default`, `catppuccin`, `nord`, or `light` |
| **Feature Preset** | `color-math note.md --preset minimal -w` | Presets: `all` (default), `minimal` |
| **Custom Colors** | `color-math note.md -c unit=#73daca -w` | Override any of 12 individual color roles |
| **AI MCP Server** | `color-math-mcp` *(or `--mcp`)* | Launch Model Context Protocol server over stdio |
| **Reset Palette** | `color-math --reset-colors` | Restore factory Tokyo Night palette |
| **Inspect Colors** | `color-math --show-colors` | Display palette, descriptions, & terminal swatches |
| **Undo / Strip** | `color-math note.md --undo -w` | Strip color wrappers back to plain LaTeX |
| **Export Config** | `color-math --init-config` | Generate a documented `.colormath.json` |

---

## 🧠 Engine Features & Disambiguation

Control recognition features with `--preset {all,minimal}` (default: `all`) or individual flags:

- **Piecewise Environments (`\begin{cases}`)**: Full structural recognition of cases with multi-branch alignment (`&`), inequalities, and relations (`\ge`, `\le`, `\ne`, `<`, `>`).
- **Inline & Display Math**: Accurately colors both display blocks (`$$...$$`) and inline expressions (`$...$`) while strictly protecting code fences and raw backticks.
- **Half-Colored Auto-Completion**: Partially colored equations are automatically cleaned and re-colorized end-to-end rather than skipped.
- **Calculus Differentials (`--differentials`)**: Disambiguates `dx`, `dt`, `d\theta`, and derivatives (`\frac{d}{dx}`, `\frac{\partial \psi}{\partial t}`) while leaving standalone distance variables `$d$` untouched.
- **Physical Units (`--units`)**: Recognizes metric prefixes and unit compounds (`\mu m`, `m/s`, `kg`, `nm`).
- **Rainbow Delimiters (`--rainbow-delimiters`)**: Recursively colors nested brackets `()`, `[]`, `{}` by depth to eliminate delimiter blindness.
- **Quantum Bra-Ket (`--braket`)**: Dirac notation (`|\psi\rangle`, `\langle\phi|`, `\langle\phi|\psi\rangle`).
- **Dimensionless Groups (`--dimensionless`)**: Recognizes engineering numbers (`Re`, `Ma`, `Pr`, `Nu`).
- **Semantic Taxonomy (`--taxonomy`)**: Colors constants ($\pi, \hbar, \infty$), Greek parameters ($\alpha, \theta$), and standard functions ($\sin, \cos, \ln$).
- **Variable Data-Flow (`--variable-data-flow`)**: Deterministically hashes variable names to track variable flow across equations.

---

## 📁 Supported File Formats

`python-color-math` automatically detects file formats by extension:
- **Markdown**: `.md`, `.markdown`, `.qmd` (Quarto)
- **Jupyter Notebooks**: `.ipynb` (transforms only Markdown cells)
- **Native LaTeX**: `.tex`, `.latex` (adds `\usepackage{xcolor}` compatibility)
- **Anki Flashcards**: `.tsv`, `.txt` (select via `--format anki`)

---

## ↩️ Complete Reversibility (Undo)

Never worry about locking your documents into color wrappers:
```bash
# Preview what plain LaTeX would look like
color-math note.md --undo

# Restore plain LaTeX back to disk
color-math note.md --undo -w

# Strip colors from an entire vault
color-math notes/ -r --undo -w
```
*Undo cleanly removes generated `\textcolor{...}{...}` and compatible legacy `\color{...}{...}` wrappers.*

---

## 🐚 Shell Autocompletion

Generate fast, native completions with full support for all flags, themes, presets, and file formats:

```bash
# Bash
color-math --generate-completion bash >> ~/.bash_completion

# Zsh
color-math --generate-completion zsh > ~/.zsh/completion/_color-math

# Fish
color-math --generate-completion fish > ~/.config/fish/completions/color-math.fish

# PowerShell
color-math --generate-completion powershell | Out-String | Invoke-Expression
# Or persist to your $PROFILE:
Add-Content $PROFILE "`ncolor-math --generate-completion powershell | Out-String | Invoke-Expression"
```

---

## 🤖 Model Context Protocol (MCP) Server

`python-color-math` includes a native Model Context Protocol (MCP) server that empowers AI assistants (**Claude Desktop**, **Cursor**, **Antigravity**, and any MCP client) to format, inspect, colorize, and uncolor LaTeX documents.

### Install MCP Extra
```bash
pip install "python-color-math[mcp]"
```

### Direct Execution
```bash
# Default stdio transport
color-math-mcp

# Or via the main CLI / module:
color-math --mcp
python -m color_math.mcp
```

### Client Configuration

Add to your assistant's MCP configuration:

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "color-math": {
      "command": "color-math-mcp"
    }
  }
}
```

#### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "color-math": {
      "command": "color-math-mcp"
    }
  }
}
```

#### Antigravity / Gemini CLI (`mcp_config.json`)
```json
{
  "mcpServers": {
    "python-color-math": {
      "command": "python",
      "args": ["-m", "color_math.mcp"]
    }
  }
}
```

### Available MCP Tools
| Tool | Description |
| :--- | :--- |
| `colorize_math_expression` | Colorizes an individual LaTeX string (e.g. `\frac{d}{dx}f(x) = f'(x)`). |
| `colorize_text` | Parses and colorizes all equations (`$...$` and `$$...$$`) inside a Markdown, LaTeX, or Jupyter document. |
| `uncolor_text` | Losslessly removes color tags, restoring clean plain LaTeX. |
| `process_file` | Colorizes or uncolors files on disk in-place (`in_place=True`) or performs a safe dry-run returning a diff. |
| `scan_vault` | Recursively scans an entire folder/vault to report math blocks and batch-colorize/uncolor notes. |
| `list_themes_and_config` | Discovers available themes (Tokyo Night, Catppuccin, Nord, Light) and semantic color mappings. |

---

## 🪝 Pre-commit Integration

Integrate `color-math` into your git workflow using [pre-commit](https://pre-commit.com):

```yaml
repos:
  - repo: https://github.com/36ty-blip/color-math
    rev: v0.2.2
    hooks:
      # Formatter: colorizes modified Markdown, LaTeX, and Jupyter files in-place
      - id: color-math
      # Linter: verifies math formatting without modifying files (fails if uncolored)
      # - id: color-math-check
```

---

## ⚙️ Configuration & Standards

`python-color-math` adheres to modern CLI standards ([clig.dev](https://clig.dev/)):
- **Config Hierarchy**: `--config <file>` > `./.colormath.json` (project local) > Global user config (`%APPDATA%\color-math\config.json` on Windows or `~/.config/color-math/config.json` on Linux/macOS) > Factory defaults.
- **Color Standards**: Honors `NO_COLOR` ([no-color.org](https://no-color.org)), `FORCE_COLOR`, and `TERM=dumb`.
- **CI / Pre-commit**: Combine `--check --json` for structured reporting in automated pipelines.

---

## 🤝 Obsidian Companion Plugin

Looking for dynamic real-time equation coloring inside Obsidian without modifying notes on disk? Check out the sister plugin:
👉 [**Obsidian Color Math**](https://github.com/36ty-blip/obsidian-color-math) *(Pure TypeScript, runs natively on Obsidian Desktop & Mobile).*

---

## 📄 License

Released under the [MIT License](LICENSE).
