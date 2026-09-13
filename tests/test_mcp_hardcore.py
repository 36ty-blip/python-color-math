"""Hardcore adversarial, edge-case, and stress tests for Color Math MCP Server."""

from __future__ import annotations

import asyncio
import json
import tempfile
import time
import unittest
from pathlib import Path

from color_math.mcp_server import create_mcp_server


class TestMCPHardcore(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_mcp_server()

    def _call(self, tool_name: str, args: dict) -> dict:
        """Helper to invoke a tool and unpack its JSON text content."""
        res = asyncio.run(self.server.call_tool(tool_name, args))
        if hasattr(res, "content") and res.content:
            raw_text = res.content[0].text
            try:
                return json.loads(raw_text)
            except Exception:
                return {"raw_output": raw_text}
        return {"result": str(res)}

    # -------------------------------------------------------------
    # 1. Idempotency (Never double-wrap colors)
    # -------------------------------------------------------------
    def test_idempotency_hard(self) -> None:
        expr = r"\frac{d^2\psi}{dx^2} + \frac{2m}{\hbar^2}(E - V(x))\psi = 0"
        # Run 1
        res1 = self._call("colorize_math_expression", {"expression": expr, "theme": "nord"})
        colored1 = res1.get("colorized", "")
        self.assertTrue(res1.get("changed"))
        self.assertIn(r"\textcolor", colored1)

        # Run 2 on the colored output
        res2 = self._call("colorize_math_expression", {"expression": colored1, "theme": "nord"})
        colored2 = res2.get("colorized", "")

        # Crucial: colored2 must not contain nested double wrappers like \textcolor{...}{\textcolor{...}}
        self.assertNotIn(r"\textcolor{#b48ead}{\textcolor", colored2)
        self.assertEqual(colored1, colored2, "Colorize must be strictly idempotent!")

    # -------------------------------------------------------------
    # 2. Reversibility Round-Trip on Advanced Math
    # -------------------------------------------------------------
    def test_reversibility_advanced_equations(self) -> None:
        complex_doc = r"""# Advanced Physics Document

## Quantum Mechanics
$$\langle \psi | \hat{H} | \phi \rangle = \int d^3x \, \psi^* \left(-\frac{\hbar^2}{2m}\nabla^2 + V(r)\right) \phi$$

## Fluid Dynamics
$$Re = \frac{\rho v L}{\mu} = 1.2 \times 10^5 \, \mu\text{m}$$

## Matrix Algebra
$$\mathbf{A} = \left(\begin{array}{cc} a_{11} & a_{12} \\ a_{21} & a_{22} \end{array}\right)^{-1}$$
"""
        # 1. Colorize
        col_res = self._call("colorize_text", {"text": complex_doc, "format_name": "markdown", "theme": "default"})
        self.assertTrue(col_res.get("changed"))
        colored_text = col_res.get("result", "")
        self.assertIn(r"\textcolor", colored_text)

        # 2. Uncolor
        uncol_res = self._call("uncolor_text", {"text": colored_text, "format_name": "markdown"})
        cleaned_text = uncol_res.get("result", "")

        # 3. Verify no color tags remain
        self.assertNotIn(r"\textcolor", cleaned_text)
        self.assertNotIn(r"\color", cleaned_text)

        # 4. Verify all math blocks and structural text remain intact
        self.assertIn(r"\langle \psi | \hat{H} | \phi \rangle", cleaned_text)
        self.assertIn(r"Re = \frac{\rho v L}{\mu}", cleaned_text)
        self.assertIn(r"\mathbf{A} =", cleaned_text)

    # -------------------------------------------------------------
    # 3. Markdown Code-Fence and Inline-Code Protection
    # -------------------------------------------------------------
    def test_code_fence_and_inline_code_immunity(self) -> None:
        md_with_code = r"""# Testing Immunity

Here is an inline code snippet containing math: `$$\frac{df}{dx} = 0$$` - this should not be touched.

Here is a fenced Python block:
```python
# Even if this looks like math:
pattern = r"$$\frac{d}{dx} f(x) = 1$$"
```

Here is a fenced markdown block:
````markdown
```
$$\int_0^\infty e^{-x} dx = 1$$
```
````

And finally, a REAL math block:
$$\frac{df}{dx} = 0$$
"""
        res = self._call("colorize_text", {"text": md_with_code, "format_name": "markdown"})
        result_text = res.get("result", "")

        # Inline code must be untouched
        self.assertIn(r"`$$\frac{df}{dx} = 0$$`", result_text)

        # Python block must be untouched
        self.assertIn(r'pattern = r"$$\frac{d}{dx} f(x) = 1$$"', result_text)

        # Fenced markdown block must be untouched
        self.assertIn(r"$$\int_0^\infty e^{-x} dx = 1$$", result_text)

        # The real math block MUST be colorized!
        self.assertIn(r"\textcolor{#bb9af7}{\frac{df}{dx}}", result_text)

    # -------------------------------------------------------------
    # 4. Jupyter Notebook (.ipynb) Integrity & Format Safety
    # -------------------------------------------------------------
    def test_jupyter_notebook_roundtrip(self) -> None:
        notebook_data = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "id": "cell-intro-1",
                    "metadata": {"tags": ["theory"]},
                    "source": [
                        "# Theory\n",
                        "Here is the gradient:\n",
                        "$$\\nabla f(\\mathbf{x}) = \\mathbf{0}$$\n",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "id": "cell-code-1",
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import numpy as np\n",
                        "# Do not colorize strings inside code cells!\n",
                        "formula = '$$\\nabla f(x) = 0$$'\n",
                    ],
                },
                {
                    "cell_type": "markdown",
                    "id": "cell-conclusion-2",
                    "metadata": {},
                    "source": [
                        "Derivative: $$\\frac{d}{dx} x^2 = 2x$$\n",
                    ],
                },
            ],
            "metadata": {"language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            nb_path = Path(tmpdir) / "analysis.ipynb"
            nb_path.write_text(json.dumps(notebook_data, indent=2), encoding="utf-8")

            # 1. Dry run
            dry_res = self._call("process_file", {"file_path": str(nb_path), "in_place": False})
            self.assertTrue(dry_res.get("changed"))
            self.assertFalse(dry_res.get("written_to_disk"))
            self.assertIsNotNone(dry_res.get("diff"))

            # 2. In-place modification
            write_res = self._call("process_file", {"file_path": str(nb_path), "in_place": True})
            self.assertTrue(write_res.get("written_to_disk"))

            # 3. Read back and parse JSON to verify valid JSON & cell preservation
            updated_content = nb_path.read_text(encoding="utf-8")
            reparsed = json.loads(updated_content)

            # Metadata and cell IDs must be preserved
            self.assertEqual(reparsed["cells"][0]["id"], "cell-intro-1")
            self.assertEqual(reparsed["cells"][0]["metadata"]["tags"], ["theory"])

            # Markdown math must be colorized
            cell0_text = "".join(reparsed["cells"][0]["source"])
            self.assertIn(r"\textcolor", cell0_text)

            # Code cell MUST NOT be touched
            cell1_text = "".join(reparsed["cells"][1]["source"])
            self.assertNotIn(r"\textcolor", cell1_text)
            self.assertIn("formula = '$$\\nabla f(x) = 0$$'", cell1_text)

            # Cell 2 markdown must be colorized
            cell2_text = "".join(reparsed["cells"][2]["source"])
            self.assertIn(r"\textcolor", cell2_text)

    # -------------------------------------------------------------
    # 5. Security & Boundary Handling
    # -------------------------------------------------------------
    def test_security_and_missing_paths(self) -> None:
        # Non-existent file
        res_missing = self._call("process_file", {"file_path": "/path/that/does/not/exist/ever.md"})
        self.assertIn("File not found", res_missing.get("error", ""))
        self.assertFalse(res_missing.get("changed"))

        # Directory passed as file
        with tempfile.TemporaryDirectory() as tmpdir:
            res_dir = self._call("process_file", {"file_path": tmpdir})
            self.assertIn("File not found", res_dir.get("error", ""))

        # Non-existent directory for scan_vault
        res_scan_missing = self._call("scan_vault", {"directory_path": "/invalid/vault/dir"})
        self.assertIn("Directory not found", res_scan_missing.get("error", ""))
        self.assertEqual(res_scan_missing.get("files_scanned"), 0)

    # -------------------------------------------------------------
    # 6. Malformed & Adversarial LaTeX Syntax
    # -------------------------------------------------------------
    def test_malformed_and_adversarial_syntax(self) -> None:
        # Dangling unbalanced braces
        malformed1 = r"\frac{a}{b"
        res1 = self._call("colorize_math_expression", {"expression": malformed1})
        self.assertIsNotNone(res1)
        # Server must not crash; returns safe output
        self.assertIn("colorized", res1)

        # Unbalanced environment
        malformed2 = r"\begin{matrix} 1 & 2"
        res2 = self._call("colorize_math_expression", {"expression": malformed2})
        self.assertIsNotNone(res2)

        # Deeply nested parentheses (rainbow delimiter stress)
        deep_nesting = "((((((((((x + 1))))))))))"
        res3 = self._call("colorize_math_expression", {"expression": deep_nesting, "rainbow_delimiters": True})
        self.assertTrue(res3.get("changed"))
        self.assertIn(r"\textcolor", res3.get("colorized"))

        # Non-standard empty equations
        empty_math = "$$   $$"
        res4 = self._call("colorize_text", {"text": empty_math})
        self.assertIsNotNone(res4)

    # -------------------------------------------------------------
    # 7. Stress & Performance: Large Document Batch
    # -------------------------------------------------------------
    def test_large_document_performance(self) -> None:
        # Generate 150 diverse math blocks in a single document
        blocks = []
        for i in range(150):
            blocks.append(f"### Section {i}\n$$\\frac{{d^{i % 3 + 1}}}{{dx^{i % 3 + 1}}} f_{i}(x) = {i}x^{{2}} + \\int_0^1 t dt$$\n")
        large_doc = "\n".join(blocks)

        start = time.perf_counter()
        res = self._call("colorize_text", {"text": large_doc, "format_name": "markdown"})
        elapsed = time.perf_counter() - start

        self.assertTrue(res.get("changed"))
        self.assertIn(r"\textcolor", res.get("result", ""))
        # Processing 150 complex blocks should take well under 2.5 seconds
        self.assertLess(elapsed, 2.5, f"Performance bottleneck: took {elapsed:.2f}s for 150 blocks")

    # -------------------------------------------------------------
    # 8. LaTeX (.tex) Document Adapter Safety
    # -------------------------------------------------------------
    def test_latex_document_adapter(self) -> None:
        tex_source = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
\section{Introduction}
Here is an equation:
\begin{equation}
\frac{df}{dx} = 2x
\end{equation}

% This is a comment: \frac{d}{dx}f(x) should not be colored!

\begin{verbatim}
code block: \frac{df}{dx}
\end{verbatim}

\end{document}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "paper.tex"
            tex_file.write_text(tex_source, encoding="utf-8")

            res = self._call("process_file", {"file_path": str(tex_file), "in_place": True})
            self.assertTrue(res.get("changed"))
            self.assertEqual(res.get("format"), "tex")

            updated_tex = tex_file.read_text(encoding="utf-8")
            # Equation in environment should be colored
            self.assertIn(r"\textcolor", updated_tex)
            # Comment must remain untouched
            self.assertIn(r"% This is a comment: \frac{d}{dx}f(x) should not be colored!", updated_tex)
            # Verbatim block must remain untouched
            self.assertIn(r"code block: \frac{df}{dx}", updated_tex)

    # -------------------------------------------------------------
    # 9. Deeply Nested Vault Scanning & Exclusion Boundaries
    # -------------------------------------------------------------
    def test_recursive_vault_hierarchy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir) / "AdityaVault"
            vault_root.mkdir()

            # Nested folders
            folder1 = vault_root / "Physics" / "Mechanics"
            folder1.mkdir(parents=True)
            folder2 = vault_root / ".obsidian" / "plugins"  # Excluded folder!
            folder2.mkdir(parents=True)

            # Files with math
            (folder1 / "kinematics.md").write_text("$$v = \frac{dx}{dt}$$", encoding="utf-8")
            (vault_root / "Physics" / "overview.md").write_text("$$E = mc^2$$", encoding="utf-8")

            # File in excluded directory (MUST NOT BE SCANNED)
            (folder2 / "plugin_note.md").write_text("$$\frac{d}{dx} 1 = 0$$", encoding="utf-8")

            # Non-math file
            (vault_root / "todo.txt").write_text("buy milk", encoding="utf-8")

            res = self._call("scan_vault", {"directory_path": str(vault_root), "recursive": True, "in_place": False})
            self.assertEqual(res.get("files_scanned"), 2)  # kinematics.md & overview.md
            self.assertEqual(res.get("files_with_math"), 2)
            self.assertEqual(res.get("files_changed"), 2)

            # Confirm .obsidian was skipped
            modified_paths = [f["path"] for f in res.get("modified_files", [])]
            for p in modified_paths:
                self.assertNotIn(".obsidian", p)

    # -------------------------------------------------------------
    # 10. Half-Colored Math Expression Completion
    # -------------------------------------------------------------
    def test_half_colored_expression_completion(self) -> None:
        """Verify that half-colored expressions get fully colored without skipping uncolored terms."""
        # Partially colored expression with functions: f was uncolored, g was colored
        partial_expr = r"f(x) + \textcolor{#bb9af7}{g(y)} = 0"
        res = self._call("colorize_math_expression", {"expression": partial_expr, "theme": "nord"})
        colorized = res.get("colorized", "")

        # Uncolored function f must now be colored alongside g and relation =
        self.assertIn(r"\textcolor", colorized)
        self.assertNotIn(r"\textcolor{#bb9af7}{\textcolor", colorized)
        self.assertRegex(colorized, r"\\textcolor\{#[0-9a-fA-F]+\}\{f\}")
        self.assertRegex(colorized, r"\\textcolor\{#[0-9a-fA-F]+\}\{g\}")

        # Partially colored derivative equation
        partial_deriv = r"$$\frac{d}{dx}\textcolor{#7aa2f7}{f(x)} = f'(x)$$"
        res_math = self._call("colorize_math_expression", {"expression": partial_deriv})
        colorized_deriv = res_math.get("colorized", "")
        self.assertRegex(colorized_deriv, r"\\textcolor\{#[0-9a-fA-F]+\}\{f'\}")


if __name__ == "__main__":
    unittest.main()
