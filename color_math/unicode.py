"""Unicode math mappings for python-color-math.

Bidirectional mapping between canonical LaTeX commands and Unicode math symbols.
Enables native recognition and coloring for clean/decluttered math syntax (e.g. \\frac{∂}{∂t}, ℏ, ∫, ∑, ≤, →).
"""
from __future__ import annotations

UNICODE_DIFFERENTIALS: dict[str, str] = {
    r"\partial": "∂",
}

UNICODE_CONSTANTS: dict[str, str] = {
    r"\hbar": "ℏ",
    r"\infty": "∞",
}

UNICODE_VECTORS: dict[str, str] = {
    r"\nabla": "∇",
}

UNICODE_INTEGRALS: dict[str, str] = {
    r"\int": "∫",
    r"\iint": "∬",
    r"\iiint": "∭",
    r"\oint": "∮",
}

UNICODE_BIG_OPERATORS: dict[str, str] = {
    r"\sum": "∑",
    r"\prod": "∏",
    r"\coprod": "∐",
    r"\bigcup": "⋃",
    r"\bigcap": "⋂",
}

UNICODE_RELATIONS: dict[str, str] = {
    r"\le": "≤",
    r"\leq": "≤",
    r"\ge": "≥",
    r"\geq": "≥",
    r"\ne": "≠",
    r"\neq": "≠",
    r"\approx": "≈",
    r"\sim": "∼",
    r"\equiv": "≡",
    r"\propto": "∝",
}

UNICODE_ARROWS: dict[str, str] = {
    r"\to": "→",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\leftrightarrow": "⟷",
    r"\mapsto": "↦",
    r"\implies": "⟹",
    r"\Longrightarrow": "⟹",
    r"\Rightarrow": "⇒",
    r"\Leftarrow": "⇐",
    r"\impliedby": "⟸",
    r"\Longleftarrow": "⟸",
    r"\iff": "⇔",
    r"\Leftrightarrow": "⇔",
    r"\uparrow": "↑",
    r"\downarrow": "↓",
}

UNICODE_SETS: dict[str, str] = {
    r"\in": "∈",
    r"\notin": "∉",
    r"\subset": "⊂",
    r"\subseteq": "⊆",
    r"\supset": "⊃",
    r"\supseteq": "⊇",
    r"\cup": "∪",
    r"\cap": "∩",
    r"\emptyset": "∅",
    r"\setminus": "∖",
    r"\forall": "∀",
    r"\exists": "∃",
    r"\nexists": "∄",
    r"\therefore": "∴",
    r"\because": "∵",
}

UNICODE_MULTIPLICATION: dict[str, str] = {
    r"\times": "×",
    r"\cdot": "·",
}

UNICODE_ADDITIVE: dict[str, str] = {
    r"\pm": "±",
    r"\mp": "∓",
}

# Standard Greek letters (BMP: U+0370 to U+03FF)
UNICODE_GREEK_LOWER_STANDARD: dict[str, str] = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\varepsilon": "ε",
    r"\zeta": "ζ",
    r"\eta": "η",
    r"\theta": "θ",
    r"\vartheta": "ϑ",
    r"\iota": "ι",
    r"\kappa": "κ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\xi": "ξ",
    r"\pi": "π",
    r"\varpi": "ϖ",
    r"\rho": "ρ",
    r"\varrho": "ϱ",
    r"\sigma": "σ",
    r"\varsigma": "ς",
    r"\tau": "τ",
    r"\upsilon": "υ",
    r"\phi": "φ",
    r"\varphi": "ϕ",
    r"\chi": "χ",
    r"\psi": "ψ",
    r"\omega": "ω",
}

# Mathematical Alphanumeric Greek letters (Plane 1 - Espanso style)
UNICODE_GREEK_LOWER_PLANE1: dict[str, str] = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\varepsilon": "ϵ",
    r"\zeta": "𝜁",  # U+1D70F
    r"\eta": "η",
    r"\theta": "θ",
    r"\vartheta": "ϑ",
    r"\iota": "ι",
    r"\kappa": "κ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\xi": "ξ",
    r"\pi": "𝜋",  # U+1D70B
    r"\varpi": "ϖ",
    r"\rho": "ρ",
    r"\varrho": "ϱ",
    r"\sigma": "σ",
    r"\varsigma": "ς",
    r"\tau": "τ",
    r"\upsilon": "υ",
    r"\phi": "φ",
    r"\varphi": "ϕ",
    r"\chi": "χ",
    r"\psi": "𝜓",  # U+1D713 (Mathematical Italic Small Psi)
    r"\omega": "𝜔",  # U+1D714
}

UNICODE_GREEK_UPPER_STANDARD: dict[str, str] = {
    r"\Gamma": "Γ",
    r"\Delta": "Δ",
    r"\Theta": "Θ",
    r"\Lambda": "Λ",
    r"\Xi": "Ξ",
    r"\Pi": "Π",
    r"\Sigma": "Σ",
    r"\Upsilon": "Υ",
    r"\Phi": "Φ",
    r"\Psi": "Ψ",
    r"\Omega": "Ω",
}

UNICODE_GREEK_UPPER_PLANE1: dict[str, str] = {
    r"\Gamma": "𝚪",  # U+1D6AA
    r"\Delta": "Δ",
    r"\Theta": "Θ",
    r"\Lambda": "Λ",
    r"\Xi": "Ξ",
    r"\Pi": "Π",
    r"\Sigma": "Σ",
    r"\Upsilon": "Υ",
    r"\Phi": "Φ",
    r"\Psi": "Ψ",
    r"\Omega": "Ω",
}

# Delimiters that MUST NOT be converted to Unicode when attached to \left, \right, or sizing commands
PROTECTED_DELIMITER_MACROS = frozenset({
    "langle",
    "rangle",
    "lceil",
    "rceil",
    "lfloor",
    "rfloor",
    "vert",
    "Vert",
    "uparrow",
    "downarrow",
    "updownarrow",
    "Uparrow",
    "Downarrow",
    "Updownarrow",
})

# Auto-repair mapping for broken TeX syntax (e.g. \left⟨ -> \left\langle)
DELIMITER_AUTO_REPAIR: dict[str, str] = {
    "⟨": r"\langle",
    "⟩": r"\rangle",
    "⌈": r"\lceil",
    "⌉": r"\rceil",
    "⌊": r"\lfloor",
    "⌋": r"\rfloor",
    "‖": r"\|",
    "⎸": r"\vert",
}
