# latex_helpers.py

import re


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")


def read_comment_end(text: str, start: int) -> int:
    """Return the index after one TeX comment, including its newline."""
    index = start + 1
    while index < len(text) and text[index] not in "\r\n":
        index += 1
    if text.startswith("\r\n", index):
        return index + 2
    return min(index + 1, len(text))


def read_verb_end(text: str, start: int) -> tuple[int, bool] | None:
    r"""Read an exact ``\verb``/``\verb*`` payload without inspecting it."""
    if not text.startswith(r"\verb", start):
        return None
    command_end = start + len(r"\verb")
    if command_end < len(text) and text[command_end].isalpha():
        return None
    if command_end < len(text) and text[command_end] == "*":
        command_end += 1
    if command_end >= len(text) or text[command_end].isspace():
        return len(text), False

    delimiter = text[command_end]
    closing = text.find(delimiter, command_end + 1)
    return (
        (len(text), False)
        if closing < 0
        else (closing + 1, True)
    )


def read_braced(text: str, start: int) -> tuple[str, int] | None:
    """
    Read a balanced {...} group starting at index 'start'.

    Returns:
        (captured_text, end_index)

    Example:
        "{abc}" -> ("{abc}", 5)
    """
    if start >= len(text) or text[start] != "{":
        return None

    depth = 0
    index = start

    while index < len(text):
        char = text[index]

        if char == "%":
            index = read_comment_end(text, index)
            continue

        if char == "\\":
            verb = read_verb_end(text, index)
            if verb is not None:
                index, closed = verb
                if not closed:
                    return None
                continue
            command = COMMAND_RE.match(text, index)
            index = command.end() if command is not None else index + 1
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1], index + 1

        index += 1

    return None


def read_script_argument(text: str, start: int) -> tuple[str, int] | None:
    """
    Read argument after _ or ^

    Handles:
        x^{abc}
        x^n
        x^\\alpha
    """

    if start >= len(text):
        return None

    # Braced argument
    if text[start] == "{":
        return read_braced(text, start)

    if text[start] in "$\r\n":
        return None

    # Latex command
    if text[start] == "\\":
        match = re.match(r"\\[A-Za-z]+|\\.", text[start:])
        if match:
            return match.group(0), start + len(match.group(0))

    # Single character
    return text[start], start + 1


def read_script(text: str, start: int) -> tuple[str, int, bool] | None:
    """
    Read full superscript/subscript.

    Example:
        "^2"
        "_{abc}"
        "^\\alpha"
    """

    marker = text[start]   # _ or ^

    argument_start = start + 1

    if argument_start < len(text) and text[argument_start] == "{":
        argument_data = read_braced(text, argument_start)

        if argument_data is None:
            return text[start:], len(text), False

        argument, end = argument_data
        return f"{marker}{argument}", end, True

    argument_data = read_script_argument(text, argument_start)

    if argument_data is None:
        return None

    argument, end = argument_data

    return f"{marker}{argument}", end, True


def read_color_wrapper(text: str, start: int) -> tuple[str, int] | None:
    """
    Read a scoped color wrapper and return its unbraced value and end index.

    Supports current ``\\textcolor{red}{x}`` output and legacy
    ``\\color{red}{x}`` output. Command names are matched exactly, so macros
    such as ``\\colorbox`` and ``\\colorful`` are left alone.
    """
    command = next(
        (
            candidate
            for candidate in (r"\textcolor", r"\color")
            if text.startswith(candidate, start)
            and (
                start + len(candidate) == len(text)
                or not text[start + len(candidate)].isalpha()
            )
        ),
        None,
    )
    if command is None:
        return None

    index = start + len(command)

    while index < len(text) and text[index].isspace():
        index += 1

    color_data = read_braced(text, index)
    if color_data is None:
        return None

    _, index = color_data

    while index < len(text) and text[index].isspace():
        index += 1

    value_data = read_braced(text, index)
    if value_data is None:
        return None

    value, end = value_data
    return value[1:-1], end


def read_color_command(text: str, start: int) -> tuple[str, int] | None:
    """
    Detect an existing scoped color command.

    Examples:
        \\textcolor{red}{x}
        \\color{red}{x}

    Returns:
        (full_command, end_index)
        or None
    """
    wrapper = read_color_wrapper(text, start)
    if wrapper is None:
        return None

    _, end = wrapper
    return text[start:end], end


def contains_color_wrapper(text: str) -> bool:
    """Find active wrappers, ignoring TeX comments and verbatim payloads."""
    if r"\textcolor" not in text and r"\color" not in text:
        return False
    index = 0
    while index < len(text):
        if text[index] == "%":
            index = read_comment_end(text, index)
            continue
        if text[index] == "\\":
            if read_color_wrapper(text, index) is not None:
                return True
            verb = read_verb_end(text, index)
            if verb is not None:
                index = verb[0]
                continue
            command = COMMAND_RE.match(text, index)
            index = command.end() if command is not None else index + 1
            continue
        index += 1
    return False


class _ParsedMacroArg:
    def __init__(self, raw: str, inner: str, end: int, braced: bool):
        self.raw = raw
        self.inner = inner
        self.end = end
        self.braced = braced


TWO_ARG_COMMANDS = frozenset({
    r"\frac",
    r"\dfrac",
    r"\tfrac",
    r"\cfrac",
    r"\binom",
    r"\dbinom",
    r"\tbinom",
    r"\overset",
    r"\underset",
    r"\stackrel",
})

OPAQUE_TEXT_COMMANDS = frozenset({
    r"\text",
    r"\mathrm",
    r"\textbf",
    r"\textit",
    r"\texttt",
    r"\textrm",
})


def _skip_ignorable_whitespace(text: str, start: int) -> int:
    index = start
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        if text[index] == "%":
            index = read_comment_end(text, index)
            continue
        break
    return index


def _read_single_macro_arg(text: str, start: int) -> _ParsedMacroArg | None:
    index = _skip_ignorable_whitespace(text, start)
    if index >= len(text):
        return None

    if text[index] == "{":
        braced = read_braced(text, index)
        if braced is not None:
            return _ParsedMacroArg(
                raw=braced[0],
                inner=braced[0][1:-1],
                end=braced[1],
                braced=True,
            )
        return None

    if text[index] == "\\":
        cmd = COMMAND_RE.match(text, index)
        if cmd is not None:
            cmd_str = cmd.group(0)
            return _ParsedMacroArg(
                raw=cmd_str,
                inner=cmd_str,
                end=index + len(cmd_str),
                braced=False,
            )

    return _ParsedMacroArg(
        raw=text[index],
        inner=text[index],
        end=index + 1,
        braced=False,
    )


def normalize_latex_braces(source: str) -> str:
    r"""Normalizes unbraced arguments in LaTeX expressions.
    e.g. \frac2L -> \frac{2}{L}, \sqrt V -> \sqrt{V},
    \frac VI -> \frac{V}{I}, E_n -> E_{n}, x^2 -> x^{2}.
    Guarantees that subsequent \textcolor wrapping never breaks TeX grammar.
    """
    result: list[str] = []
    index = 0

    while index < len(source):
        if source[index] == "%":
            end = read_comment_end(source, index)
            result.append(source[index:end])
            index = end
            continue

        if source[index] in "^_":
            marker = source[index]
            arg = _read_single_macro_arg(source, index + 1)
            if arg is not None:
                norm_inner = (
                    normalize_latex_braces(arg.inner)
                    if arg.braced
                    else normalize_latex_braces(arg.raw)
                )
                result.append(f"{marker}{{{norm_inner}}}")
                index = arg.end
                continue
            else:
                result.append(marker)
                index += 1
                continue

        if source[index] == "\\":
            verb = read_verb_end(source, index)
            if verb is not None:
                v_end = verb[0]
                result.append(source[index:v_end])
                index = v_end
                continue

            cmd_match = COMMAND_RE.match(source, index)
            if cmd_match is not None:
                cmd = cmd_match.group(0)
                cmd_end = index + len(cmd)

                if cmd in OPAQUE_TEXT_COMMANDS:
                    braced = read_braced(source, cmd_end)
                    if braced is not None:
                        result.append(f"{cmd}{braced[0]}")
                        index = braced[1]
                        continue

                if cmd in TWO_ARG_COMMANDS:
                    arg1 = _read_single_macro_arg(source, cmd_end)
                    if arg1 is not None:
                        arg2 = _read_single_macro_arg(source, arg1.end)
                        if arg2 is not None:
                            norm1 = (
                                normalize_latex_braces(arg1.inner)
                                if arg1.braced
                                else normalize_latex_braces(arg1.raw)
                            )
                            norm2 = (
                                normalize_latex_braces(arg2.inner)
                                if arg2.braced
                                else normalize_latex_braces(arg2.raw)
                            )
                            result.append(f"{cmd}{{{norm1}}}{{{norm2}}}")
                            index = arg2.end
                            continue

                elif cmd == r"\sqrt":
                    cur = _skip_ignorable_whitespace(source, cmd_end)
                    optional = ""
                    if cur < len(source) and source[cur] == "[":
                        opt_close = source.find("]", cur)
                        if opt_close != -1:
                            optional = source[cur : opt_close + 1]
                            cur = opt_close + 1
                    arg = _read_single_macro_arg(source, cur)
                    if arg is not None:
                        norm = (
                            normalize_latex_braces(arg.inner)
                            if arg.braced
                            else normalize_latex_braces(arg.raw)
                        )
                        result.append(f"{cmd}{optional}{{{norm}}}")
                        index = arg.end
                        continue

        result.append(source[index])
        index += 1

    return "".join(result)

