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
    "energy_operator": "#2ac3de",
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


from .unicode import (
    UNICODE_BIG_OPERATORS,
    UNICODE_INTEGRALS,
    UNICODE_RELATIONS,
    UNICODE_ARROWS,
    UNICODE_SETS,
    UNICODE_MULTIPLICATION,
    UNICODE_CONSTANTS,
    UNICODE_VECTORS,
    UNICODE_GREEK_LOWER_STANDARD,
    UNICODE_GREEK_LOWER_PLANE1,
    UNICODE_GREEK_UPPER_STANDARD,
    UNICODE_GREEK_UPPER_PLANE1,
)
from .custom_definitions import (
    CUSTOM_CONSTANTS,
    CUSTOM_FUNCTIONS,
    CUSTOM_OPERATORS,
    CUSTOM_PARAMETERS,
    CUSTOM_QUANTUM_OPERATORS,
    CUSTOM_RELATIONS,
    sanitize_definition,
)

CUSTOM_BARE_FUNCTIONS: set[str] = set()
CUSTOM_MACRO_FUNCTIONS: set[str] = set()
for _raw_fn in CUSTOM_FUNCTIONS:
    _macro, _bare = sanitize_definition(_raw_fn)
    if _bare:
        CUSTOM_BARE_FUNCTIONS.add(_bare)
    if _macro:
        CUSTOM_MACRO_FUNCTIONS.add(_macro)

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
    *UNICODE_BIG_OPERATORS.values(),
    *CUSTOM_OPERATORS,
}


INTEGRALS = {
    r"\int",
    r"\iint",
    r"\iiint",
    r"\oint",
    *UNICODE_INTEGRALS.values(),
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
    *UNICODE_RELATIONS.values(),
    *CUSTOM_RELATIONS,
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
    *UNICODE_ARROWS.values(),
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
    *UNICODE_SETS.values(),
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
    "×",
    "✕",
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
    *CUSTOM_MACRO_FUNCTIONS,
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
    | set(CUSTOM_QUANTUM_OPERATORS)
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
    *UNICODE_CONSTANTS.values(),
    *CUSTOM_CONSTANTS,
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
ALL_BARE_FUNCTIONS = FULL_BARE_FUNCTIONS | CUSTOM_BARE_FUNCTIONS
BARE_FUNCTIONS = ALL_BARE_FUNCTIONS


def get_bare_functions(options: ColorMathOptions | None = None) -> frozenset[str]:
    base = FULL_BARE_FUNCTIONS if (options is None or options.extended_functions) else STANDARD_BARE_FUNCTIONS
    return frozenset(base | CUSTOM_BARE_FUNCTIONS)


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
    *UNICODE_GREEK_LOWER_STANDARD.values(),
    *UNICODE_GREEK_LOWER_PLANE1.values(),
    *UNICODE_GREEK_UPPER_STANDARD.values(),
    *UNICODE_GREEK_UPPER_PLANE1.values(),
    "𝜓",
    "𝝍",
    *CUSTOM_PARAMETERS,
}

NON_SLASH_MATH_CONSTANTS = {c for c in MATH_CONSTANTS if not c.startswith("\\")}
NON_SLASH_MATH_PARAMETERS = {c for c in MATH_PARAMETERS if not c.startswith("\\")}


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
    *CUSTOM_MACRO_FUNCTIONS,
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
    color_alignment: bool = False
    color_single_constants: bool = False
    normalize_braces: bool = False
    extended_functions: bool = True
    color_quantum_operators: bool = False
    rainbow_bare_braces: bool = False
    highlight_unmatched_braces: bool = False
    field: str = "math"

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
            normalize_braces=False,
            extended_functions=True,
            rainbow_bare_braces=False,
            highlight_unmatched_braces=True,
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
            color_alignment=True,
            color_single_constants=True,
            normalize_braces=False,
            extended_functions=True,
            rainbow_bare_braces=True,
            highlight_unmatched_braces=True,
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


def ensure_global_config_exists() -> Path | None:
    """Ensure that the global configuration file and folder exist on disk.

    Creates the directory and saves the documented default configuration if it
    does not already exist. Returns the Path to the global config.
    """
    path = get_global_config_path()
    if path is None:
        return None
    if not path.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            save_default_config(path)
        except OSError:
            pass
    return path


def open_config_folder(path: Path | None = None) -> bool:
    """Open the configuration folder in the operating system's file manager."""
    target = path
    if target is None:
        local_candidate = Path(".colormath.json")
        if local_candidate.exists():
            target = local_candidate
        else:
            target = ensure_global_config_exists() or get_global_config_path()

    if target is None:
        return False

    folder = target.parent if target.suffix else target
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if not target.exists() and target.suffix == ".json":
            save_default_config(target)
    except OSError:
        pass

    try:
        if sys.platform == "win32":
            os.startfile(folder)
            return True
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", str(folder)], check=False)
            return True
        else:
            import subprocess
            subprocess.run(["xdg-open", str(folder)], check=False)
            return True
    except Exception:
        return False


DEFAULT_UNICODE_CONFIG: dict[str, object] = {
    "greek_style": "plane1",
    "convert_definite_integrals": False,
    "convert_bounded_operators": False,
    "convert_prose_to_unicode": False,
    "convert_prose_to_latex": False,
}


def get_bundled_default_config_path() -> Path:
    """Return path to bundled colormath.default.json."""
    return Path(__file__).parent / "colormath.default.json"


def get_bundled_default_config() -> dict[str, object]:
    """Load the factory defaults configuration object."""
    default_path = get_bundled_default_config_path()
    if default_path.exists():
        try:
            return json.loads(default_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "_comment": "Python Color Math factory default configuration",
        "theme": "default",
        "colors": dict(DEFAULT_COLORS),
        "options": asdict(ColorMathOptions()),
        "unicode": dict(DEFAULT_UNICODE_CONFIG),
        "_role_descriptions": ROLE_DESCRIPTIONS,
    }


def load_config(
    path: Path | None = None,
) -> tuple[dict[str, str], ColorMathOptions, dict[str, object]]:
    """
    Load configuration from path, local '.colormath.json', or global user config.
    Fault-tolerant: If the user file contains JSON syntax errors or invalid types,
    a warning is emitted and it safely falls back to factory defaults without crashing.
    Returns (palette_dict, ColorMathOptions, unicode_config_dict).
    """
    palette = dict(DEFAULT_COLORS)
    options = ColorMathOptions()
    unicode_config = dict(DEFAULT_UNICODE_CONFIG)

    target = path
    if target is None:
        local_candidate = Path(".colormath.json")
        if local_candidate.exists():
            target = local_candidate
        else:
            global_candidate = ensure_global_config_exists()
            if global_candidate and global_candidate.exists():
                target = global_candidate

    if target is None or not target.exists():
        return palette, options, unicode_config

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            sys.stderr.write(
                f"color-math warning: config file '{target}' must contain a JSON object. "
                "Safely falling back to default configuration.\n"
            )
            return palette, options, unicode_config
    except Exception as err:
        sys.stderr.write(
            f"color-math warning: failed to parse config file '{target}': {err}. "
            "Safely falling back to default configuration.\n"
        )
        return palette, options, unicode_config

    # 1. Apply theme
    if "theme" in data and isinstance(data["theme"], str):
        try:
            palette.update(get_theme(data["theme"]))
        except ValueError:
            pass

    # 2. Apply color overrides
    if "colors" in data and isinstance(data["colors"], dict):
        for k, v in data["colors"].items():
            if isinstance(k, str) and isinstance(v, str) and k in DEFAULT_COLORS:
                palette[k] = v

    # 3. Apply engine options
    if "options" in data and isinstance(data["options"], dict):
        raw_options = data["options"]
        options = ColorMathOptions(
            enable_taxonomy=bool(raw_options.get("enable_taxonomy", options.enable_taxonomy)),
            rainbow_delimiters=bool(raw_options.get("rainbow_delimiters", options.rainbow_delimiters)),
            variable_data_flow=bool(raw_options.get("variable_data_flow", options.variable_data_flow)),
            color_units=bool(raw_options.get("color_units", options.color_units)),
            color_differentials=bool(raw_options.get("color_differentials", options.color_differentials)),
            color_braket=bool(raw_options.get("color_braket", options.color_braket)),
            color_dimensionless=bool(raw_options.get("color_dimensionless", options.color_dimensionless)),
            color_alignment=bool(raw_options.get("color_alignment", options.color_alignment)),
            color_single_constants=bool(raw_options.get("color_single_constants", options.color_single_constants)),
            normalize_braces=bool(raw_options.get("normalize_braces", options.normalize_braces)),
            extended_functions=bool(raw_options.get("extended_functions", options.extended_functions)),
            color_quantum_operators=bool(raw_options.get("color_quantum_operators", options.color_quantum_operators)),
            rainbow_bare_braces=bool(raw_options.get("rainbow_bare_braces", options.rainbow_bare_braces)),
            highlight_unmatched_braces=bool(raw_options.get("highlight_unmatched_braces", options.highlight_unmatched_braces)),
            field=str(raw_options.get("field", options.field)),
        )

    # 4. Apply unicode options
    if "unicode" in data and isinstance(data["unicode"], dict):
        raw_unicode = data["unicode"]
        if "greek_style" in raw_unicode and raw_unicode["greek_style"] in ("plane1", "standard"):
            unicode_config["greek_style"] = raw_unicode["greek_style"]
        if "convert_definite_integrals" in raw_unicode:
            unicode_config["convert_definite_integrals"] = bool(raw_unicode["convert_definite_integrals"])
        if "convert_bounded_operators" in raw_unicode:
            unicode_config["convert_bounded_operators"] = bool(raw_unicode["convert_bounded_operators"])
        if "convert_prose_to_unicode" in raw_unicode:
            unicode_config["convert_prose_to_unicode"] = bool(raw_unicode["convert_prose_to_unicode"])
        if "convert_prose_to_latex" in raw_unicode:
            unicode_config["convert_prose_to_latex"] = bool(raw_unicode["convert_prose_to_latex"])

    return palette, options, unicode_config


def save_default_config(path: Path) -> Path:
    """Save the clean default configuration to path, and copy the reference default file."""
    content = get_bundled_default_config()
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    # Also save .colormath.default.json alongside .colormath.json if appropriate
    target_dir = path.parent
    default_ref_path = target_dir / ".colormath.default.json"
    try:
        default_ref_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    except OSError:
        pass

    return path


def reset_config_file(path: Path) -> Path:
    """Reset an existing configuration file at path back to factory defaults."""
    return save_default_config(path)
