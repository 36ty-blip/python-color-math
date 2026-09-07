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
e^{\\sqrt{\\sin(f(y)^n)}}
\\right]
\&=
e^{\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\frac{d}{dx}
\\left\[
\\sqrt{\\sin(f(y)^n)}
\\right]
\\
\&=
e^{\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\frac{1}{2\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\frac{d}{dx}
\\left\[
\\sin(f(y)^n)
\\right]
\\
\&=
e^{\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\frac{1}{2\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\cos(f(y)^n)
\\cdot
\\frac{d}{dx}
\\left\[
f(y)^n
\\right]
\\
\&=
e^{\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\frac{1}{2\\sqrt{\\sin(f(y)^n)}}
\\cdot
\\cos(f(y)^n)
\\cdot
n f(y)^{n-1}
\\cdot
f'(y)y'
\\end{aligned}
$$

\---

## 2\. Multi-line algebra simplification using `aligned`

$$
\\begin{aligned}
(x+y)^3
\&=
(x+y)(x+y)^2
\\
\&=
(x+y)(x^2+2xy+y^2)
\\
\&=
x^3+2x^2y+xy^2+x^2y+2xy^2+y^3
\\
\&=
x^3+3x^2y+3xy^2+y^3
\\end{aligned}
$$

\---

## 3\. Multi-line matrix equation

$$
\\begin{aligned}
\\mathbf{A}\\mathbf{x}
\&= 
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
\&=
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
\\mathbf{I}\_3
===

\\begin{bmatrix}
1 \& 0 \& 0 \\
0 \& 1 \& 0 \\
0 \& 0 \& 1
\\end{bmatrix}
$$

\---

## 13\. Diagonal matrix

$$
\\mathbf{D}
===

\\begin{bmatrix}
\\lambda\_1 \& 0 \& 0 \\
0 \& \\lambda\_2 \& 0 \\
0 \& 0 \& \\lambda\_3
\\end{bmatrix}
$$

\---

## 14\. Matrix transpose

$$
\\begin{bmatrix}
a \& b \& c \\
d \& e \& f
\\end{bmatrix}^{T}
===

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
===

\\begin{bmatrix}
\\mathbf{A}\\mathbf{x}+\\mathbf{B}\\mathbf{y} \\
\\mathbf{C}\\mathbf{x}+\\mathbf{D}\\mathbf{y}
\\end{bmatrix}
$$

\---

## 19\. Small matrix inside an equation

$$
\\det
\\begin{bmatrix}
a \& b \\
c \& d
\\end{bmatrix}
===

ad-bc
$$

\---

## 20\. Tensor slice as a matrix

$$
\\mathcal{T}\_{::k}
===

\\begin{bmatrix}
t\_{11k} \& t\_{12k} \& t\_{13k} \\
t\_{21k} \& t\_{22k} \& t\_{23k} \\
t\_{31k} \& t\_{32k} \& t\_{33k}
\\end{bmatrix}
$$

\---

## 21\. Tensor unfolding matrix

$$
\\mathbf{T}\_{(1)}
===

\\begin{bmatrix}
t\_{111} \& t\_{121} \& t\_{131} \& t\_{112} \& t\_{122} \& t\_{132} \\
t\_{211} \& t\_{221} \& t\_{231} \& t\_{212} \& t\_{222} \& t\_{232} \\
t\_{311} \& t\_{321} \& t\_{331} \& t\_{312} \& t\_{322} \& t\_{332}
\\end{bmatrix}
$$

\---

## 22\. Piecewise function using `cases`

$$
f(x)
===

\\begin{cases}
x^2, \& x \\ge 0 \\
-x, \& x < 0
\\end{cases}
$$

\---

## 23\. System of equations using `cases`

$$
\\begin{cases}
ax+by+cz=r\_1 \\
dx+ey+fz=r\_2 \\
gx+hy+iz=r\_3
\\end{cases}
$$

\---

## 24\. System of equations using `aligned`

$$
\\begin{aligned}
ax+by+cz \&= r\_1 \\
dx+ey+fz \&= r\_2 \\
gx+hy+iz \&= r\_3
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

