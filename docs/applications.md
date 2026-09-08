# Compatible applications

Color Math remains Obsidian-first. These integrations reuse the same
`$$...$$` scanner and `\textcolor{...}{...}` output, so they do not introduce
application-specific conversion modes.

## Typora

Typora uses MathJax for `$$...$$` math blocks. Process its Markdown files in
place, then reopen or refresh the document:

```powershell
color-math --file --in-place "notes.md"
```

Reference: [Typora math documentation](https://support.typora.io/Math/).

## VS Code Markdown Preview

VS Code's built-in Markdown preview uses KaTeX, which supports `\textcolor`
and hexadecimal colors. No extension is required:

```powershell
color-math --file --in-place "notes.md"
```

Open the preview after conversion. Keep the built-in
`markdown.math.enabled` setting enabled.

References: [VS Code Markdown math](https://code.visualstudio.com/docs/languages/markdown)
and [KaTeX color support](https://katex.org/docs/supported).

## Quarto

The CLI accepts `.qmd` files directly. Quarto HTML output uses MathJax by
default, and Quarto equation labels after the closing delimiter are preserved:

```powershell
color-math --file --in-place "report.qmd"
quarto render "report.qmd"
```

For the closest match to Obsidian, keep Quarto's HTML math method set to
MathJax. KaTeX is also compatible with the generated `\textcolor` wrappers.

References: [Quarto equations](https://quarto.org/docs/authoring/markdown-basics.html)
and [Quarto HTML math methods](https://quarto.org/docs/output-formats/html-basics.html).

## GitHub Markdown

GitHub uses MathJax for equations in Markdown files, issues, pull requests,
discussions, and wikis. Use `$$...$$` blocks because fenced `math` blocks are
intentionally protected by Color Math's code-fence safety rules.

```powershell
color-math --file --in-place "README.md"
```

Always preview the rendered file on GitHub before publishing because GitHub
controls its MathJax configuration.

Reference: [GitHub mathematical expressions](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).

## Material for MkDocs

Process files under the MkDocs `docs` directory normally:

```powershell
color-math --file --in-place "docs/lesson.md"
```

Then enable MathJax in `mkdocs.yml`:

```yaml
markdown_extensions:
  - pymdownx.arithmatex:
      generic: true

extra_javascript:
  - javascripts/mathjax.js
  - https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js
```

Use the MathJax initialization file shown in the official Material for MkDocs
guide. KaTeX is another supported option and understands `\textcolor`.

Reference: [Material for MkDocs math setup](https://squidfunk.github.io/mkdocs-material/reference/math/).

## Jupyter notebooks

Files ending in `.ipynb` are detected automatically. Only Markdown-cell
`source` values are converted; code cells, outputs, attachments, and metadata
remain data-identical:

```powershell
color-math --file --in-place "lesson.ipynb"
```

Notebook `source` may be either a string or a list of strings, and both forms
are supported. The first changed save normalizes JSON whitespace with Python's
standard JSON writer, but does not add a notebook dependency or execute cells.

Reference: [Jupyter notebook format](https://nbformat.readthedocs.io/en/v5.10.2/format_description.html).

## Anki imports

Anki text and TSV exports do not have a unique filename extension, so select
the adapter explicitly before importing the resulting file:

```powershell
color-math --format anki --file --in-place "cards.tsv"
```

The adapter preserves tabs, fields, HTML, and surrounding text while coloring
math inside Anki's standard `\(...\)` and `\[...\]` MathJax delimiters. Legacy
`[$]...[/$]` and `[$$]...[/$$]` import forms are also recognized. Standard
MathJax delimiters are preferred for new cards and cloze notes.

Reference: [Anki Math and Symbols](https://docs.ankiweb.net/math.html).

## Native LaTeX documents

Files ending in `.tex` or `.latex` are detected automatically:

```powershell
color-math --file --in-place "paper.tex"
```

The native scanner handles `$...$`, `$$...$$`, `\(...\)`, `\[...\]`, and
common equation/AMS display environments. TeX comments, `\verb`, and
`verbatim`, `Verbatim`, `lstlisting`, and `minted` environments are protected.

MathJax-style hex colors are translated to native `xcolor` names. A marked,
generated preamble block supplies `xcolor` and the required color definitions;
`--undo` removes both the wrappers and that generated block. If the document
already loads `xcolor`, its package line is reused.

Reference: [CTAN xcolor package](https://ctan.org/pkg/xcolor).

## Compatibility boundary

- Display math must use `$$...$$`; inline `$...$` remains unchanged.
- Existing Markdown code fences, inline code, and TeX verbatim content remain
  protected.
- Jupyter conversion may reformat JSON whitespace on the first changed save;
  notebook values and non-Markdown cells are preserved.
- Native LaTeX scanning is conservative rather than a complete TeX expansion
  engine. Math hidden inside custom macros such as `\ensuremath` is left alone.
- PDF-oriented Quarto output is separate from the native `.tex` adapter; use
  the generated `.tex` file only if it is part of your maintained source.
- Use `--undo` to remove generated wrappers in every supported application.
