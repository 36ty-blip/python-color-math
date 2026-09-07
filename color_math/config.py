# config.py
from __future__ import annotations
from dataclasses import dataclass

DEFAULT_COLORS = {
    "main": "#7aa2f7",
    "orange": "#e0af68",
    "dot": "white",
    "derivative": "#bb9af7",
    "chain": "#9ece6a",
    "upper": "#bb9af7",
    "relation": "white",
    "arrow": "#f7768e",
    "set": "#bb9af7",
    "spacing": "white",
    "parameter": "#bb9af7",
    "unit": "#73daca",
}

COLORS = dict(DEFAULT_COLORS)


BIG_OPERATORS = {
    r"\sum",
    r"\prod",
    r"\coprod",
    r"\bigcup",
    r"\bigcap",
    r"\bigsqcup",
    r"\bigvee",
    r"\bigwedge",
    r"\bigoplus",
    r"\bigotimes",
}


INTEGRALS = {
    r"\int",
    r"\iint",
    r"\iiint",
    r"\oint",
}


LIMIT_OPERATORS = {
    r"\lim",
    r"\sup",
    r"\inf",
    r"\max",
    r"\min",
}


RELATIONS = {
    r"\le",
    r"\ge",
    r"\ne",
    r"\neq",
    r"\leq",
    r"\geq",
    r"\approx",
    r"\sim",
    r"\equiv",
    r"\propto",
    r"\simeq",
    r"\cong",
    r"\pm",
    r"\mp",
    r"\div",
    r"\ast",
    r"\star",
    r"\circ",
    r"\bullet",
    "=",
    "<",
    ">",
}


ARROWS = {
    r"\xrightarrow",
    r"\xleftarrow",
    r"\hookrightarrow",
    r"\hookleftarrow",
    r"\uparrow",
    r"\downarrow",
    r"\implies",
    r"\iff",
    r"\longrightarrow",
    r"\longleftarrow",
    r"\leftrightarrow",
    r"\rightarrow",
    r"\leftarrow",
    r"\Rightarrow",
    r"\Leftarrow",
    r"\Leftrightarrow",
    r"\mapsto",
    r"\to",
}


SET_SYMBOLS = {
    r"\forall",
    r"\exists",
    r"\land",
    r"\lor",
    r"\ni",
    r"\sqsubset",
    r"\sqsubseteq",
    r"\uplus",
    r"\notin",
    r"\subseteq",
    r"\supseteq",
    r"\subset",
    r"\supset",
    r"\setminus",
    r"\emptyset",
    r"\in",
    r"\cup",
    r"\cap",
}


SPACING_COMMANDS = {
    r"\,",
    r"\:",
    r"\;",
    r"\quad",
    r"\qquad",
}


MULTIPLICATION_SYMBOLS = {
    r"\cdot",
    r"\times",
    "·",
    "*",
}


FUNCTION_COMMANDS = {
    r"\arccos",
    r"\arcsin",
    r"\arctan",
    r"\cos",
    r"\cosh",
    r"\exp",
    r"\ln",
    r"\log",
    r"\sec",
    r"\sin",
    r"\sinh",
    r"\tan",
    r"\tanh",
}


# Combined commands that should receive special coloring
COLOR_COMMANDS = (
    BIG_OPERATORS
    | INTEGRALS
    | LIMIT_OPERATORS
    | RELATIONS
    | ARROWS
    | SET_SYMBOLS
    | SPACING_COMMANDS
    | MULTIPLICATION_SYMBOLS
)


# Longest first so scanner matches \longrightarrow before \to
SORTED_COLOR_COMMANDS = sorted(
    COLOR_COMMANDS,
    key=len,
    reverse=True,
)


MATH_CONSTANTS = {
    r"\pi",
    r"\varpi",
    r"\hbar",
    r"\infty",
    r"\ell",
    r"\aleph",
    r"\Re",
    r"\Im",
    r"\top",
    r"\bot",
}


MATH_ACCENTS = {
    r"\dot",
    r"\ddot",
    r"\dddot",
    r"\ddddot",
    r"\hat",
    r"\widehat",
    r"\tilde",
    r"\widetilde",
    r"\bar",
    r"\vec",
    r"\check",
    r"\breve",
    r"\acute",
    r"\grave",
    r"\mathring",
}


MATH_PARAMETERS = {
    r"\alpha",
    r"\beta",
    r"\gamma",
    r"\delta",
    r"\epsilon",
    r"\varepsilon",
    r"\zeta",
    r"\eta",
    r"\theta",
    r"\vartheta",
    r"\iota",
    r"\kappa",
    r"\lambda",
    r"\mu",
    r"\nu",
    r"\xi",
    r"\rho",
    r"\varrho",
    r"\sigma",
    r"\varsigma",
    r"\tau",
    r"\upsilon",
    r"\phi",
    r"\varphi",
    r"\chi",
    r"\psi",
    r"\omega",
    r"\Gamma",
    r"\Delta",
    r"\Theta",
    r"\Lambda",
    r"\Xi",
    r"\Pi",
    r"\Sigma",
    r"\Upsilon",
    r"\Phi",
    r"\Psi",
    r"\Omega",
}


MATH_FUNCTIONS = {
    r"\sin",
    r"\cos",
    r"\tan",
    r"\csc",
    r"\sec",
    r"\cot",
    r"\arcsin",
    r"\arccos",
    r"\arctan",
    r"\sinh",
    r"\cosh",
    r"\tanh",
    r"\coth",
    r"\ln",
    r"\log",
    r"\exp",
    r"\det",
    r"\gcd",
    r"\max",
    r"\min",
    r"\dim",
    r"\ker",
    r"\hom",
    r"\deg",
    r"\arg",
    r"\Pr",
    r"\sup",
    r"\inf",
}


RAINBOW_DELIMITER_COLORS: list[str] = [
    "#e0af68",  # Tier 0: Gold
    "#7aa2f7",  # Tier 1: Cyan / Blue
    "#bb9af7",  # Tier 2: Purple / Lavender
    "#f7768e",  # Tier 3: Coral / Pink
]


VARIABLE_HASH_PALETTE: list[str] = [
    "#7aa2f7",  # Tokyo Blue
    "#7dcfff",  # Tokyo Cyan
    "#bb9af7",  # Tokyo Purple
    "#f7768e",  # Tokyo Pink
    "#e0af68",  # Tokyo Orange/Gold
    "#9ece6a",  # Tokyo Green
    "#2ac3de",  # Light Cyan
    "#ff9e64",  # Peach
]


def hash_string_to_color(s: str, palette: list[str] = VARIABLE_HASH_PALETTE) -> str:
    """Deterministic string hashing for variable data-flow coloring."""
    h = 0
    for char in s:
        h = (h * 31 + ord(char)) & 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000
    idx = abs(h) % len(palette)
    return palette[idx]


@dataclass
class ColorMathOptions:
    enable_taxonomy: bool = False
    rainbow_delimiters: bool = False
    variable_data_flow: bool = False
    color_units: bool = False
    color_differentials: bool = False
    color_braket: bool = False
    color_dimensionless: bool = False

    @classmethod
    def extended(cls) -> ColorMathOptions:
        """Returns standard extended options matching Obsidian plugin defaults."""
        return cls(
            enable_taxonomy=True,
            rainbow_delimiters=True,
            variable_data_flow=False,
            color_units=True,
            color_differentials=True,
            color_braket=True,
            color_dimensionless=True,
        )

    @classmethod
    def all_enabled(cls) -> ColorMathOptions:
        """Returns options with all features enabled including variable data-flow."""
        return cls(
            enable_taxonomy=True,
            rainbow_delimiters=True,
            variable_data_flow=True,
            color_units=True,
            color_differentials=True,
            color_braket=True,
            color_dimensionless=True,
        )
