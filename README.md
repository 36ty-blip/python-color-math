# 🎨 color-math (Python)

> Pure Python semantic LaTeX and MathJax colorizer for Obsidian Markdown notes, KaTeX documents, and scientific workflows. Zero dependencies.

[![CI](https://github.com/36ty-blip/python-color-math/actions/workflows/ci.yml/badge.svg)](https://github.com/36ty-blip/python-color-math/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/color-math.svg)](https://pypi.org/project/color-math/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

`color-math` is a fast, standalone command-line tool and Python library that automatically parses LaTeX and MathJax expressions and wraps elements in semantic `\textcolor{...}{...}` annotations. It works across plain Markdown, Obsidian notes, Quarto documents, Jupyter notebooks, and raw LaTeX files without modifying surrounding prose or code blocks.

> [!NOTE]
> **Looking for the Obsidian Plugin?** Check out [obsidian-color-math](https://github.com/36ty-blip/obsidian-color-math) for real-time live preview math coloring directly inside Obsidian!

---

## ✨ Features

- **Zero External Dependencies**: Runs entirely on the Python Standard Library (Python 3.10+).
- **Physical Units & Metric Prefixes**: Distinguishes units (`\mu m`, `m/s`, `nm`, `kg`) from variables, shielding algebraic variables like $m$ in $F = ma$ or $E = mc^2$.
- **Calculus Differentials & Derivatives**: Recognizes infinitesimal differentials ($dx$, $dt$, $d\theta$) and derivative fractions ($\frac{d}{dx}$, $\frac{\partial \psi}{\partial t}$), while preserving standalone distance $d$ and relations like $d\iff e$.
- **Dirac Quantum Bra-Ket Notation**: Formats kets ($|\psi\rangle$), bras ($\langle\phi|$), and expectation values ($\langle\phi|\hat{H}|\psi\rangle$) while protecting absolute values ($|x| < 5$).
- **Dimensionless Numbers**: Identifies contiguous engineering numbers ($Re$, $Ma$, $Pr$, $Nu$) without capturing separated variables ($R\,e$).
- **Rainbow Delimiters**: Stack-based delimiter matching that colors nested parentheses, brackets, and braces by nesting depth.
- **Mathematical Symbol Taxonomy**: Categorizes constants ($\pi, \hbar, \infty$), Greek parameters ($\alpha, \theta, \lambda$), functions ($\sin, \cos, \ln$), and bound summation/limit indices.
- **Variable Data-Flow Hashing**: Deterministically hashes identifiers across an equation so each unique variable maintains a consistent color across terms.
- **Boxed Equations**: Preserves `\boxed{...}` wrappers while coloring internal mathematical structures.
- **Signature Tokyo Night Palette**: Muted pastel tones calibrated for readability and reduced eye strain.
- **Markdown & TeX Safety**: Fenced code blocks, inline code, TeX comments, and `\verb` blocks are protected and left unmodified.
- **Lossless & Reversible**: Includes a `--undo` command to cleanly strip all injected colors back to original LaTeX notation.

---

## 🚀 Installation

Install from PyPI:

```bash
pip install color-math
```

Or install from source:

```bash
git clone https://github.com/36ty-blip/python-color-math.git
cd python-color-math
pip install .
```

---

## 💻 CLI Usage

### Process a Markdown or LaTeX file

```bash
# Colorize equations in a single note
color-math note.md

# Colorize an entire directory of notes recursively
color-math ./vault/

# Preview changes without modifying files (Dry Run)
color-math --dry-run note.md

# Revert and clean colors back to plain LaTeX
color-math --undo note.md
```

### Stdin / Pipe Support

Pipe equations directly through the CLI:

```bash
echo "$$\frac{d}{dx}f(g(x)) = f'(g(x)) \cdot g'(x)$$" | color-math
```

---

## 🐍 Python API

Use `color-math` directly as a library in your Python applications, scripts, or data pipelines:

```python
from color_math import colorize_latex, ColorMathOptions

latex = r"\frac{d}{dx}f(g(x)) = f'(g(x)) \cdot g'(x)"

# Basic coloring with default Tokyo Night palette
colored = colorize_latex(latex)
print(colored)

# Enable extended features (Rainbow delimiters, Variable hashing, etc.)
opts = ColorMathOptions.all_enabled()
extended_colored = colorize_latex(latex, options=opts)
```

---

## 🧪 Testing

Run the comprehensive test suites (51 tests):

```bash
# Run feature test suite
python -m unittest discover tests

# Run regression self-test suite
python -m tests.self_test
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
