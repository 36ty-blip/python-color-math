# 🎨 Python Color Math

> Semantic color for LaTeX in Markdown documents, without handing your notation to a computer algebra system.

Python Color Math (`python-color-math`) is a local command-line tool that adds semantic color to display-math blocks in Markdown, Jupyter notebooks, native LaTeX, and notes. It inserts scoped `\textcolor{...}{...}` wrappers for MathJax and KaTeX renderers while preserving the original LaTeX structure.

## ✨ Highlights

| Feature | Current behavior |
| --- | --- |
| Derivatives | Colors chain-rule stages, coefficients, powers, and selected nested forms semantically. |
| Nested functions | Distinguishes calls such as `y(x(g(3)))`, including `y`, `x`, and `g`, while treating `3` as a constant. |
| Matrices and tensors | Handles products, transpose/inverse groups, determinants, traces, norms, contractions, and tensor products. |
| General LaTeX | Colors operators, relations, arrows, scripts, sums, integrals, and limits. |
| Markdown safety | Leaves fenced code, inline code, TeX comments, and `\verb` payloads unchanged. |
| Reversibility | Removes both current `\textcolor` output and compatible legacy `\color` wrappers. |

## 🌈 Before and after

Input:

```latex
$$
\frac{d}{dx}f(g(y))
=
f'(g(y))\cdot g'(y)y'
$$
```

Generated output:

```latex
$$
\frac{d}{dx}\textcolor{#7aa2f7}{f(g(y))}
\textcolor{white}{=}
\textcolor{#bb9af7}{f'(g(y))}\textcolor{white}{\cdot} \textcolor{#9ece6a}{g'(y)}\textcolor{#9ece6a}{y'}
$$
```

The inserted wrappers are ordinary MathJax-compatible LaTeX, so the result stays inside the Markdown note rather than depending on a custom Obsidian theme.

## 🚀 Quick start

### Requirements

- Python 3.10 or newer
- Obsidian with its built-in MathJax rendering

### Install

From PyPI:

```bash
pip install python-color-math
```

Or locally from the repository directory:

```bash
pip install .
```

There are no third-party runtime dependencies. `pip install -r requirements.txt` is also supported for compatibility.

> [!TIP]
> **Commands & Environment Variables (PATH)**:
> - Installation registers both the short **`color-math`** and full **`python-color-math`** executable commands.
> - If Python's `Scripts/` folder (or `~/.local/bin` on Linux) is not added to your system `PATH`, you never need to configure environment variables manually — you can run the tool directly via Python:
>   ```bash
>   python -m color_math [options]
>   # or
>   python -m python_color_math [options]
>   ```
> - *Linux notes*: GUI support uses Python's standard `tkinter`. On Debian/Ubuntu distros, install it with `sudo apt install python3-tk` if it isn't bundled with your Python install.

### Interactive Tutorial

Run the interactive tutorial for a fast 2-minute guided tour with tips and examples:

```bash
color-math --tutorial
```

### 🖥️ Graphical Pop-up Window (`--ui` / `--gui`)

Prefer a visual interface? Launch the high-DPI pop-up window:

```bash
color-math --ui
# or using the --gui alias:
color-math --gui
# or with a note preloaded:
color-math note.md --ui
# or directly via Python (no PATH needed):
python -m color_math --ui
```

The pop-up window provides:
- **Preview vs Write Toggle**: Inspect rendered diffs safely or write directly to the note.
- **Color Palette & Visual Color Chooser**: Interactive swatches for all 12 color roles with a visual color picker.
- **Theme & Preset Selectors**: Switch themes (`default`, `catppuccin`, `nord`, `light`) or presets with one click.
- **Instant Reset**: Revert colors to factory defaults at any time.
- **High-DPI Support**: Automatically scales crisp fonts and swatches to match your monitor DPI.

### Convert notes

Preview the converted Markdown in your terminal (leaves files unchanged):

```bash
color-math "path/to/note.md"
```

Save the conversion directly back to the note:

```bash
color-math -w "path/to/note.md"
# or using --in-place:
color-math -i "path/to/note.md"
```

Convert an entire folder or vault recursively:

```bash
color-math notes/ -r -w
```

Preview changes as a unified diff:

```bash
color-math note.md --diff
```

Convert one expression directly:

```bash
color-math "$$\\frac{d}{dx}f(y)^n=nf(y)^{n-1}\\cdot f'(y)y'$$"
```

## 🎨 Themes, Custom Colors & Reset

### View active colors

Inspect all active color roles, their current hex values, and what symbols they color:

```bash
color-math --show-colors
```

### Built-in themes

Switch between curated color palettes with `--theme`:

```bash
color-math note.md --theme catppuccin -w
color-math note.md --theme nord -w
color-math note.md --theme light -w
color-math note.md --theme default -w
```

### Reset to default colors

Changed your palette and want to revert back? Reset colors and configuration to the clean default Tokyo Night palette anytime:

```bash
color-math --reset-colors
```

### Export a configuration file

Generate a documented `.colormath.json` to tweak colors and feature options without editing Python source files:

```bash
color-math --init-config
```

## Compatible applications

The converter remains Obsidian-first, but its ordinary Markdown and
`\textcolor` output also works with:

| Application | Input | Extra converter setup |
| --- | --- | --- |
| Typora | `.md` | None |
| VS Code Markdown Preview | `.md` | None |
| GitHub Markdown | `.md` with `$$...$$` blocks | None |
| Quarto | `.qmd` | None for HTML/MathJax output |
| Material for MkDocs | `.md` | Enable MathJax or KaTeX in MkDocs |
| Jupyter | `.ipynb` Markdown cells | None; detected from the extension |
| Anki | `.txt` or `.tsv` import | Pass `--format anki` |
| Native LaTeX | `.tex` or `.latex` | None; `xcolor` support is generated |

The command stays the same for every target:

```bash
color-math --file --in-place "path/to/document.md"
```

Quarto files can be passed directly with their `.qmd` extension. See
[`docs/applications.md`](docs/applications.md) for setup instructions and
platform-specific cautions.

Jupyter and native LaTeX files are selected automatically:

```bash
color-math --file --in-place "lesson.ipynb"
color-math --file --in-place "paper.tex"
```

Anki exports have no unique extension, so select the adapter explicitly:

```bash
color-math --format anki --file --in-place "cards.tsv"
```

## ↩️ Undo colors

Preview a color-free version:

```bash
color-math --undo "path/to/colored-note.md"
```

Restore the note back to clean plain LaTeX:

```bash
color-math --undo -w "path/to/colored-note.md"
```

Strip colors from an entire folder:

```bash
color-math notes/ -r --undo -w
```

> [!WARNING]
> Undo removes generated `\textcolor{...}{...}` wrappers and legacy `\color{...}{...}` wrappers inside detected `$$...$$` blocks. It cannot distinguish generated wrappers from color wrappers you wrote by hand inside display math, so preview before saving changes on a note with manual colors.

Text outside display math, Markdown code, TeX comments, and `\verb` payloads are left untouched.

## 🚦 Linter and Pre-Commit Mode (`--check`)

Verify whether notes in your vault or repository are colored and properly formatted without modifying them:

```bash
color-math notes/ -r --check
```

- Returns **exit code 0** if all notes are clean.
- Returns **exit code 1** and lists unformatted files if changes are required (ideal for GitHub Actions and pre-commit hooks).

## 🔎 Inspect math structure

Use the source-preserving parser to inspect recognized nested function calls and constants:

```bash
python -m color_math --file --parse tests/original/derivatives.md
```

The inspector reports structure without rewriting the LaTeX or pretending unsupported matrix/tensor notation is a scalar expression.

## 🧪 Verify the project

```bash
python -m color_math --self-test
python -m tests.self_test
```

- `python -m color_math --self-test` runs the installed-package smoke tests.
- `python -m tests.self_test` runs the exact repository suite, including byte-for-byte fixtures, undo round trips, idempotence, Markdown protection, BOM/newline preservation, and atomic file replacement.

Both commands are read-only by default. Refresh [`tests/generated/`](tests/README.md) explicitly:

```bash
python -m tests.self_test --update-generated
```

GitHub Actions runs the suite on Windows and Linux. You can also build a local wheel without another packaging dependency:

```bash
python -m pip wheel --no-deps --wheel-dir dist .
```

## 🗂️ Project layout

The package is separated into conversion rules, source-preserving parsers, and small shared utilities:

```text
obsidian-color-math/
├── color_math/
│   ├── converters/                 # LaTeX coloring rules
│   │   ├── __init__.py
│   │   ├── align.py                # Reserved align-environment rule
│   │   ├── block.py                # Main Markdown-to-math pipeline
│   │   ├── derivative.py           # Chain-rule semantic formatter
│   │   ├── equation.py             # Reserved equation rule
│   │   ├── generic.py              # Token-coloring fallback
│   │   ├── integral.py             # Reserved integral rule
│   │   ├── limit.py                # Reserved limit rule
│   │   ├── matrix.py               # Matrix and tensor formatter
│   │   └── semantic.py             # Shared math-block helpers
│   ├── parsers/                    # Lossless Markdown and LaTeX scanning
│   │   ├── __init__.py
│   │   ├── latex_spans.py          # Lossless LaTeX operand spans
│   │   ├── markdown_scanner.py     # Code-fence-aware Markdown spans
│   │   ├── math_parser.py          # Nested-function inspector
│   │   └── scanner.py              # Generic operator scanner
│   ├── utils/                      # Small shared formatting helpers
│   │   ├── __init__.py
│   │   ├── coloring.py             # Builds color wrappers
│   │   ├── latex_helpers.py        # Balanced-group and command readers
│   │   └── spans.py                # Selects and applies color spans
│   ├── __init__.py                 # Public conversion and undo helpers
│   ├── __main__.py                 # `python -m color_math` entry point
│   ├── config.py                   # Color palette and command groups
│   ├── io.py                       # Byte-preserving atomic file writes
│   ├── main.py                     # Command-line interface
│   ├── self_test.py                # Installed-package smoke tests
│   └── undo.py                     # Removes current and legacy colors
├── tests/
│   ├── original/                   # Unprocessed Markdown fixtures
│   ├── expected/                   # Exact expected output
│   ├── generated/                  # Latest generated output
│   ├── __init__.py
│   ├── README.md                   # Fixture guide
│   └── self_test.py                # Exact and round-trip test suite
├── docs/
│   └── examples.md                 # Additional usage examples
├── .github/
│   └── workflows/
│       └── tests.yml               # Windows and Linux CI
├── .gitignore                      # Local/build files excluded from Git
├── COMMUNITY_POST.md               # Obsidian community announcement draft
├── LICENSE                         # MIT License
├── pyproject.toml                  # Package metadata and CLI entry point
├── README.md                       # This guide
├── requirements.txt                # Compatibility installation file
└── UNDO.py                         # Backward-compatible undo launcher
```

## ⚠️ Limitations

- Generic LaTeX receives token-level coloring when no semantic rule matches.
- Rich semantic coloring currently covers the derivative, matrix, and tensor forms represented by the test fixtures; it does not algebraically simplify or repair expressions.
- Nested-call recognition currently covers plain `name(...)` and `name\left(...\right)` forms. Unsupported forms remain unchanged or receive generic coloring.
- Inline `$...$` math is intentionally not converted yet.
- The inline-math limitation applies to Markdown. The Anki and native LaTeX
  adapters scan their native inline delimiters explicitly.
- The Markdown scanner protects common fenced-code, inline-code, list, blockquote, and Obsidian-callout forms, but it is not a complete CommonMark parser. Rare indentation and lazy-container forms may need manual review.
- `--in-place` expects UTF-8. It preserves UTF-8 BOMs and exact newline bytes, writes a same-directory temporary file, and atomically replaces the note only after the full output reaches disk.

## 🤝 Contributing

The most useful contribution is a representative fixture containing:

1. The unprocessed Markdown and LaTeX input.
2. The exact output you expect.
3. A short explanation of the intended Obsidian/MathJax rendering.

See [`tests/README.md`](tests/README.md) for the fixture layout and [`COMMUNITY_POST.md`](COMMUNITY_POST.md) for the community announcement draft.

## 📄 License

Released under the [MIT License](LICENSE).
