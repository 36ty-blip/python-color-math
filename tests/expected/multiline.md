# Multi-line Equation and Matrix Tests

These examples are written for Obsidian math blocks.

## Rules used

* Put `$$` on its own line.
* Do not add extra `\&` at the start or end of normal matrix rows.
* Use `\&` only between columns.
* Use `\\\\` to end a row.
* Use `aligned` for multi-line equations.
* Use `array` when you need column formatting, vertical separator lines, or augmented matrices.

\---

## 1\. Multi-line chain rule using `aligned`

$$
\\begin{aligned}
\\frac{d}{dx}
\\left\[
e^{\textcolor{#bb9af7}{\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^n)}}}
\\right]
\&\textcolor{white}{=}
e^{\textcolor{#bb9af7}{\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^n)}}}
\\cdot
\\frac{d}{dx}
\\left\[
\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})}
\\right]
\\
\&\textcolor{white}{=}
e^{\textcolor{#bb9af7}{\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^n)}}}
\\cdot
\\frac{1}{2\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})}}
\\cdot
\\frac{d}{dx}
\\left\[
\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})
\\right]
\\
\&\textcolor{white}{=}
e^{\textcolor{#bb9af7}{\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^n)}}}
\\cdot
\\frac{1}{2\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})}}
\\cdot
\\\textcolor{#7aa2f7}{cos}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})
\\cdot
\\frac{d}{dx}
\\left\[
\textcolor{#7aa2f7}{f}(y)^\textcolor{#bb9af7}{n}
\\right]
\\
\&\textcolor{white}{=}
e^{\textcolor{#bb9af7}{\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^n)}}}
\\cdot
\\frac{1}{2\\sqrt{\\\textcolor{#7aa2f7}{sin}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})}}
\\cdot
\\\textcolor{#7aa2f7}{cos}(\textcolor{#bb9af7}{f}(y)^\textcolor{#bb9af7}{n})
\\cdot
n \textcolor{#7aa2f7}{f}(y)^{\textcolor{#bb9af7}{n-1}}
\\cdot
\textcolor{#7aa2f7}{f'}(y)y'
\\end{aligned}
$$

\---

## 2\. Multi-line algebra simplification using `aligned`

$$
\\begin{aligned}
(x+y)^\textcolor{#bb9af7}{3}
\&\textcolor{white}{=}
(x+y)(x+y)^\textcolor{#bb9af7}{2}
\\
\&\textcolor{white}{=}
(x+y)(x^\textcolor{#bb9af7}{2}+2xy+y^\textcolor{#bb9af7}{2})
\\
\&\textcolor{white}{=}
x^\textcolor{#bb9af7}{3}+2x^\textcolor{#bb9af7}{2}y+xy^\textcolor{#bb9af7}{2}+x^\textcolor{#bb9af7}{2}y+2xy^\textcolor{#bb9af7}{2}+y^\textcolor{#bb9af7}{3}
\\
\&\textcolor{white}{=}
x^\textcolor{#bb9af7}{3}+3x^\textcolor{#bb9af7}{2}y+3xy^\textcolor{#bb9af7}{2}+y^\textcolor{#bb9af7}{3}
\\end{aligned}
$$

\---

## 3\. Multi-line matrix equation

$$
\\begin{aligned}
\\mathbf{A}\\mathbf{x}
\&\textcolor{white}{=} 
\\begin{bmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{bmatrix}
\\begin{bmatrix}
x \\
y \\
z
\\end{bmatrix}
\\
\&\textcolor{white}{=}
\\begin{bmatrix}
ax+by+cz \\
dx+ey+fz \\
gx+hy+iz
\\end{bmatrix}
\\end{aligned}
$$

\---

# Matrix Environment Tests

## 4\. Plain matrix: `matrix`

$$
\\begin{matrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{matrix}
$$

\---

## 5\. Parentheses matrix: `pmatrix`

$$
\\begin{pmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{pmatrix}
$$

\---

## 6\. Square bracket matrix: `bmatrix`

$$
\\begin{bmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{bmatrix}
$$

\---

## 7\. Curly brace matrix: `Bmatrix`

$$
\\begin{Bmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{Bmatrix}
$$

\---

## 8\. Determinant matrix: `vmatrix`

$$
\\begin{vmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{vmatrix}
$$

\---

## 9\. Double-bar norm matrix: `Vmatrix`

$$
\\begin{Vmatrix}
a \& b \& c \\
d \& e \& f \\
g \& h \& i
\\end{Vmatrix}
$$

\---

# Practical Matrix Tests

## 10\. Column vector

$$
\\begin{bmatrix}
x \\
y \\
z
\\end{bmatrix}
$$

\---

## 11\. Row vector

$$
\\begin{bmatrix}
x \& y \& z
\\end{bmatrix}
$$

\---

## 12\. Identity matrix

$$
\\\textcolor{#bb9af7}{m}\textcolor{#9ece6a}{a}\textcolor{#e0af68}{t}\textcolor{#e0af68}{h}\textcolor{#e0af68}{b}\textcolor{#e0af68}{f}\textcolor{#e0af68}{{I}}\_\textcolor{#e0af68}{3}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\\textcolor{#bb9af7}{b}\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{g}\textcolor{#9ece6a}{i}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{{bmatrix}}
\textcolor{#e0af68}{1} \& \textcolor{#e0af68}{0} \& \textcolor{#e0af68}{0} \\
\textcolor{#e0af68}{0} \& \textcolor{#e0af68}{1} \& \textcolor{#e0af68}{0} \\
\textcolor{#e0af68}{0} \& \textcolor{#e0af68}{0} \& \textcolor{#e0af68}{1}
\\\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{{bmatrix}}
$$

\---

## 13\. Diagonal matrix

$$
\\\textcolor{#bb9af7}{m}\textcolor{#9ece6a}{a}\textcolor{#e0af68}{t}\textcolor{#e0af68}{h}\textcolor{#e0af68}{b}\textcolor{#e0af68}{f}\textcolor{#e0af68}{{D}}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\\textcolor{#bb9af7}{b}\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{g}\textcolor{#9ece6a}{i}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{{bmatrix}}
\\\textcolor{#9ece6a}{l}\textcolor{#9ece6a}{a}\textcolor{#9ece6a}{m}\textcolor{#9ece6a}{b}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{a}\_\textcolor{#e0af68}{1} \& \textcolor{#e0af68}{0} \& \textcolor{#e0af68}{0} \\
\textcolor{#e0af68}{0} \& \\\textcolor{#9ece6a}{l}\textcolor{#9ece6a}{a}\textcolor{#9ece6a}{m}\textcolor{#9ece6a}{b}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{a}\_\textcolor{#e0af68}{2} \& \textcolor{#e0af68}{0} \\
\textcolor{#e0af68}{0} \& \textcolor{#e0af68}{0} \& \\\textcolor{#9ece6a}{l}\textcolor{#9ece6a}{a}\textcolor{#9ece6a}{m}\textcolor{#9ece6a}{b}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{a}\_\textcolor{#e0af68}{3}
\\\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{{bmatrix}}
$$

\---

## 14\. Matrix transpose

$$
\\begin{bmatrix}
a \& b \& c \\
d \& e \& f
\\end{bmatrix}^{\textcolor{#bb9af7}{T}}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\begin{bmatrix}
a \& d \\
b \& e \\
c \& f
\\end{bmatrix}
$$

\---

## 15\. Augmented matrix using `array`

$$
\\left\[
\\begin{array}{ccc|c}
1 \& 2 \& 3 \& 4 \\
0 \& 1 \& 5 \& 6 \\
0 \& 0 \& 1 \& 7
\\end{array}
\\right]
$$

\---

## 16\. Matrix with horizontal divider using `array`

$$
\\left\[
\\begin{array}{ccc}
a \& b \& c \\
d \& e \& f \\
\\hline
g \& h \& i
\\end{array}
\\right]
$$

\---

## 17\. Block matrix

$$
\\begin{bmatrix}
\\mathbf{A} \& \\mathbf{B} \\
\\mathbf{C} \& \\mathbf{D}
\\end{bmatrix}
$$

\---

## 18\. Block matrix equation

$$
\\begin{bmatrix}
\\mathbf{A} \& \\mathbf{B} \\
\\mathbf{C} \& \\mathbf{D}
\\end{bmatrix}
\\begin{bmatrix}
\\mathbf{x} \\
\\mathbf{y}
\\end{bmatrix}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\begin{bmatrix}
\\mathbf{A}\\mathbf{x}+\\mathbf{B}\\mathbf{y} \\
\\mathbf{C}\\mathbf{x}+\\mathbf{D}\\mathbf{y}
\\end{bmatrix}
$$

\---

## 19\. Small matrix inside an equation

$$
\\\textcolor{#bb9af7}{d}\textcolor{#9ece6a}{e}\textcolor{#e0af68}{t}
\\\textcolor{#e0af68}{b}\textcolor{#e0af68}{e}\textcolor{#e0af68}{g}\textcolor{#e0af68}{i}\textcolor{#e0af68}{n}\textcolor{#e0af68}{{bmatrix}}
\textcolor{#e0af68}{a} \& \textcolor{#e0af68}{b} \\
\textcolor{#e0af68}{c} \& \textcolor{#e0af68}{d}
\\\textcolor{#e0af68}{e}\textcolor{#e0af68}{n}\textcolor{#e0af68}{d}\textcolor{#e0af68}{{bmatrix}}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\textcolor{#bb9af7}{a}\textcolor{#9ece6a}{d}\textcolor{white}{-}\textcolor{#9ece6a}{b}\textcolor{#9ece6a}{c}
$$

\---

## 20\. Tensor slice as a matrix

$$
\\\textcolor{#bb9af7}{m}\textcolor{#9ece6a}{a}\textcolor{#e0af68}{t}\textcolor{#e0af68}{h}\textcolor{#e0af68}{c}\textcolor{#e0af68}{a}\textcolor{#e0af68}{l}\textcolor{#e0af68}{{T}}\_\textcolor{#e0af68}{{::k}}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\\textcolor{#bb9af7}{b}\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{g}\textcolor{#9ece6a}{i}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{{bmatrix}}
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{11k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{12k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{13k}} \\
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{21k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{22k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{23k}} \\
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{31k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{32k}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{33k}}
\\\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{{bmatrix}}
$$

\---

## 21\. Tensor unfolding matrix

$$
\\\textcolor{#bb9af7}{m}\textcolor{#9ece6a}{a}\textcolor{#e0af68}{t}\textcolor{#e0af68}{h}\textcolor{#e0af68}{b}\textcolor{#e0af68}{f}\textcolor{#e0af68}{{T}}\_\textcolor{#e0af68}{{(1)}}
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\\textcolor{#bb9af7}{b}\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{g}\textcolor{#9ece6a}{i}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{{bmatrix}}
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{111}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{121}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{131}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{112}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{122}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{132}} \\
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{211}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{221}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{231}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{212}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{222}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{232}} \\
\textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{311}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{321}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{331}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{312}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{322}} \& \textcolor{#9ece6a}{t}\_\textcolor{#9ece6a}{{332}}
\\\textcolor{#9ece6a}{e}\textcolor{#9ece6a}{n}\textcolor{#9ece6a}{d}\textcolor{#9ece6a}{{bmatrix}}
$$

\---

## 22\. Piecewise function using `cases`

$$
\textcolor{#7aa2f7}{f}(x)
\textcolor{white}{=}\textcolor{white}{=}\textcolor{white}{=}

\\begin{cases}
x^\textcolor{#bb9af7}{2}, \& x \\ge 0 \\
-x, \& x \textcolor{white}{<} 0
\\end{cases}
$$

\---

## 23\. System of equations using `cases`

$$
\\begin{cases}
ax+by+cz\textcolor{white}{=}r\_1 \\
dx+ey+fz\textcolor{white}{=}r\_2 \\
gx+hy+iz\textcolor{white}{=}r\_3
\\end{cases}
$$

\---

## 24\. System of equations using `aligned`

$$
\\begin{aligned}
ax+by+cz \&\textcolor{white}{=} r\_1 \\
dx+ey+fz \&\textcolor{white}{=} r\_2 \\
gx+hy+iz \&\textcolor{white}{=} r\_3
\\end{aligned}
$$

\---

## 25\. Matrix with fractions

$$
\\begin{bmatrix}
\\frac{1}{a} \& \\frac{1}{b} \& \\frac{1}{c} \\
\\frac{1}{d} \& \\frac{1}{e} \& \\frac{1}{f} \\
\\frac{1}{g} \& \\frac{1}{h} \& \\frac{1}{i}
\\end{bmatrix}
$$

