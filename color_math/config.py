from __future__ import annotations
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

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

THEMES: dict[str, dict[str, str]] = {
    "default": dict(DEFAULT_COLORS),
    "catppuccin": {
        "main": "#8aadf4",
        "orange": "#f5a97f",
        "dot": "white",
        "derivative": "#c6a0f6",
        "chain": "#a6da95",
        "upper": "#c6a0f6",
        "relation": "white",
        "arrow": "#ed8796",
        "set": "#c6a0f6",
        "spacing": "white",
        "parameter": "#c6a0f6",
        "unit": "#8bd5ca",
    },
    "nord": {
        "main": "#88c0d0",
        "orange": "#d08770",
        "dot": "white",
        "derivative": "#b48ead",
        "chain": "#a3be8c",
        "upper": "#b48ead",
        "relation": "white",
        "arrow": "#bf616a",
        "set": "#b48ead",
        "spacing": "white",
        "parameter": "#b48ead",
        "unit": "#8fbcbb",
    },
    "light": {
        "main": "#1a5fb4",
        "orange": "#c64600",
        "dot": "#222222",
        "derivative": "#613583",
        "chain": "#26a269",
        "upper": "#613583",
        "relation": "#222222",
        "arrow": "#c01c28",
        "set": "#613583",
        "spacing": "#222222",
        "parameter": "#613583",
        "unit": "#008080",
    },
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    "main": "Primary functions, terms, and outermost operations (e.g. f(x))",
    "derivative": "Derivative marks and differentiated functions (e.g. f'(x))",
    "chain": "Chain rule factors, inner differential stages (e.g. g'(x), y')",
    "orange": "Big operators, sums, integrals, and limits (e.g. \\sum, \\int, \\lim)",
    "dot": "Multiplication symbols, dots, and cross products (e.g. \\cdot, \\times)",
    "relation": "Equals, inequalities, and comparison symbols (e.g. =, <, \\le)",
    "arrow": "Implication and mapping arrows (e.g. \\to, \\implies)",
    "set": "Set theory relations and operators (e.g. \\in, \\subset)",
    "spacing": "LaTeX spacing and alignment commands (e.g. \\quad, \\,)",
    "upper": "Matrix exponents, transposes, and top indices (e.g. A^T, M^{-1})",
    "parameter": "Inner function parameters and indexed variables",
    "unit": "Physical units and dimensions (e.g. m/s, \\mu m, ^\\circ C)",
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
    r"\imath",
    r"\jmath",
    r"\mathrm{e}",
    r"\mathrm{i}",
    r"\mathrm{j}",
}


FONT_STYLE_MACROS = frozenset({
    r"\mathbf",
    r"\mathcal",
    r"\mathbb",
    r"\mathfrak",
    r"\mathsf",
    r"\mathtt",
    r"\mathit",
    r"\boldsymbol",
    r"\pmb",
})


STANDARD_BARE_FUNCTIONS = frozenset({
    "sin",
    "cos",
    "tan",
    "csc",
    "sec",
    "cot",
    "arcsin",
    "arccos",
    "arctan",
    "arccsc",
    "arcsec",
    "arccot",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "sech",
    "csch",
    "ln",
    "log",
    "exp",
    "det",
    "gcd",
    "max",
    "min",
    "dim",
    "ker",
    "hom",
    "deg",
    "arg",
    "Pr",
    "sup",
    "inf",
    "rank",
    "nullity",
    "tr",
    "trace",
    "span",
    "diag",
    "sgn",
})

EXTENDED_BARE_FUNCTIONS = frozenset({
    "adj",
    "col",
    "row",
    "nul",
    "im",
    "sp",
    "rg",
    "var",
    "cov",
    "std",
    "med",
    "cor",
    "pdf",
    "cdf",
    "pmf",
    "lcm",
    "mod",
    "rem",
    "div",
    "rot",
    "res",
    "erf",
    "abs",
    "sig",
    "dom",
    "ran",
    "cod",
    "tg",
    "ctg",
    "sh",
    "ch",
    "th",
    "cth",
    "lg",
    "lb",
    "aut",
    "end",
    "gal",
    "ann",
    "tor",
    "ext",
    "pic",
    "cl",
    "jac",
    "hes",
    "wr",
    "vol",
    "rms",
    "fft",
    "dft",
    "ord",
    "val",
    "num",
    "den",
    "sn",
    "cn",
    "dn",
    "avg",
    "len",
})

FULL_BARE_FUNCTIONS = STANDARD_BARE_FUNCTIONS | EXTENDED_BARE_FUNCTIONS
ALL_BARE_FUNCTIONS = FULL_BARE_FUNCTIONS
BARE_FUNCTIONS = FULL_BARE_FUNCTIONS


def get_bare_functions(options: ColorMathOptions | None = None) -> frozenset[str]:
    if options is not None and not options.extended_functions:
        return STANDARD_BARE_FUNCTIONS
    return FULL_BARE_FUNCTIONS


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
    r"\rank",
    r"\nullity",
    r"\tr",
    r"\trace",
    r"\span",
    r"\diag",
    r"\sgn",
    r"\adj",
    r"\col",
    r"\row",
    r"\nul",
    r"\im",
    r"\sp",
    r"\rg",
    r"\var",
    r"\cov",
    r"\std",
    r"\med",
    r"\cor",
    r"\pdf",
    r"\cdf",
    r"\pmf",
    r"\lcm",
    r"\mod",
    r"\rem",
    r"\rot",
    r"\res",
    r"\erf",
    r"\abs",
    r"\sig",
    r"\dom",
    r"\ran",
    r"\cod",
    r"\tg",
    r"\ctg",
    r"\sh",
    r"\ch",
    r"\th",
    r"\cth",
    r"\lg",
    r"\lb",
    r"\aut",
    r"\gal",
    r"\ann",
    r"\tor",
    r"\ext",
    r"\pic",
    r"\cl",
    r"\jac",
    r"\hes",
    r"\wr",
    r"\vol",
    r"\rms",
    r"\fft",
    r"\dft",
    r"\ord",
    r"\val",
    r"\num",
    r"\den",
    r"\sn",
    r"\cn",
    r"\dn",
    r"\avg",
    r"\len",
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
    color_alignment: bool = True
    color_single_constants: bool = True
    extended_functions: bool = True

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
            color_alignment=True,
            color_single_constants=True,
            extended_functions=True,
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


def get_theme(name: str) -> dict[str, str]:
    """Retrieve colors for a theme preset by name, or fallback to default."""
    theme = THEMES.get(name.lower())
    if theme is None:
        valid = ", ".join(THEMES.keys())
        raise ValueError(f"unknown theme '{name}'. Available themes: {valid}")
    return dict(theme)


def reset_colors() -> dict[str, str]:
    """Reset the global runtime COLORS dictionary back to factory DEFAULT_COLORS."""
    COLORS.clear()
    COLORS.update(DEFAULT_COLORS)
    return dict(COLORS)


def default_config_dict() -> dict[str, object]:
    """Return dictionary representation of the default configuration."""
    return {
        "theme": "default",
        "colors": dict(DEFAULT_COLORS),
        "options": asdict(ColorMathOptions()),
    }


def get_global_config_path() -> Path | None:
    """Return platform-appropriate XDG / AppData user configuration path."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "color-math" / "config.json"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "color-math" / "config.json"
        home = os.environ.get("HOME")
        if home:
            return Path(home) / ".config" / "color-math" / "config.json"
    return None


def load_config(path: Path | None = None) -> tuple[dict[str, str], ColorMathOptions]:
    """
    Load configuration from path, local '.colormath.json', or global user config.
    Returns (palette_dict, ColorMathOptions).
    """
    target = path
    if target is None:
        local_candidate = Path(".colormath.json")
        if local_candidate.exists():
            target = local_candidate
        else:
            global_candidate = get_global_config_path()
            if global_candidate and global_candidate.exists():
                target = global_candidate

    if target is None or not target.exists():
        return dict(DEFAULT_COLORS), ColorMathOptions()

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as err:
        raise ValueError(f"Failed to parse config file {target}: {err}") from err

    palette = dict(DEFAULT_COLORS)
    if isinstance(data, dict):
        if "theme" in data and isinstance(data["theme"], str):
            try:
                palette.update(get_theme(data["theme"]))
            except ValueError:
                pass
        if "colors" in data and isinstance(data["colors"], dict):
            for k, v in data["colors"].items():
                if isinstance(k, str) and isinstance(v, str):
                    palette[k] = v

    raw_options = data.get("options", {}) if isinstance(data, dict) else {}
    options = ColorMathOptions(
        enable_taxonomy=bool(raw_options.get("enable_taxonomy", False)),
        rainbow_delimiters=bool(raw_options.get("rainbow_delimiters", False)),
        variable_data_flow=bool(raw_options.get("variable_data_flow", False)),
        color_units=bool(raw_options.get("color_units", False)),
        color_differentials=bool(raw_options.get("color_differentials", False)),
        color_braket=bool(raw_options.get("color_braket", False)),
        color_dimensionless=bool(raw_options.get("color_dimensionless", False)),
    )
    return palette, options


def save_default_config(path: Path) -> Path:
    """Save the clean default configuration to path."""
    content = {
        "_comment": "Python Color Math configuration file",
        "theme": "default",
        "colors": dict(DEFAULT_COLORS),
        "options": asdict(ColorMathOptions()),
        "_role_descriptions": ROLE_DESCRIPTIONS,
    }
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return path


def reset_config_file(path: Path) -> Path:
    """Reset an existing configuration file at path back to factory defaults."""
    return save_default_config(path)
