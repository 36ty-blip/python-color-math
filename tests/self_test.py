"""Run exact repository regression checks."""

from __future__ import annotations

import argparse
import codecs
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import color_math.io as file_io
from color_math.adapters import AdapterError, detect_format, transform_document
from color_math.converters.block import convert_text
from color_math.converters.align import convert_align_block
from color_math.converters.integral import convert_integral_line
from color_math.converters.limit import convert_limit_line
from color_math.converters.matrix import convert_matrix_block
from color_math.parsers.math_parser import (
    format_math_structure,
    parse_math_blocks,
    parse_math_body,
)
from color_math.parsers.markdown_scanner import (
    CODE_SPAN,
    FENCED_CODE,
    scan_markdown,
)
from color_math.undo import uncolor_text
from .test_cli import CLITests
from .test_features import FeatureTests
from .test_gui import GUITests


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "original"
EXPECTED = ROOT / "expected"
GENERATED = ROOT / "generated"


def fixture_paths(directory: Path) -> dict[str, Path]:
    return {
        path.name: path
        for path in sorted(directory.glob("*.md"))
        if path.is_file()
    }


def converted_fixture(path: Path) -> tuple[str, bytes, str]:
    source, source_bytes = file_io.read_utf8(path)
    actual = convert_text(source)
    return actual, file_io.encode_utf8(actual, source_bytes), source


def refresh_generated() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for name, source_path in fixture_paths(ORIGINAL).items():
        _, actual_bytes, _ = converted_fixture(source_path)
        (GENERATED / name).write_bytes(actual_bytes)


class FixtureTests(unittest.TestCase):
    maxDiff = None

    def test_fixture_sets_match(self) -> None:
        originals = fixture_paths(ORIGINAL)
        self.assertTrue(originals, "original/ contains no Markdown fixtures")
        self.assertEqual(
            set(originals),
            set(fixture_paths(EXPECTED)),
            "original/ and expected/ must contain the same Markdown filenames",
        )

    def test_fixture_properties(self) -> None:
        originals = fixture_paths(ORIGINAL)
        expected = fixture_paths(EXPECTED)
        for name in sorted(originals.keys() & expected.keys()):
            actual, actual_bytes, source = converted_fixture(originals[name])
            expected_text, expected_bytes = file_io.read_utf8(expected[name])

            with self.subTest(fixture=name, property="expected output"):
                self.assertEqual(actual, expected_text)
                self.assertEqual(actual_bytes, expected_bytes)
            with self.subTest(fixture=name, property="undo round trip"):
                self.assertEqual(uncolor_text(actual), source)
            with self.subTest(fixture=name, property="idempotence"):
                self.assertEqual(convert_text(actual), actual)

    def test_generated_snapshots_match_expected(self) -> None:
        expected = fixture_paths(EXPECTED)
        generated = fixture_paths(GENERATED)
        self.assertEqual(
            set(generated),
            set(expected),
            "generated/ and expected/ must contain the same Markdown filenames",
        )
        for name in sorted(expected):
            with self.subTest(fixture=name):
                self.assertEqual(
                    generated[name].read_bytes(),
                    expected[name].read_bytes(),
                )


class MarkdownScannerTests(unittest.TestCase):
    maxDiff = None

    def assert_pipeline_protection(
        self,
        source: str,
        expected_protected: list[tuple[str, str]],
    ) -> None:
        scan = scan_markdown(source)
        self.assertEqual(
            [
                (span.kind, source[span.start:span.end])
                for span in scan.protected
            ],
            expected_protected,
        )
        self.assertEqual(
            [parsed.source for parsed in parse_math_blocks(source)],
            ["outside(3)"],
        )

        converted = convert_text(source)
        self.assertNotEqual(converted, source)
        for _, protected in expected_protected:
            self.assertIn(protected, converted)
        self.assertEqual(uncolor_text(converted), source)

    def test_top_level_backtick_and_tilde_fences(self) -> None:
        for marker in ("```", "~~~~"):
            fenced = (
                f"{marker}latex\n"
                "$$\\textcolor{red}{inside}$$\n"
                f"{marker}\n"
            )
            source = fenced + "$$outside(3)$$\n"
            with self.subTest(marker=marker):
                self.assert_pipeline_protection(
                    source,
                    [(FENCED_CODE, fenced)],
                )


    def test_direct_list_marker_fence(self) -> None:
        fenced = (
            "- ```latex\n"
            "  $$\\textcolor{red}{inside}$$\n"
            "  ```\n"
        )
        self.assert_pipeline_protection(
            fenced + "$$outside(3)$$\n",
            [(FENCED_CODE, fenced)],
        )

    def test_nested_lists_inside_obsidian_callout(self) -> None:
        fenced = (
            "> [!note]\n"
            "> - outer\n"
            ">   - inner\n"
            ">     ~~~~latex\n"
            ">     $$\\textcolor{red}{inside}$$\n"
            ">     ~~~~\n"
        )
        source = fenced + "$$outside(3)$$\n"
        scan = scan_markdown(source)
        self.assertEqual(
            source[scan.protected[0].start:scan.protected[0].end],
            fenced.split("\n", 3)[3],
        )
        self.assert_pipeline_protection(
            source,
            [(FENCED_CODE, fenced.split("\n", 3)[3])],
        )

    def test_crlf_offsets_are_exact(self) -> None:
        prefix = "before\r\n"
        fenced = (
            "> ```latex\r\n"
            "> $$\\textcolor{red}{inside}$$\r\n"
            "> ```\r\n"
        )
        source = prefix + fenced + "$$outside(3)$$\r\n"
        span = scan_markdown(source).protected[0]
        self.assertEqual(span.start, len(prefix))
        self.assertEqual(span.content_start, len(prefix + "> ```latex\r\n"))
        self.assertEqual(
            span.content_end,
            len(prefix + "> ```latex\r\n> $$\\textcolor{red}{inside}$$\r\n"),
        )
        self.assertEqual(span.end, len(prefix + fenced))
        self.assertEqual(source[span.start:span.end].encode(), fenced.encode())
        self.assert_pipeline_protection(
            source,
            [(FENCED_CODE, fenced)],
        )

    def test_inline_code_uses_exact_backtick_runs_across_lines(self) -> None:
        one_tick = r"`$$\textcolor{red}{one}$$`"
        two_ticks = (
            "``payload ` and\n"
            "$$\\textcolor{blue}{two}$$``"
        )
        source = one_tick + "\n" + two_ticks + "\n$$outside(3)$$\n"
        self.assert_pipeline_protection(
            source,
            [(CODE_SPAN, one_tick), (CODE_SPAN, two_ticks)],
        )

    def test_unclosed_container_fence_stops_at_boundary(self) -> None:
        for fenced in (
            "> ```latex\n> $$\\textcolor{red}{inside}$$\n",
            "- ```latex\n  $$\\textcolor{red}{inside}$$\n",
        ):
            source = fenced + "$$outside(3)$$\n"
            with self.subTest(fenced=fenced):
                self.assert_pipeline_protection(
                    source,
                    [(FENCED_CODE, fenced)],
                )


class ApplicationCompatibilityTests(unittest.TestCase):
    def assert_compatible(
        self,
        source: str,
        preserved: tuple[str, ...] = (),
    ) -> str:
        converted = convert_text(source)
        self.assertNotEqual(converted, source)
        self.assertEqual(uncolor_text(converted), source)
        self.assertEqual(convert_text(converted), converted)
        for fragment in preserved:
            self.assertIn(fragment, converted)
        return converted

    def test_plain_markdown_targets_share_the_existing_pipeline(self) -> None:
        source = "# Formula\n\n$$\n\\binom{n}{k}+f(x)\n$$\n"
        converted = self.assert_compatible(source, ("# Formula",))
        self.assertIn(r"\textcolor{#7aa2f7}{f}(x)", converted)

    def test_quarto_front_matter_and_equation_label_are_preserved(self) -> None:
        source = (
            "---\ntitle: Test\nformat: html\n---\n\n"
            "$$\n\\sin(x)=\\frac{a+b}{c+d}\n$$ {#eq-test}\n"
        )
        converted = self.assert_compatible(
            source,
            ("---\ntitle: Test\nformat: html\n---", "$$ {#eq-test}"),
        )
        self.assertIn(r"\textcolor{#7aa2f7}{\sin}", converted)

    def test_mkdocs_indented_math_is_preserved(self) -> None:
        source = (
            "!!! note\n"
            "    A colored equation:\n\n"
            "    $$\n"
            "    \\sqrt{a+b}=f(x)\n"
            "    $$\n"
        )
        converted = self.assert_compatible(
            source,
            ("!!! note", "    $$"),
        )
        self.assertIn(r"\sqrt{\textcolor{#7aa2f7}{a}", converted)


class DocumentAdapterTests(unittest.TestCase):
    def test_jupyter_changes_only_markdown_cells(self) -> None:
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["A formula:\n", "$$f(x)=g(x)$$\n"],
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": "print('$$f(x)$$')",
                    "outputs": [],
                    "execution_count": None,
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        source = json.dumps(notebook, indent=1) + "\n"
        converted = transform_document(source, "jupyter")
        actual = json.loads(converted)

        self.assertIn(r"\textcolor{#7aa2f7}{f}", "".join(actual["cells"][0]["source"]))
        self.assertEqual(actual["cells"][1], notebook["cells"][1])
        self.assertEqual(transform_document(converted, "jupyter"), converted)
        self.assertEqual(json.loads(transform_document(converted, "jupyter", True)), notebook)

    def test_jupyter_rejects_invalid_notebook_shape(self) -> None:
        with self.assertRaisesRegex(AdapterError, "cells list"):
            transform_document("{}", "jupyter")

    def test_anki_standard_and_legacy_delimiters_round_trip(self) -> None:
        source = (
            "Front\t\\(f(x)\\)<br>\\[\\frac{a+b}{c}\\]\n"
            "Legacy\t[$$]g(x)[/$$]\n"
        )
        converted = transform_document(source, "anki")

        self.assertIn(r"\(\textcolor{#7aa2f7}{f}(x)\)", converted)
        self.assertIn(r"[$$]\textcolor{#7aa2f7}{g}(x)[/$$]", converted)
        self.assertEqual(transform_document(converted, "anki"), converted)
        self.assertEqual(transform_document(converted, "anki", True), source)

    def test_tex_scans_math_and_protects_literal_regions(self) -> None:
        source = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "Inline $f(x)$ and display \\[g(x)=1\\].\n"
            "% keep $comment(x)$ unchanged\n"
            "\\verb|$literal(x)$|\n"
            "\\begin{verbatim}\n$also_literal(x)$\n\\end{verbatim}\n"
            "\\begin{align}\nh(x)&=k(x)\\\\\n\\end{align}\n"
            "\\end{document}\n"
        )
        converted = transform_document(source, "tex")

        self.assertIn("% color-math: begin generated xcolor support", converted)
        self.assertIn(r"\usepackage{xcolor}", converted)
        self.assertNotRegex(converted, r"\\textcolor\{#[0-9A-Fa-f]{6}\}")
        self.assertIn(r"\textcolor{colormath7aa2f7}{f}", converted)
        self.assertIn("% keep $comment(x)$ unchanged", converted)
        self.assertIn(r"\verb|$literal(x)$|", converted)
        self.assertIn("\\begin{verbatim}\n$also_literal(x)$\n\\end{verbatim}", converted)
        self.assertEqual(transform_document(converted, "tex"), converted)
        self.assertEqual(transform_document(converted, "tex", True), source)

    def test_file_suffix_detection_is_narrow(self) -> None:
        self.assertEqual(detect_format(Path("lesson.ipynb")), "jupyter")
        self.assertEqual(detect_format(Path("paper.tex")), "tex")
        self.assertEqual(detect_format(Path("cards.tsv")), "markdown")
        self.assertEqual(detect_format(Path("cards.tsv"), "anki"), "anki")


class LosslessRegressionTests(unittest.TestCase):
    maxDiff = None

    def assert_lossless(self, source: str, expected: str) -> str:
        actual = convert_text(source)
        self.assertEqual(actual, expected)
        self.assertEqual(uncolor_text(actual), source)
        self.assertEqual(convert_text(actual), actual)
        return actual

    def test_comment_braces_do_not_change_grouping(self) -> None:
        cases = (
            (
                "$$f(x)% }\n+g(x)$$",
                "$$\\textcolor{#7aa2f7}{f}(x)% }\n"
                "+\\textcolor{#7aa2f7}{g}(x)$$",
            ),
            (
                "$$f(x)% {\n+g(x)$$",
                "$$\\textcolor{#7aa2f7}{f}(x)% {\n"
                "+\\textcolor{#7aa2f7}{g}(x)$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assert_lossless(source, expected)

    def test_nested_tilde_fence_is_byte_exact(self) -> None:
        source = (
            "- item\n"
            "  > [!note]\n"
            "  > ~~~~latex\n"
            "  > $$y(x(g(3)))$$\n"
            "  > ~~~~\n"
        )
        self.assert_lossless(source, source)
        self.assertEqual(parse_math_blocks(source), [])

    def test_verb_payload_is_not_colored_or_inspected(self) -> None:
        for source in (
            r"$$\verb|y(x(g(3)))|$$",
            r"$$\verb*|y(x(g(3)))|$$",
        ):
            with self.subTest(source=source, property="conversion"):
                self.assert_lossless(source, source)
            with self.subTest(source=source, property="semantic parser"):
                self.assertEqual(
                    format_math_structure(parse_math_body(source[2:-2])),
                    "No nested function calls found.",
                )

    def test_scalar_operators_are_not_routed_as_matrices(self) -> None:
        cases = (
            (
                r"$$\sum_{i=1}^{n} x_i$$",
                r"$$\textcolor{#e0af68}{\sum_{\textcolor{#9ece6a}{i=1}}"
                r"^{\textcolor{#bb9af7}{n}}} x_\textcolor{#9ece6a}{i}$$",
            ),
            (
                r"$$\int_0^1 f(x)\,dx$$",
                r"$$\textcolor{#e0af68}{\int_\textcolor{#9ece6a}{0}"
                r"^\textcolor{#bb9af7}{1}} \textcolor{#7aa2f7}{f}(x)"
                r"\textcolor{white}{\,}dx$$",
            ),
            (
                r"$$\lim_{x\to0} f(x)$$",
                r"$$\textcolor{#e0af68}{\lim_{\textcolor{#9ece6a}{x\to0}}} "
                r"\textcolor{#7aa2f7}{f}(x)$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertIsNone(convert_matrix_block(source))
                self.assert_lossless(source, expected)

    def test_nested_array_inside_delimiters_is_a_matrix_operand(self) -> None:
        source = (
            r"$$\mathbf{M}=\left(\begin{array}{cc}a&b\\c&d"
            r"\end{array}\right)$$"
        )
        expected = (
            r"$$\textcolor{#7aa2f7}{\mathbf{M}}\textcolor{white}{=}"
            r"\textcolor{#bb9af7}{\left(\begin{array}{cc}"
            r"\textcolor{#7aa2f7}{a}&\textcolor{#bb9af7}{b}\\"
            r"\textcolor{#9ece6a}{c}&\textcolor{#7aa2f7}{d}"
            r"\end{array}\right)}$$"
        )
        self.assertEqual(convert_matrix_block(source), expected)
        self.assert_lossless(source, expected)

    def test_control_sequences_and_script_operands_stay_whole(self) -> None:
        cases = (
            (
                r"$$\operatorname*{arg\,max}_{x} f(x)$$",
                r"$$\textcolor{#7aa2f7}{\operatorname*{arg"
                r"\textcolor{white}{\,}max}}_"
                r"{\textcolor{#9ece6a}{x}} \textcolor{#7aa2f7}{f}(x)$$",
            ),
            (
                r"$$\Bigl(y(x)\Bigr)$$",
                r"$$\Bigl(\textcolor{#7aa2f7}{y}(x)\Bigr)$$",
            ),
            (
                r"$$\bigg\lVert y(x) \bigg\rVert$$",
                r"$$\bigg\lVert \textcolor{#7aa2f7}{y}(x) \bigg\rVert$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assert_lossless(source, expected)

    def test_math_style_declarations_are_not_wrapped(self) -> None:
        for style in (
            "displaystyle",
            "textstyle",
            "scriptstyle",
            "scriptscriptstyle",
        ):
            source = rf"$$f(x)+\{style} g(x)$$"
            expected = (
                rf"$$\textcolor{{#7aa2f7}}{{f}}(x)+\{style} "
                r"\textcolor{#7aa2f7}{g}(x)$$"
            )
            with self.subTest(style=style):
                actual = self.assert_lossless(source, expected)
                self.assertNotIn(rf"{{\{style}}}", actual)

    def test_composite_closers_do_not_hide_following_source(self) -> None:
        cases = (
            r"\left(x\right)",
            r"\|x\|",
            r"\begin{bmatrix}x\end{bmatrix}",
        )
        suffix = (
            r"+\textcolor{#7aa2f7}{f}(y)+z^\textcolor{#bb9af7}{2}"
            r"+\textcolor{#e0af68}{\sum_{\textcolor{#9ece6a}{i=1}}"
            r"^{\textcolor{#bb9af7}{n}}}i"
        )
        for prefix in cases:
            source = f"$${prefix}+f(y)+z^2+\\sum_{{i=1}}^{{n}}i$$"
            with self.subTest(prefix=prefix):
                colored_prefix = (
                    r"\begin{bmatrix}\textcolor{#7aa2f7}{x}\end{bmatrix}"
                    if prefix == r"\begin{bmatrix}x\end{bmatrix}"
                    else prefix
                )
                self.assert_lossless(source, f"$${colored_prefix}{suffix}$$")

    def test_linebreak_optional_spacing_stays_attached(self) -> None:
        source = "$$\\frac{d}{dx}f(x)=g(x)\\\\[2pt]\n+h(x)$$"
        expected = (
            "$$\\frac{d}{dx}\\textcolor{#7aa2f7}{f(x)}"
            "\\textcolor{white}{=}\\textcolor{#7aa2f7}{g(x)}"
            "\\\\[2pt]\n\\textcolor{white}{+}"
            "\\textcolor{#7aa2f7}{h(x)}$$"
        )
        actual = self.assert_lossless(source, expected)
        self.assertIn("\\\\[2pt]", actual)
        self.assertNotIn(r"\\\textcolor{#7aa2f7}{[2pt]}", actual)

    def test_operator_comments_do_not_detach_limits(self) -> None:
        source = "$$\\sum % keep\n\\limits_{i=1}^{n}a_i$$"
        expected = (
            "$$\\textcolor{#e0af68}{\\sum % keep\n"
            "\\limits_{\\textcolor{#9ece6a}{i=1}}"
            "^{\\textcolor{#bb9af7}{n}}}"
            "a_\\textcolor{#9ece6a}{i}$$"
        )
        actual = self.assert_lossless(source, expected)
        self.assertNotIn(r"\textcolor{white}{\limits}", actual)

    def test_comments_before_required_arguments_stay_attached(self) -> None:
        cases = (
            (
                "$$\\frac{d}{dx}f(x)=\\hat % keep\n{x}$$",
                "$$\\frac{d}{dx}\\textcolor{#7aa2f7}{f(x)}"
                "\\textcolor{white}{=}"
                "\\textcolor{#7aa2f7}{\\hat % keep\n{x}}$$",
            ),
            (
                "$$x^ % keep\n{2}$$",
                "$$x^ % keep\n{\\textcolor{#bb9af7}{2}}$$",
            ),
            (
                "$$\\mathbf % keep\n{A}=\\mathbf{B}$$",
                "$$\\textcolor{#7aa2f7}{\\mathbf % keep\n{A}}"
                "\\textcolor{white}{=}"
                "\\textcolor{#bb9af7}{\\mathbf{B}}$$",
            ),
            (
                "$$\\frac % keep\n{1}{x}$$",
                "$$\\frac % keep\n{\\textcolor{#e0af68}{1}}"
                "{\\textcolor{#bb9af7}{x}}$$",
            ),
            (
                "$$\\bigl % keep\n(f(x)\\bigr)$$",
                "$$\\bigl % keep\n("
                "\\textcolor{#7aa2f7}{f}(x)\\bigr)$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assert_lossless(source, expected)

    def test_negated_relations_stay_atomic(self) -> None:
        for relation in (r"\not\in", r"\not=", r"\not\subseteq"):
            source = f"$$x{relation} A+f(y)$$"
            expected = (
                f"$$x{relation} A+"
                r"\textcolor{#7aa2f7}{f}(y)$$"
            )
            with self.subTest(relation=relation):
                self.assert_lossless(source, expected)

    def test_dimension_command_is_not_split(self) -> None:
        source = r"$$\frac{d}{dx}f(x)=a\above 1pt b$$"
        expected = (
            r"$$\frac{d}{dx}\textcolor{#7aa2f7}{f(x)}"
            r"\textcolor{white}{=}\textcolor{#7aa2f7}{a}"
            r"\above 1pt b$$"
        )
        self.assert_lossless(source, expected)

    def test_optional_color_models_stay_opaque(self) -> None:
        cases = (
            (
                r"$$\frac{d}{dx}f(x)=\textcolor[RGB]{255,0,0}{g(x)}$$",
                r"$$\frac{d}{dx}\textcolor{#7aa2f7}{f(x)}"
                r"\textcolor{white}{=}\textcolor[RGB]{255,0,0}{g(x)}$$",
            ),
            (
                r"$$\mathbf{A}=\colorbox[rgb]{1,0,0}{\mathbf{x}}$$",
                r"$$\mathbf{A}\textcolor{white}{=}"
                r"\colorbox[rgb]{1,0,0}{\mathbf{x}}$$",
            ),
            (
                r"$$\mathbf{A}=\fcolorbox[rgb]{0,0,0}{1,1,1}{\mathbf{x}}$$",
                r"$$\mathbf{A}\textcolor{white}{=}"
                r"\fcolorbox[rgb]{0,0,0}{1,1,1}{\mathbf{x}}$$",
            ),
            (
                r"$$\mathbf{A}=\fcolorbox[rgb]{0,0,0}"
                r"[rgb]{1,1,1}{\mathbf{x}}$$",
                r"$$\mathbf{A}\textcolor{white}{=}"
                r"\fcolorbox[rgb]{0,0,0}[rgb]{1,1,1}{\mathbf{x}}$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assert_lossless(source, expected)

    def test_unknown_commands_do_not_hide_the_equation_tail(self) -> None:
        self.assert_lossless(
            r"$$y=\binom{n}{k}+f(t)$$",
            r"$$y\textcolor{white}{=}\binom{\textcolor{#7aa2f7}{n}}"
            r"{\textcolor{#bb9af7}{k}}+\textcolor{#7aa2f7}{f}(t)$$",
        )

    def test_scalar_subscript_does_not_enable_matrix_mode(self) -> None:
        source = r"$$x_i=\frac{a+b}{c+d}+f(t)$$"
        expected = (
            r"$$x_\textcolor{#9ece6a}{i}\textcolor{white}{=}"
            r"\frac{\textcolor{#7aa2f7}{a}+\textcolor{#bb9af7}{b}}"
            r"{\textcolor{#bb9af7}{c}+\textcolor{#9ece6a}{d}}+"
            r"\textcolor{#7aa2f7}{f}(t)$$"
        )
        self.assertIsNone(convert_matrix_block(source))
        self.assert_lossless(source, expected)

    def test_structured_objects_color_their_contents(self) -> None:
        cases = (
            (
                r"$$y=\frac{a+b}{c+d}$$",
                r"$$y\textcolor{white}{=}\frac{\textcolor{#7aa2f7}{a}"
                r"+\textcolor{#bb9af7}{b}}{\textcolor{#bb9af7}{c}"
                r"+\textcolor{#9ece6a}{d}}$$",
            ),
            (
                r"$$y=\sqrt{a+b}+\widehat{c+d}$$",
                r"$$y\textcolor{white}{=}\sqrt{\textcolor{#7aa2f7}{a}"
                r"+\textcolor{#bb9af7}{b}}+\widehat{"
                r"\textcolor{#7aa2f7}{c}+\textcolor{#bb9af7}{d}}$$",
            ),
            (
                r"$$\begin{bmatrix}a&b\\c&d\end{bmatrix}$$",
                r"$$\begin{bmatrix}\textcolor{#7aa2f7}{a}&"
                r"\textcolor{#bb9af7}{b}\\\textcolor{#9ece6a}{c}&"
                r"\textcolor{#7aa2f7}{d}\end{bmatrix}$$",
            ),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assert_lossless(source, expected)

    def test_builtin_functions_and_common_aliases_are_colored(self) -> None:
        self.assert_lossless(
            r"$$y=\sin(x)+\cos(y)$$",
            r"$$y\textcolor{white}{=}\textcolor{#7aa2f7}{\sin}(x)+"
            r"\textcolor{#7aa2f7}{\cos}(y)$$",
        )
        self.assert_lossless(
            r"$$a\le b\ne c\implies d\iff e\pm f$$",
            r"$$a\textcolor{white}{\le} b\textcolor{white}{\ne} c"
            r"\textcolor{#f7768e}{\implies} d"
            r"\textcolor{#f7768e}{\iff} e\textcolor{white}{\pm} f$$",
        )

    def test_reserved_converters_now_handle_their_forms(self) -> None:
        cases = (
            (
                convert_align_block,
                r"$$\begin{aligned}a&=b+c\\d&=e+f\end{aligned}$$",
                r"$$\begin{aligned}\textcolor{#7aa2f7}{a}&"
                r"\textcolor{white}{=}\textcolor{#bb9af7}{b}+"
                r"\textcolor{#9ece6a}{c}\\\textcolor{#9ece6a}{d}&"
                r"\textcolor{white}{=}\textcolor{#7aa2f7}{e}+"
                r"\textcolor{#bb9af7}{f}\end{aligned}$$",
            ),
            (
                convert_integral_line,
                r"$$I=\int_0^1 \sin(x)\,dx$$",
                r"$$I\textcolor{white}{=}\textcolor{#e0af68}{\int_"
                r"\textcolor{#9ece6a}{0}^\textcolor{#bb9af7}{1}} "
                r"\textcolor{#7aa2f7}{\sin}(x)\textcolor{white}{\,}dx$$",
            ),
            (
                convert_limit_line,
                r"$$L=\lim_{x\to0}\frac{\sin x}{x}$$",
                r"$$L\textcolor{white}{=}\textcolor{#e0af68}{\lim_{"
                r"\textcolor{#9ece6a}{x\to0}}}\frac{"
                r"\textcolor{#7aa2f7}{\sin} \textcolor{#bb9af7}{x}}"
                r"{\textcolor{#bb9af7}{x}}$$",
            ),
        )
        for converter, source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(converter(source), expected)
                self.assert_lossless(source, expected)

    def test_undo_only_changes_active_display_math(self) -> None:
        source = (
            r"Prose \textcolor{red}{word}." "\n"
            "$$x % \\textcolor{red}{commented}\n"
            r"+\verb|\textcolor{blue}{verbatim}|"
            r"+\textcolor{green}{y}+\color{orange}{z}$$"
        )
        expected = (
            r"Prose \textcolor{red}{word}." "\n"
            "$$x % \\textcolor{red}{commented}\n"
            r"+\verb|\textcolor{blue}{verbatim}|+y+z$$"
        )
        self.assertEqual(uncolor_text(source), expected)


class AtomicIOTests(unittest.TestCase):
    def test_bom_and_mixed_newlines_are_preserved(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "note.md"
            source = codecs.BOM_UTF8 + b"one\r\ntwo\nthree\rfour"
            path.write_bytes(source)

            text, original = file_io.read_utf8(path)
            output = file_io.encode_utf8(text.replace("two", "TWO"), original)

            self.assertTrue(file_io.replace_bytes(path, output, original))
            self.assertEqual(
                path.read_bytes(),
                codecs.BOM_UTF8 + b"one\r\nTWO\nthree\rfour",
            )

    def test_unchanged_file_is_not_rewritten(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "note.md"
            source = b"unchanged\r\n"
            path.write_bytes(source)

            with patch.object(
                file_io.tempfile,
                "mkstemp",
                side_effect=AssertionError("temporary file created"),
            ):
                self.assertFalse(file_io.replace_bytes(path, source, source))

    def test_failed_replace_keeps_original_and_cleans_up(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "note.md"
            source = b"original\n"
            path.write_bytes(source)

            with patch.object(file_io.os, "replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    file_io.replace_bytes(path, b"replacement\n", source)

            self.assertEqual(path.read_bytes(), source)
            self.assertEqual(list(root.glob(".note.md.*.tmp")), [])

    def test_concurrent_edit_is_never_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "note.md"
            source = b"original\n"
            external = b"edited elsewhere\n"
            path.write_bytes(external)

            with self.assertRaisesRegex(OSError, "file changed"):
                file_io.replace_bytes(path, b"our output\n", source)

            self.assertEqual(path.read_bytes(), external)
            self.assertEqual(list(root.glob(".note.md.*.tmp")), [])


class GeneratedOutputTests(unittest.TestCase):
    def test_refresh_writes_only_generated(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            expected = root / "expected"
            generated = root / "generated"
            original.mkdir()
            expected.mkdir()
            source = b"Prose\n$$y(x(g(3)))$$\n"
            expected_bytes = b"expected stays untouched\n"
            (original / "case.md").write_bytes(source)
            (expected / "case.md").write_bytes(expected_bytes)

            with patch.dict(
                globals(),
                {"ORIGINAL": original, "EXPECTED": expected, "GENERATED": generated},
            ):
                refresh_generated()

            text, _ = file_io.read_utf8(original / "case.md")
            self.assertEqual((original / "case.md").read_bytes(), source)
            self.assertEqual((expected / "case.md").read_bytes(), expected_bytes)
            self.assertEqual(
                (generated / "case.md").read_bytes(),
                convert_text(text).encode("utf-8"),
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-generated", action="store_true")
    args = parser.parse_args(argv)

    if args.update_generated:
        refresh_generated()

    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return int(not result.wasSuccessful())


if __name__ == "__main__":
    raise SystemExit(main())
